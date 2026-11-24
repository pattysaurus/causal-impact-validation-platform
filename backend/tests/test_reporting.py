import pandas as pd

from causal_engine.config import SimulationConfig
from causal_engine.reporting import create_validation_report, format_validation_report
from causal_engine.simulation import generate_synthetic_panel


def test_clean_synthetic_report_contains_all_validation_outputs() -> None:
    panel = generate_synthetic_panel(SimulationConfig(random_seed=42))

    report = create_validation_report(panel)
    rendered = format_validation_report(report)

    assert report.verdict.label == "Credible"
    assert report.did_result is not None
    assert report.event_study_result is not None
    assert report.model_unavailable_reason is None
    assert "Estimated DiD effect:" in rendered
    assert "cannot establish causality" in rendered


def test_broken_synthetic_report_surfaces_diagnostic_reasons() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(pre_trend_difference=2.0, noise_std=1.0, random_seed=42)
    )

    report = create_validation_report(panel)
    rendered = format_validation_report(report)

    assert report.verdict.label == "Don't trust this estimate"
    assert report.did_result is not None
    assert "pre_trend: serious" in rendered


def test_missing_outcomes_preserve_diagnostics_but_withhold_model_outputs() -> None:
    panel = generate_synthetic_panel(
        SimulationConfig(missing_data_rate=0.10, random_seed=42)
    )
    original_panel = panel.copy(deep=True)

    report = create_validation_report(panel)
    rendered = format_validation_report(report)

    assert report.verdict.label == "Don't trust this estimate"
    assert report.did_result is None
    assert report.event_study_result is None
    assert report.model_unavailable_reason in rendered
    pd.testing.assert_frame_equal(panel, original_panel)
