
"""Deterministic interpretation of diagnostic evidence, not a causal proof."""

from dataclasses import dataclass
from typing import Literal

from causal_engine.diagnostics import DiagnosticReport, Severity


VerdictLabel = Literal["Credible", "Suggestive", "Don't trust this estimate"]


@dataclass(frozen=True)
class Verdict:
    """A cautious decision-support summary based on diagnostic findings."""

    label: VerdictLabel
    severity: Severity
    reasons: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]
    methodological_caveat: str


def determine_verdict(report: DiagnosticReport) -> Verdict:
    """Map the most serious diagnostic evidence to a reproducible verdict."""
    serious_results = [result for result in report.results if result.severity == "serious"]
    warning_results = [result for result in report.results if result.severity == "warning"]

    caveat = (
        "This verdict summarizes diagnostic evidence only. Passing checks is consistent with the model assumptions, but cannot establish causality."
    )
    if serious_results:
        return Verdict(
            label="Don't trust this estimate",
            severity="serious",
            reasons=tuple(f"{result.name}: {result.explanation}" for result in serious_results),
            recommended_next_steps=_next_steps(serious_results),
            methodological_caveat=caveat,
        )
    if warning_results:
        return Verdict(
            label="Suggestive",
            severity="warning",
            reasons=tuple(f"{result.name}: {result.explanation}" for result in warning_results),
            recommended_next_steps=_next_steps(warning_results),
            methodological_caveat=caveat,
        )
    return Verdict(
        label="Credible",
        severity="info",
        reasons=("All configured diagnostics are consistent with their minimum thresholds.",),
        recommended_next_steps=(
            "Review the substantive intervention context and alternative explanations before using the estimate.",
        ),
        methodological_caveat=caveat,
    )


def _next_steps(results: list) -> tuple[str, ...]:
    steps: list[str] = []
    for result in results:
        if result.name in {"pre_trend", "placebo_in_time", "control_quality"}:
            steps.append("Reassess the comparison group, timing, and untreated trend assumptions.")
        elif result.name == "data_adequacy":
            steps.append("Improve panel completeness and obtain more treated or control units if possible.")
        elif result.name == "small_cluster":
            steps.append("Treat cluster-robust inference cautiously and seek more independent unit clusters.")
        elif result.name == "precision_power":
            steps.append("Collect more informative data or report the estimate as insufficiently precise.")
    return tuple(dict.fromkeys(steps)) or (
        "Review the diagnostic inputs before interpreting the estimate.",
    )
