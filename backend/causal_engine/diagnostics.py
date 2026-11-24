
"""Evidence checks for the baseline single-intervention DiD design."""

from dataclasses import dataclass
from typing import Literal, Mapping

import numpy as np
import pandas as pd
import statsmodels.api as sm

from causal_engine.config import DEFAULT_DIAGNOSTIC_THRESHOLDS, DiagnosticThresholds
from causal_engine.did import estimate_difference_in_differences


Severity = Literal["info", "warning", "serious"]
_SEVERITY_ORDER = {"info": 0, "warning": 1, "serious": 2}
_REQUIRED_COLUMNS = {"outcome", "treated", "post", "unit_id", "date"}


@dataclass(frozen=True)
class DiagnosticResult:
    """One diagnostic finding, its severity, and inspectable supporting metrics."""

    name: str
    severity: Severity
    explanation: str
    metrics: Mapping[str, float | int | bool]


@dataclass(frozen=True)
class DiagnosticReport:
    """All baseline evidence checks for a candidate DiD panel."""

    results: tuple[DiagnosticResult, ...]

    @property
    def overall_severity(self) -> Severity:
        return max(self.results, key=lambda result: _SEVERITY_ORDER[result.severity]).severity

    def by_name(self, name: str) -> DiagnosticResult:
        return next(result for result in self.results if result.name == name)


def run_diagnostics(
    data: pd.DataFrame,
    *,
    thresholds: DiagnosticThresholds = DEFAULT_DIAGNOSTIC_THRESHOLDS,
) -> DiagnosticReport:
    """Run pre-trend, placebo, adequacy, control, cluster, and precision checks."""
    _validate_diagnostic_input(data)
    complete_data = data.dropna(subset=["outcome"]).copy()

    results = [
        _pretrend_check(complete_data, thresholds),
        _placebo_in_time_check(complete_data, thresholds),
        _data_adequacy_check(data, complete_data, thresholds),
        _control_quality_check(complete_data, thresholds),
        _small_cluster_check(complete_data, thresholds),
        _precision_check(complete_data, thresholds),
    ]
    return DiagnosticReport(results=tuple(results))


def _validate_diagnostic_input(data: pd.DataFrame) -> None:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame.")
    missing_columns = _REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}.")
    for column in ("treated", "post"):
        if data[column].isna().any() or not data[column].isin([0, 1, False, True]).all():
            raise ValueError(f"{column} must contain only binary 0/1 or boolean values.")


def _pretrend_check(
    data: pd.DataFrame, thresholds: DiagnosticThresholds
) -> DiagnosticResult:
    pre_data = data.loc[~data["post"].astype(bool)].copy()
    n_periods = pre_data["date"].nunique()
    if n_periods < thresholds.minimum_pre_periods:
        return DiagnosticResult(
            "pre_trend",
            "serious",
            "There are too few pre-periods to assess trend alignment; this raises concern and cannot establish parallel trends.",
            {"n_pre_periods": int(n_periods)},
        )

    model = _fit_time_interaction_model(pre_data)
    coefficient = float(model.params["treated_time"])
    p_value = float(model.pvalues["treated_time"])
    if p_value < thresholds.significance_level:
        explanation = (
            "The treated and control pre-period slopes differ in this test, which raises concern about parallel trends and cannot establish causality."
        )
        severity: Severity = "serious"
    else:
        explanation = (
            "Pre-period slopes are statistically consistent with alignment in this test; a non-significant pre-trend test does not prove parallel trends or establish causality."
        )
        severity = "info"
    return DiagnosticResult(
        "pre_trend",
        severity,
        explanation,
        {"slope_difference": coefficient, "p_value": p_value, "n_pre_periods": int(n_periods)},
    )


