
"""End-to-end, presentation-ready summaries of synthetic DiD validation runs."""

from dataclasses import dataclass

import pandas as pd

from causal_engine.diagnostics import DiagnosticReport, run_diagnostics
from causal_engine.did import DidResult, estimate_difference_in_differences
from causal_engine.event_study import EventStudyResult, estimate_event_study
from causal_engine.verdict import Verdict, determine_verdict


@dataclass(frozen=True)
class ValidationReport:
    """One coherent view of estimation evidence and its methodological caveat."""

    did_result: DidResult | None
    event_study_result: EventStudyResult | None
    diagnostic_report: DiagnosticReport
    verdict: Verdict
    model_unavailable_reason: str | None


def create_validation_report(data: pd.DataFrame) -> ValidationReport:
    """Run the existing validation modules without changing the supplied panel."""
    diagnostic_report = run_diagnostics(data)
    verdict = determine_verdict(diagnostic_report)

    if data["outcome"].isna().any():
        return ValidationReport(
            did_result=None,
            event_study_result=None,
            diagnostic_report=diagnostic_report,
            verdict=verdict,
            model_unavailable_reason=(
                "Model estimates are unavailable because outcome values are missing."
            ),
        )

    return ValidationReport(
        did_result=estimate_difference_in_differences(data),
        event_study_result=estimate_event_study(data),
        diagnostic_report=diagnostic_report,
        verdict=verdict,
        model_unavailable_reason=None,
    )


def format_validation_report(report: ValidationReport) -> str:
    """Format a concise human-readable summary without overstating evidence."""
    lines = [
        f"Verdict: {report.verdict.label}",
        f"Severity: {report.verdict.severity}",
    ]
    if report.did_result is None:
        lines.append(report.model_unavailable_reason or "Model estimates are unavailable.")
    else:
        result = report.did_result
        lines.append(
            "Estimated DiD effect: "
            f"{result.effect_estimate:.3f} "
            f"(95% CI {result.confidence_interval_lower:.3f} to "
            f"{result.confidence_interval_upper:.3f}; {result.standard_error_type} SE)"
        )

    lines.append("Diagnostics:")
    lines.extend(
        f"- {result.name}: {result.severity} — {result.explanation}"
        for result in report.diagnostic_report.results
    )
    lines.append(f"Caveat: {report.verdict.methodological_caveat}")
    return "\n".join(lines)
