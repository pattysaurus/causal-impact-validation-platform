
from causal_engine.config import SimulationConfig
from causal_engine.diagnostics import run_diagnostics
from causal_engine.simulation import generate_synthetic_panel


def test_clean_default_panel_has_all_expected_diagnostic_results() -> None:
    panel = generate_synthetic_panel(SimulationConfig(random_seed=42))

    report = run_diagnostics(panel)

    assert [result.name for result in report.results] == [
        "pre_trend",
        "placebo_in_time",
        "data_adequacy",
        "control_quality",
        "small_cluster",
        "precision_power",
    ]
    assert report.overall_severity == "info"
    assert "does not prove parallel trends" in report.by_name("pre_trend").explanation


def test_too_few_control_units_raise_a_data_adequacy_concern() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(n_treated_units=20, n_control_units=1, random_seed=77)
    )

    report = run_diagnostics(panel)

    assert report.by_name("data_adequacy").severity == "serious"
    assert report.by_name("small_cluster").severity == "warning"


def test_non_parallel_pretrends_trigger_pretrend_and_control_quality_concerns() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(pre_trend_difference=2.0, noise_std=1.0, random_seed=42)
    )

    report = run_diagnostics(panel)

    assert report.by_name("pre_trend").severity == "serious"
    assert report.by_name("control_quality").severity == "serious"


def test_fake_pre_treatment_effect_triggers_placebo_concern() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(fake_pre_treatment_effect=15.0, noise_std=1.0, random_seed=42)
    )

    report = run_diagnostics(panel)

    assert report.by_name("placebo_in_time").severity == "serious"


def test_high_noise_triggers_precision_concern() -> None:
    panel = generate_synthetic_panel(SimulationConfig(noise_std=100.0, random_seed=42))

    report = run_diagnostics(panel)

    assert report.by_name("precision_power").severity == "serious"


def test_missing_data_triggers_data_adequacy_concern() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(missing_data_rate=0.10, random_seed=42)
    )

    report = run_diagnostics(panel)

    assert report.by_name("data_adequacy").severity == "serious"
