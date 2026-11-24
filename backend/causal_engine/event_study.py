
"""Event-study estimates around a single shared intervention date."""

from dataclasses import dataclass

import pandas as pd
import statsmodels.api as sm

from causal_engine.did import _clustered_parameter_inference, _validate_input


REFERENCE_PERIOD = -1


@dataclass(frozen=True)
class EventStudyResult:
    """Chart-ready dynamic treatment effects relative to the final pre-period."""

    effects: pd.DataFrame
    x_values: tuple[int, ...]
    estimates: tuple[float, ...]
    confidence_interval_lower: tuple[float, ...]
    confidence_interval_upper: tuple[float, ...]
    labels: tuple[str, ...]
    reference_period: int
    zero_reference_line: float
    n_clusters: int
    standard_error_type: str
    model_formula: str


def estimate_event_study(data: pd.DataFrame) -> EventStudyResult:
    """Estimate period-specific treated-group deviations using clustered OLS."""
    _validate_input(data)
    if "intervention_date" not in data.columns:
        raise ValueError("Missing required columns: intervention_date.")
    if data["intervention_date"].isna().any():
        raise ValueError("intervention_date must not contain missing values.")

    dates = pd.to_datetime(data["date"], errors="raise")
    intervention_dates = pd.to_datetime(data["intervention_date"], errors="raise")
    if intervention_dates.nunique() != 1:
        raise ValueError("event study requires one shared intervention_date.")

    unique_dates = pd.Index(sorted(dates.unique()))
    intervention_date = intervention_dates.iloc[0]
    if intervention_date not in unique_dates:
        raise ValueError("intervention_date must appear in the date column.")

    intervention_position = unique_dates.get_loc(intervention_date)
    relative_time = dates.map(
        {date: position - intervention_position for position, date in enumerate(unique_dates)}
    ).astype(int)
    if REFERENCE_PERIOD not in set(relative_time):
        raise ValueError("event study requires a period immediately before intervention.")

    treated = data["treated"].astype(int)
    design_matrix = pd.DataFrame({"intercept": 1.0, "treated": treated}, index=data.index)
    relative_periods = sorted(relative_time.unique())

    for period in relative_periods:
        if period == REFERENCE_PERIOD:
            continue
        time_column = _period_column("time", period)
        interaction_column = _period_column("treated_time", period)
        period_indicator = (relative_time == period).astype(int)
        # Common time indicators absorb shocks shared by treated and control units.
        design_matrix[time_column] = period_indicator
        # Each interaction is the treated-group deviation for that relative period.
        design_matrix[interaction_column] = treated * period_indicator

    model = sm.OLS(data["outcome"].astype(float), design_matrix).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["unit_id"]},
    )

    effect_rows: list[dict[str, object]] = []
    for period in relative_periods:
        period_type = (
            "reference"
            if period == REFERENCE_PERIOD
            else "pre"
            if period < REFERENCE_PERIOD
            else "post"
        )
        if period == REFERENCE_PERIOD:
            estimate = lower = upper = 0.0
        else:
            interaction_column = _period_column("treated_time", period)
            estimate = float(model.params[interaction_column])
            _, _, lower, upper = _clustered_parameter_inference(model, interaction_column)
        effect_rows.append(
            {
                "relative_time": period,
                "estimate": estimate,
                "confidence_interval_lower": lower,
                "confidence_interval_upper": upper,
                "period_type": period_type,
                "is_pre_period": period < REFERENCE_PERIOD,
                "is_reference_period": period == REFERENCE_PERIOD,
                "label": _period_label(period),
            }
        )

    effects = pd.DataFrame(effect_rows)
    return EventStudyResult(
        effects=effects,
        x_values=tuple(effects["relative_time"]),
        estimates=tuple(effects["estimate"]),
        confidence_interval_lower=tuple(effects["confidence_interval_lower"]),
        confidence_interval_upper=tuple(effects["confidence_interval_upper"]),
        labels=tuple(effects["label"]),
        reference_period=REFERENCE_PERIOD,
        zero_reference_line=0.0,
        n_clusters=int(data["unit_id"].nunique()),
        standard_error_type="unit-clustered",
        model_formula="outcome ~ treated + relative_time + treated:relative_time",
    )


def _period_column(prefix: str, period: int) -> str:
    suffix = f"m{abs(period)}" if period < 0 else f"p{period}"
    return f"{prefix}_{suffix}"


def _period_label(period: int) -> str:
    if period == REFERENCE_PERIOD:
        return "Reference (t-1)"
    return f"t{period:+d}"
