
import numpy as np
import pandas as pd
import pytest

from causal_engine.config import SimulationConfig
from causal_engine.did import estimate_difference_in_differences
from causal_engine.simulation import generate_synthetic_panel


RECOVERY_RUNS = 200
MINIMUM_COVERAGE = 0.90
# One unit is 5% of the known 20-unit planted effect in this fixed experiment.
MEAN_ESTIMATE_TOLERANCE = 1.0


def _panel(**overrides: object) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "treatment_effect": 20.0,
        "noise_std": 0.0,
        "n_treated_units": 4,
        "n_control_units": 5,
        "n_pre_periods": 6,
        "n_post_periods": 6,
        "random_seed": 91,
        "common_time_trend": 1.5,
        "unit_effect_std": 4.0,
        "pre_trend_difference": 0.0,
    }
    defaults.update(overrides)
    return generate_synthetic_panel(SimulationConfig(**defaults))


def test_clean_data_recovers_exact_planted_treatment_effect() -> None:
    treatment_effect = 20.0

    result = estimate_difference_in_differences(_panel(treatment_effect=treatment_effect))

    assert result.effect_estimate == pytest.approx(treatment_effect)
    assert np.isfinite(result.standard_error)
    assert np.isfinite(result.confidence_interval_lower)
    assert np.isfinite(result.confidence_interval_upper)


def test_effect_is_zero_when_planted_treatment_effect_is_zero() -> None:
    result = estimate_difference_in_differences(_panel(treatment_effect=0.0))

    assert result.effect_estimate == pytest.approx(0.0, abs=1e-12)


def test_confidence_interval_contains_planted_effect_with_fixed_moderate_noise() -> None:
    treatment_effect = 20.0
    panel = _panel(
        treatment_effect=treatment_effect,
        noise_std=6.0,
        n_treated_units=25,
        n_control_units=25,
        n_pre_periods=12,
        n_post_periods=12,
        random_seed=202,
    )

    result = estimate_difference_in_differences(panel)

    assert result.confidence_interval_lower <= treatment_effect <= result.confidence_interval_upper


def test_result_metadata_reports_panel_counts() -> None:
    panel = _panel(n_treated_units=3, n_control_units=4, n_pre_periods=2, n_post_periods=5)

    result = estimate_difference_in_differences(panel)

    assert result.n_observations == len(panel)
    assert result.n_treated_units == 3
    assert result.n_control_units == 4
    assert result.n_clusters == 7
    assert result.n_pre_observations == (3 + 4) * 2
    assert result.n_post_observations == (3 + 4) * 5
    assert result.standard_error_type == "unit-clustered"
    assert result.model_formula == "outcome ~ treated + post + treated:post"


def test_non_clustered_standard_errors_remain_available() -> None:
    result = estimate_difference_in_differences(
        _panel(), standard_error_type="non-clustered"
    )

    assert result.standard_error_type == "non-clustered"


def test_clustered_confidence_intervals_recover_known_effect_over_repeated_samples() -> None:
    true_effect = 20.0
    estimates: list[float] = []
    intervals_covering_truth = 0

    for random_seed in range(RECOVERY_RUNS):
        panel = _panel(
            treatment_effect=true_effect,
            noise_std=5.0,
            n_treated_units=20,
            n_control_units=20,
            n_pre_periods=12,
            n_post_periods=12,
            random_seed=random_seed,
        )
        result = estimate_difference_in_differences(panel)
        estimates.append(result.effect_estimate)
        intervals_covering_truth += int(
            result.confidence_interval_lower <= true_effect <= result.confidence_interval_upper
        )

    coverage = intervals_covering_truth / RECOVERY_RUNS
    mean_estimate = float(np.mean(estimates))
    print(f"Observed clustered-CI coverage: {coverage:.3f}")

    assert coverage >= MINIMUM_COVERAGE
    assert mean_estimate == pytest.approx(true_effect, abs=MEAN_ESTIMATE_TOLERANCE)


def test_estimation_does_not_mutate_input_data() -> None:
    panel = _panel()
    original_panel = panel.copy(deep=True)

    estimate_difference_in_differences(panel)

    pd.testing.assert_frame_equal(panel, original_panel)


def test_missing_required_columns_raise_helpful_error() -> None:
    panel = _panel().drop(columns="date")

    with pytest.raises(ValueError, match="Missing required columns: date"):
        estimate_difference_in_differences(panel)


@pytest.mark.parametrize("column", ["treated", "post"])
def test_non_binary_treatment_indicators_raise_helpful_error(column: str) -> None:
    panel = _panel()
    panel[column] = panel[column].astype(int)
    panel.loc[panel.index[0], column] = 2

    with pytest.raises(ValueError, match=f"{column} must contain only binary"):
        estimate_difference_in_differences(panel)


def test_missing_outcome_values_raise_helpful_error() -> None:
    panel = _panel()
    panel.loc[panel.index[0], "outcome"] = np.nan

    with pytest.raises(ValueError, match="outcome must not contain missing values"):
        estimate_difference_in_differences(panel)


@pytest.mark.parametrize("treated_value", [True, False])
def test_only_one_treatment_group_raises_helpful_error(treated_value: bool) -> None:
    panel = _panel()
    panel["treated"] = treated_value

    with pytest.raises(ValueError, match="both treated and control observations"):
        estimate_difference_in_differences(panel)


@pytest.mark.parametrize("post_value", [True, False])
def test_only_one_time_period_group_raises_helpful_error(post_value: bool) -> None:
    panel = _panel()
    panel["post"] = post_value

    with pytest.raises(ValueError, match="both pre and post observations"):
        estimate_difference_in_differences(panel)
