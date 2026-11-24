
"""Baseline Difference-in-Differences estimation using conventional OLS."""

from dataclasses import dataclass
import math
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pandas.api import types as pdt


REQUIRED_COLUMNS = {"outcome", "treated", "post", "unit_id", "date"}
MODEL_FORMULA = "outcome ~ treated + post + treated:post"
INTERACTION_COLUMN = "treated_post"
StandardErrorType = Literal["unit-clustered", "non-clustered"]


@dataclass(frozen=True)
class DidResult:
    """Summary of the baseline Difference-in-Differences model fit."""

    effect_estimate: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    standard_error: float
    n_observations: int
    n_treated_units: int
    n_control_units: int
    n_clusters: int
    n_pre_observations: int
    n_post_observations: int
    standard_error_type: StandardErrorType
    model_formula: str
    r_squared: float
    adjusted_r_squared: float
    residual_degrees_of_freedom: float


def estimate_difference_in_differences(
    data: pd.DataFrame,
    *,
    standard_error_type: StandardErrorType = "unit-clustered",
) -> DidResult:
    """Estimate the treatment-by-post interaction in a two-group DiD model.

    Unit-clustered standard errors are the default because observations from a
    unit may be correlated over time. Conventional OLS errors remain available
    for comparison but are labelled ``non-clustered``.
    """
    _validate_input(data)

    # Build a new design matrix so the caller's DataFrame is never changed.
    treated = data["treated"].astype(int)
    post = data["post"].astype(int)
    design_matrix = pd.DataFrame(
        {
            "intercept": 1.0,
            "treated": treated,
            "post": post,
            INTERACTION_COLUMN: treated * post,
        },
        index=data.index,
    )

    if standard_error_type == "unit-clustered":
        model = sm.OLS(data["outcome"].astype(float), design_matrix).fit(
            cov_type="cluster",
            cov_kwds={"groups": data["unit_id"]},
        )
    elif standard_error_type == "non-clustered":
        model = sm.OLS(data["outcome"].astype(float), design_matrix).fit()
    else:
        raise ValueError(
            "standard_error_type must be 'unit-clustered' or 'non-clustered'."
        )
    if standard_error_type == "unit-clustered":
        standard_error, p_value, lower, upper = _clustered_parameter_inference(
            model, INTERACTION_COLUMN
        )
    else:
        confidence_interval = model.conf_int(alpha=0.05).loc[INTERACTION_COLUMN]
        standard_error = float(model.bse[INTERACTION_COLUMN])
        p_value = float(model.pvalues[INTERACTION_COLUMN])
        lower = float(confidence_interval.iloc[0])
        upper = float(confidence_interval.iloc[1])

    # This coefficient is the treated group's post-period change beyond the
    # control group's post-period change in the specified baseline model.
    return DidResult(
        effect_estimate=float(model.params[INTERACTION_COLUMN]),
        confidence_interval_lower=lower,
        confidence_interval_upper=upper,
        p_value=p_value,
        standard_error=standard_error,
        n_observations=int(model.nobs),
        n_treated_units=int(data.loc[treated.eq(1), "unit_id"].nunique()),
        n_control_units=int(data.loc[treated.eq(0), "unit_id"].nunique()),
        n_clusters=int(data["unit_id"].nunique()),
        n_pre_observations=int(post.eq(0).sum()),
        n_post_observations=int(post.eq(1).sum()),
        standard_error_type=standard_error_type,
        model_formula=MODEL_FORMULA,
        r_squared=float(model.rsquared),
        adjusted_r_squared=float(model.rsquared_adj),
        residual_degrees_of_freedom=float(model.df_resid),
    )


def _validate_input(data: pd.DataFrame) -> None:
    """Validate that a panel can support the narrow baseline DiD model."""
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame.")

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {names}.")

    if data.empty:
        raise ValueError("data must contain at least one observation.")

    for column in ("treated", "post"):
        values = data[column]
        if values.isna().any() or not values.isin([0, 1, False, True]).all():
            raise ValueError(f"{column} must contain only binary 0/1 or boolean values.")

    if not pdt.is_numeric_dtype(data["outcome"]) or pdt.is_bool_dtype(data["outcome"]):
        raise ValueError("outcome must be numeric.")
    if data["outcome"].isna().any():
        raise ValueError("outcome must not contain missing values.")
    if not np.isfinite(data["outcome"].astype(float)).all():
        raise ValueError("outcome must contain only finite values.")

    if data["unit_id"].isna().any():
        raise ValueError("unit_id must not contain missing values.")
    if data["date"].isna().any():
        raise ValueError("date must not contain missing values.")

    treated = data["treated"].astype(bool)
    post = data["post"].astype(bool)
    if not treated.any() or treated.all():
        raise ValueError("data must contain both treated and control observations.")
    if not post.any() or post.all():
        raise ValueError("data must contain both pre and post observations.")

    if data.loc[treated, "unit_id"].nunique() < 1:
        raise ValueError("data must contain at least one treated unit.")
    if data.loc[~treated, "unit_id"].nunique() < 1:
        raise ValueError("data must contain at least one control unit.")


def _clustered_parameter_inference(model, parameter: str) -> tuple[float, float, float, float]:
    """Return stable normal-approximation inference for a clustered parameter."""
    estimate = float(model.params[parameter])
    covariance = model.cov_params()
    variance = float(covariance.loc[parameter, parameter])
    covariance_scale = float(np.abs(np.diag(covariance)).max())
    numerical_tolerance = np.finfo(float).eps * max(1.0, covariance_scale) * 100
    if variance < 0:
        if abs(variance) <= numerical_tolerance:
            variance = 0.0
        else:
            raise ValueError("Clustered covariance produced a negative parameter variance.")

    standard_error = math.sqrt(variance)
    if standard_error == 0:
        p_value = 1.0 if estimate == 0 else 0.0
    else:
        z_statistic = abs(estimate / standard_error)
        p_value = math.erfc(z_statistic / math.sqrt(2.0))
    critical_value = 1.959963984540054
    return (
        standard_error,
        p_value,
        estimate - critical_value * standard_error,
        estimate + critical_value * standard_error,
    )
