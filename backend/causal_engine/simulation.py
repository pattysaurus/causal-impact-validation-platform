
"""Synthetic panel generation with an explicit, known treatment effect."""

import numpy as np
import pandas as pd

from causal_engine.config import SimulationConfig


REQUIRED_COLUMNS = (
    "date",
    "unit_id",
    "outcome",
    "treated",
    "post",
    "intervention_date",
)


def generate_synthetic_panel(config: SimulationConfig) -> pd.DataFrame:
    """Return a balanced panel whose treatment effect is known by construction.

    ``treatment_effect_applied`` is included solely for transparent debugging of
    the data-generating process; it is not an estimated effect.
    """
    rng = np.random.default_rng(config.random_seed)
    missingness_rng = np.random.default_rng(config.random_seed + 1)
    total_periods = config.n_pre_periods + config.n_post_periods
    dates = pd.date_range("2020-01-01", periods=total_periods, freq="MS")
    intervention_date = dates[config.n_pre_periods]
    records: list[dict[str, object]] = []

    unit_definitions = [
        (f"treated_{index:03d}", True)
        for index in range(config.n_treated_units)
    ] + [
        (f"control_{index:03d}", False)
        for index in range(config.n_control_units)
    ]

    for unit_id, is_treated in unit_definitions:
        # Each unit gets a fixed baseline difference across all time periods.
        unit_baseline = rng.normal(0.0, config.unit_effect_std)

        for time_index, date in enumerate(dates):
            is_post = time_index >= config.n_pre_periods
            common_trend = config.common_time_trend * time_index

            # A nonzero value creates a treated-only slope difference before treatment.
            treated_pretrend = (
                config.pre_trend_difference
                * min(time_index, config.n_pre_periods - 1)
                if is_treated
                else 0.0
            )
            treatment_effect_applied = (
                config.treatment_effect if is_treated and is_post else 0.0
            )
            # An early, treated-only shift deliberately violates clean timing.
            fake_pre_effect_applied = (
                config.fake_pre_treatment_effect
                if is_treated
                and not is_post
                and time_index >= config.n_pre_periods // 2
                else 0.0
            )
            noise = rng.normal(0.0, config.noise_std)
            outcome = (
                unit_baseline
                + common_trend
                + treated_pretrend
                + fake_pre_effect_applied
                + treatment_effect_applied
                + noise
            )
            if (
                config.missing_data_rate > 0
                and missingness_rng.random() < config.missing_data_rate
            ):
                outcome = np.nan

            records.append(
                {
                    "date": date,
                    "unit_id": unit_id,
                    "outcome": outcome,
                    "treated": is_treated,
                    "post": is_post,
                    "intervention_date": intervention_date,
                    "treatment_effect_applied": treatment_effect_applied,
                    "fake_pre_treatment_effect_applied": fake_pre_effect_applied,
                }
            )

    panel = pd.DataFrame.from_records(records)
    panel["unit_id"] = panel["unit_id"].astype("string")
    panel["outcome"] = panel["outcome"].astype(float)
    panel["treated"] = panel["treated"].astype(bool)
    panel["post"] = panel["post"].astype(bool)
    panel["treatment_effect_applied"] = panel["treatment_effect_applied"].astype(float)
    return panel
