
"""Configuration for deterministic synthetic panel-data simulations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Inputs for one balanced synthetic Difference-in-Differences panel."""

    treatment_effect: float = 20.0
    noise_std: float = 5.0
    n_treated_units: int = 20
    n_control_units: int = 20
    n_pre_periods: int = 12
    n_post_periods: int = 12
    random_seed: int = 42
    common_time_trend: float = 1.0
    unit_effect_std: float = 5.0
    pre_trend_difference: float = 0.0
    fake_pre_treatment_effect: float = 0.0
    missing_data_rate: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "n_treated_units",
            "n_control_units",
            "n_pre_periods",
            "n_post_periods",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer.")

        for field_name in ("noise_std", "unit_effect_std"):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative.")

        if not 0 <= self.missing_data_rate < 1:
            raise ValueError("missing_data_rate must be between 0 (inclusive) and 1 (exclusive).")


@dataclass(frozen=True)
class DiagnosticThresholds:
    """Named judgment thresholds used consistently by every diagnostic."""

    # A two-sided p-value below this is treated as evidence that raises concern.
    significance_level: float = 0.05
    # Fewer units in either group leaves comparison-group evidence too thin.
    minimum_treated_units: int = 5
    minimum_control_units: int = 5
    # Fewer periods cannot meaningfully describe pre- or post-intervention change.
    minimum_pre_periods: int = 3
    minimum_post_periods: int = 2
    # More missing panel cells than this makes the observed panel materially incomplete.
    maximum_missing_fraction: float = 0.05
    # Very few independent unit clusters make cluster-robust inference unstable.
    minimum_effective_clusters: int = 10
    small_cluster_warning_threshold: int = 30
    # Pre-period group means should move closely together for a reassuring control check.
    minimum_pretrend_correlation: float = 0.90
    maximum_pretrend_slope_difference: float = 0.50
    # A wider interval is too imprecise for this project's 20-unit reference effect.
    maximum_ci_half_width: float = 10.0
    # The MDE is the approximate effect needed to exceed a 95% normal critical value.
    normal_critical_value: float = 1.96

    def __post_init__(self) -> None:
        if not 0 < self.significance_level < 1:
            raise ValueError("significance_level must be between 0 and 1.")
        if not 0 <= self.maximum_missing_fraction < 1:
            raise ValueError("maximum_missing_fraction must be between 0 and 1.")
        if not -1 <= self.minimum_pretrend_correlation <= 1:
            raise ValueError("minimum_pretrend_correlation must be between -1 and 1.")


DEFAULT_DIAGNOSTIC_THRESHOLDS = DiagnosticThresholds()
