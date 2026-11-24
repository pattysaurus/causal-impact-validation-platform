
from dataclasses import replace

import pandas as pd
import pytest
from pandas.api import types as pdt

from causal_engine.config import SimulationConfig
from causal_engine.simulation import REQUIRED_COLUMNS, generate_synthetic_panel


@pytest.fixture
def config() -> SimulationConfig:
    return SimulationConfig(
        treatment_effect=20.0,
        noise_std=0.0,
        n_treated_units=3,
        n_control_units=4,
        n_pre_periods=4,
        n_post_periods=5,
        random_seed=101,
        common_time_trend=1.5,
        unit_effect_std=3.0,
        pre_trend_difference=0.0,
    )


def test_panel_has_required_schema_and_column_types(config: SimulationConfig) -> None:
    panel = generate_synthetic_panel(config)

    assert set(REQUIRED_COLUMNS).issubset(panel.columns)
    assert pdt.is_datetime64_any_dtype(panel["date"])
    assert pdt.is_string_dtype(panel["unit_id"])
    assert pdt.is_float_dtype(panel["outcome"])
    assert pdt.is_bool_dtype(panel["treated"])
    assert pdt.is_bool_dtype(panel["post"])
    assert pdt.is_datetime64_any_dtype(panel["intervention_date"])


def test_panel_has_expected_row_count(config: SimulationConfig) -> None:
    panel = generate_synthetic_panel(config)

    expected_rows = (config.n_treated_units + config.n_control_units) * (
        config.n_pre_periods + config.n_post_periods
    )
    assert len(panel) == expected_rows


def test_every_unit_has_all_expected_dates(config: SimulationConfig) -> None:
    panel = generate_synthetic_panel(config)
    expected_dates = config.n_pre_periods + config.n_post_periods

    assert panel.groupby("unit_id")["date"].nunique().eq(expected_dates).all()
    assert panel.groupby("unit_id").size().eq(expected_dates).all()


def test_treated_units_have_no_effect_before_intervention(config: SimulationConfig) -> None:
    panel = generate_synthetic_panel(config)
    zero_effect_panel = generate_synthetic_panel(replace(config, treatment_effect=0.0))
    treated_pre_periods = panel.loc[panel["treated"] & ~panel["post"]]
    treated_pre_effect = (
        panel.loc[panel["treated"] & ~panel["post"], "outcome"].to_numpy()
        - zero_effect_panel.loc[
            zero_effect_panel["treated"] & ~zero_effect_panel["post"], "outcome"
        ].to_numpy()
    )

    assert treated_pre_periods["treatment_effect_applied"].eq(0.0).all()
    assert (treated_pre_effect == 0.0).all()
    assert (treated_pre_periods["date"] < treated_pre_periods["intervention_date"]).all()


def test_treated_units_receive_planted_effect_after_intervention(
    config: SimulationConfig,
) -> None:
    panel = generate_synthetic_panel(config)
    zero_effect_panel = generate_synthetic_panel(replace(config, treatment_effect=0.0))
    treated_post_periods = panel.loc[panel["treated"] & panel["post"]]
    treated_post_effect = (
        panel.loc[panel["treated"] & panel["post"], "outcome"].to_numpy()
        - zero_effect_panel.loc[
            zero_effect_panel["treated"] & zero_effect_panel["post"], "outcome"
        ].to_numpy()
    )

    assert treated_post_periods["treatment_effect_applied"].eq(
        config.treatment_effect
    ).all()
    assert (treated_post_effect == config.treatment_effect).all()
    assert (treated_post_periods["date"] >= treated_post_periods["intervention_date"]).all()


def test_control_units_never_receive_treatment_effect(config: SimulationConfig) -> None:
    panel = generate_synthetic_panel(config)
    zero_effect_panel = generate_synthetic_panel(replace(config, treatment_effect=0.0))
    control_periods = panel.loc[~panel["treated"]]
    control_effect = (
        panel.loc[~panel["treated"], "outcome"].to_numpy()
        - zero_effect_panel.loc[~zero_effect_panel["treated"], "outcome"].to_numpy()
    )

    assert control_periods["treatment_effect_applied"].eq(0.0).all()
    assert (control_effect == 0.0).all()


def test_same_configuration_produces_identical_data(config: SimulationConfig) -> None:
    first_panel = generate_synthetic_panel(config)
    second_panel = generate_synthetic_panel(config)

    pd.testing.assert_frame_equal(first_panel, second_panel)


def test_noiseless_treated_by_post_difference_equals_planted_effect(
    config: SimulationConfig,
) -> None:
    panel = generate_synthetic_panel(config)
    group_period_means = panel.groupby(["treated", "post"], observed=True)[
        "outcome"
    ].mean()

    treated_change = group_period_means[True, True] - group_period_means[True, False]
    control_change = group_period_means[False, True] - group_period_means[False, False]

    assert treated_change - control_change == pytest.approx(config.treatment_effect)


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "message"),
    [
        ("n_treated_units", 0, "n_treated_units must be a positive integer"),
        ("n_control_units", -1, "n_control_units must be a positive integer"),
        ("n_pre_periods", 0, "n_pre_periods must be a positive integer"),
        ("n_post_periods", False, "n_post_periods must be a positive integer"),
        ("noise_std", -0.1, "noise_std must be non-negative"),
        ("unit_effect_std", -0.1, "unit_effect_std must be non-negative"),
    ],
)
def test_invalid_configuration_has_helpful_error(
    field_name: str, invalid_value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SimulationConfig(**{field_name: invalid_value})


def test_fake_pre_treatment_effect_is_applied_only_before_intervention() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(
            fake_pre_treatment_effect=7.0,
            n_pre_periods=6,
            n_post_periods=3,
            random_seed=31,
        )
    )

    fake_effect_rows = panel.loc[panel["fake_pre_treatment_effect_applied"] > 0]
    assert (~fake_effect_rows["post"]).all()
    assert fake_effect_rows["treated"].all()


def test_missing_data_option_is_deterministic() -> None:
    config = SimulationConfig(missing_data_rate=0.20, random_seed=32)

    first_panel = generate_synthetic_panel(config)
    second_panel = generate_synthetic_panel(config)

    pd.testing.assert_frame_equal(first_panel, second_panel)
    assert first_panel["outcome"].isna().any()
