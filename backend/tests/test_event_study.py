
import pandas as pd
import pytest

from causal_engine.config import SimulationConfig
from causal_engine.event_study import estimate_event_study
from causal_engine.simulation import generate_synthetic_panel


def _panel(**overrides: object) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "treatment_effect": 15.0,
        "noise_std": 0.0,
        "n_treated_units": 8,
        "n_control_units": 8,
        "n_pre_periods": 5,
        "n_post_periods": 4,
        "random_seed": 71,
        "common_time_trend": 1.0,
        "unit_effect_std": 3.0,
        "pre_trend_difference": 0.0,
    }
    defaults.update(overrides)
    return generate_synthetic_panel(SimulationConfig(**defaults))


def test_event_study_returns_chart_ready_relative_time_effects() -> None:
    result = estimate_event_study(_panel())
    effects = result.effects

    assert list(effects.columns) == [
        "relative_time",
        "estimate",
        "confidence_interval_lower",
        "confidence_interval_upper",
        "period_type",
        "is_pre_period",
        "is_reference_period",
        "label",
    ]
    assert result.x_values == (-5, -4, -3, -2, -1, 0, 1, 2, 3)
    assert result.reference_period == -1
    assert result.zero_reference_line == 0.0
    assert result.standard_error_type == "unit-clustered"
    assert effects["confidence_interval_lower"].notna().all()
    assert effects["confidence_interval_upper"].notna().all()


def test_clean_event_study_recovers_zero_pre_effects_and_planted_post_effect() -> None:
    treatment_effect = 15.0
    result = estimate_event_study(_panel(treatment_effect=treatment_effect))
    effects = result.effects

    assert effects.loc[effects["is_pre_period"], "estimate"].to_list() == pytest.approx(
        [0.0, 0.0, 0.0, 0.0]
    )
    assert effects.loc[effects["is_reference_period"], "estimate"].to_list() == [0.0]
    assert effects.loc[effects["period_type"] == "post", "estimate"].to_list() == pytest.approx(
        [treatment_effect] * 4
    )


def test_event_study_does_not_mutate_input_data() -> None:
    panel = _panel(noise_std=2.0)
    original_panel = panel.copy(deep=True)

    estimate_event_study(panel)

    pd.testing.assert_frame_equal(panel, original_panel)


def test_event_study_requires_shared_intervention_date() -> None:
    panel = _panel()
    panel.loc[panel.index[0], "intervention_date"] = panel.loc[0, "date"]

    with pytest.raises(ValueError, match="one shared intervention_date"):
        estimate_event_study(panel)
