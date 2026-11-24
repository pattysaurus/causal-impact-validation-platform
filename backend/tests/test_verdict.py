
import pytest

from causal_engine.config import SimulationConfig
from causal_engine.diagnostics import run_diagnostics
from causal_engine.simulation import generate_synthetic_panel
from causal_engine.verdict import determine_verdict


@pytest.mark.parametrize(
    "config",
    [
        SimulationConfig(pre_trend_difference=2.0, noise_std=1.0, random_seed=42),
        SimulationConfig(fake_pre_treatment_effect=15.0, noise_std=1.0, random_seed=42),
        SimulationConfig(n_treated_units=20, n_control_units=1, random_seed=42),
        SimulationConfig(noise_std=100.0, random_seed=42),
        SimulationConfig(missing_data_rate=0.10, random_seed=42),
    ],
    ids=["non_parallel_pretrends", "fake_pre_effect", "few_controls", "high_noise", "missing_data"],
)
def test_every_broken_simulation_returns_dont_trust_verdict(config: SimulationConfig) -> None:
    verdict = determine_verdict(run_diagnostics(generate_synthetic_panel(config)))

    assert verdict.label == "Don't trust this estimate"
    assert verdict.severity == "serious"
    assert "cannot establish causality" in verdict.methodological_caveat


def test_clean_default_simulation_returns_credible_with_caveat() -> None:
    verdict = determine_verdict(
        run_diagnostics(generate_synthetic_panel(SimulationConfig(random_seed=42)))
    )

    assert verdict.label == "Credible"
    assert verdict.severity == "info"
    assert "cannot establish causality" in verdict.methodological_caveat


def test_small_cluster_warning_returns_suggestive_verdict() -> None:
    verdict = determine_verdict(
        run_diagnostics(
            generate_synthetic_panel(
                SimulationConfig(n_treated_units=10, n_control_units=10, random_seed=7)
            )
        )
    )

    assert verdict.label == "Suggestive"
    assert verdict.severity == "warning"