def _placebo_in_time_check(
    data: pd.DataFrame, thresholds: DiagnosticThresholds
) -> DiagnosticResult:
    pre_data = data.loc[~data["post"].astype(bool)].copy()
    dates = sorted(pre_data["date"].unique())
    if len(dates) < thresholds.minimum_pre_periods:
        return DiagnosticResult(
            "placebo_in_time",
            "serious",
            "There are too few pre-periods for an in-time placebo check; this is insufficient evidence for stable untreated behavior.",
            {"n_pre_periods": len(dates)},
        )

    cutoff = dates[len(dates) // 2]
    pre_data["post"] = pre_data["date"] >= cutoff
    model = _fit_binary_interaction_model(pre_data)
    p_value = float(model.pvalues["treated_post"])
    coefficient = float(model.params["treated_post"])
    if p_value < thresholds.significance_level:
        explanation = (
            "A placebo intervention inside the pre-period shows a treated-group deviation, which raises concern and cannot establish causality."
        )
        severity: Severity = "serious"
    else:
        explanation = (
            "The placebo-in-time estimate is consistent with no treated-group deviation; this check cannot establish causality."
        )
        severity = "info"
    return DiagnosticResult(
        "placebo_in_time",
        severity,
        explanation,
        {"placebo_effect": coefficient, "p_value": p_value, "placebo_cutoff_index": len(dates) // 2},
    )


def _data_adequacy_check(
    original_data: pd.DataFrame,
    complete_data: pd.DataFrame,
    thresholds: DiagnosticThresholds,
) -> DiagnosticResult:
    treated = original_data["treated"].astype(bool)
    post = original_data["post"].astype(bool)
    n_treated_units = int(original_data.loc[treated, "unit_id"].nunique())
    n_control_units = int(original_data.loc[~treated, "unit_id"].nunique())
    n_units = int(original_data["unit_id"].nunique())
    n_dates = int(original_data["date"].nunique())
    expected_cells = n_units * n_dates
    missing_rows = max(0, expected_cells - len(original_data))
    missing_outcomes = int(original_data["outcome"].isna().sum())
    missing_fraction = (missing_rows + missing_outcomes) / expected_cells if expected_cells else 1.0
    n_pre_observations = int((~complete_data["post"].astype(bool)).sum())
    n_post_observations = int(complete_data["post"].astype(bool).sum())
    effective_clusters = int(complete_data["unit_id"].nunique())

    serious_reasons = [
        n_treated_units < thresholds.minimum_treated_units,
        n_control_units < thresholds.minimum_control_units,
        n_pre_observations == 0,
        n_post_observations == 0,
        missing_fraction > thresholds.maximum_missing_fraction,
        effective_clusters < thresholds.minimum_effective_clusters,
    ]
    if any(serious_reasons):
        severity: Severity = "serious"
        explanation = (
            "Panel size or completeness raises concern: the available data are insufficient for a reliable baseline comparison and cannot establish causality."
        )
    else:
        severity = "info"
        explanation = (
            "Panel counts and completeness are consistent with the configured minimum adequacy thresholds; this cannot establish causality."
        )
    return DiagnosticResult(
        "data_adequacy",
        severity,
        explanation,
        {
            "n_treated_units": n_treated_units,
            "n_control_units": n_control_units,
            "n_pre_observations": n_pre_observations,
            "n_post_observations": n_post_observations,
            "missing_fraction": missing_fraction,
            "effective_clusters": effective_clusters,
        },
    )


def _control_quality_check(
    data: pd.DataFrame, thresholds: DiagnosticThresholds
) -> DiagnosticResult:
    pre_data = data.loc[~data["post"].astype(bool)]
    means = pre_data.groupby(["date", "treated"], observed=True)["outcome"].mean().unstack()
    if means.shape[0] < thresholds.minimum_pre_periods or set(means.columns) != {False, True}:
        return DiagnosticResult(
            "control_quality",
            "serious",
            "Pre-period control comparisons are insufficient, which raises concern about control quality and cannot establish causality.",
            {"n_aligned_pre_periods": int(means.shape[0])},
        )

    control_values = means[False].to_numpy()
    treated_values = means[True].to_numpy()
    if np.std(control_values) == 0 and np.std(treated_values) == 0:
        correlation = 1.0 if np.allclose(control_values, treated_values) else 0.0
    else:
        correlation = float(np.corrcoef(control_values, treated_values)[0, 1])
    time = np.arange(len(means), dtype=float)
    slope_difference = float(
        np.polyfit(time, treated_values, 1)[0] - np.polyfit(time, control_values, 1)[0]
    )
    if (
        not np.isfinite(correlation)
        or correlation < thresholds.minimum_pretrend_correlation
        or abs(slope_difference) > thresholds.maximum_pretrend_slope_difference
    ):
        severity: Severity = "serious"
        explanation = (
            "Pre-period control and treated trajectories are poorly aligned, which raises concern and cannot establish causality."
        )
    else:
        severity = "info"
        explanation = (
            "Pre-period control trajectory alignment is consistent with the configured thresholds; it cannot establish causality."
        )
    return DiagnosticResult(
        "control_quality",
        severity,
        explanation,
        {"pretrend_correlation": correlation, "slope_difference": slope_difference},
    )


def _small_cluster_check(
    data: pd.DataFrame, thresholds: DiagnosticThresholds
) -> DiagnosticResult:
    n_clusters = int(data["unit_id"].nunique())
    if n_clusters < thresholds.minimum_effective_clusters:
        severity: Severity = "serious"
        explanation = (
            "There are too few effective unit clusters for reliable cluster-robust inference; this raises concern and cannot establish causality."
        )
    elif n_clusters < thresholds.small_cluster_warning_threshold:
        severity = "warning"
        explanation = (
            "The cluster count is small, so conventional cluster-robust standard errors may be unreliable; this cannot establish causality."
        )
    else:
        severity = "info"
        explanation = (
            "The number of unit clusters is above the project's small-cluster warning threshold; this cannot establish causality."
        )
    return DiagnosticResult(
        "small_cluster",
        severity,
        explanation,
        {"n_clusters": n_clusters},
    )


def _precision_check(
    data: pd.DataFrame, thresholds: DiagnosticThresholds
) -> DiagnosticResult:
    try:
        result = estimate_difference_in_differences(data)
    except ValueError as error:
        return DiagnosticResult(
            "precision_power",
            "serious",
            f"Precision cannot be estimated for this panel ({error}); this is insufficient evidence and cannot establish causality.",
            {},
        )

    half_width = (result.confidence_interval_upper - result.confidence_interval_lower) / 2
    minimum_detectable_effect = thresholds.normal_critical_value * result.standard_error
    interval_contains_zero = (
        result.confidence_interval_lower <= 0 <= result.confidence_interval_upper
    )
    if (
        not np.isfinite(half_width)
        or half_width > thresholds.maximum_ci_half_width
        or interval_contains_zero
    ):
        severity: Severity = "serious"
        explanation = (
            "The estimate is too imprecise to distinguish the intervention effect from zero at the configured precision threshold; this is insufficient evidence and cannot establish causality."
        )
    else:
        severity = "info"
        explanation = (
            "The confidence interval is precise enough for the configured reference threshold; this is consistent with detectable evidence but cannot establish causality."
        )
    return DiagnosticResult(
        "precision_power",
        severity,
        explanation,
        {
            "ci_half_width": float(half_width),
            "minimum_detectable_effect": float(minimum_detectable_effect),
            "interval_contains_zero": bool(interval_contains_zero),
        },
    )


def _fit_time_interaction_model(data: pd.DataFrame):
    dates = pd.Index(sorted(data["date"].unique()))
    time_index = data["date"].map({date: index for index, date in enumerate(dates)}).astype(float)
    treated = data["treated"].astype(int)
    design_matrix = pd.DataFrame(
        {
            "intercept": 1.0,
            "treated": treated,
            "time": time_index,
            "treated_time": treated * time_index,
        },
        index=data.index,
    )
    return sm.OLS(data["outcome"].astype(float), design_matrix).fit(
        cov_type="cluster", cov_kwds={"groups": data["unit_id"]}
    )


def _fit_binary_interaction_model(data: pd.DataFrame):
    treated = data["treated"].astype(int)
    post = data["post"].astype(int)
    design_matrix = pd.DataFrame(
        {
            "intercept": 1.0,
            "treated": treated,
            "post": post,
            "treated_post": treated * post,
        },
        index=data.index,
    )
    return sm.OLS(data["outcome"].astype(float), design_matrix).fit(
        cov_type="cluster", cov_kwds={"groups": data["unit_id"]}
    )
