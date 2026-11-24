
"""Adapters between HTTP schemas and the independent causal engine."""

import pandas as pd

from app.schemas import (
    DiagnosticResultResponse,
    DidResultResponse,
    EventStudyEffectResponse,
    EventStudyResponse,
    PanelAnalysisRequest,
    SimulationConfigRequest,
    ValidationReportResponse,
    VerdictResponse,
)
from causal_engine.config import SimulationConfig
from causal_engine.reporting import ValidationReport, create_validation_report
from causal_engine.simulation import generate_synthetic_panel


def analyze_panel_request(request: PanelAnalysisRequest) -> ValidationReportResponse:
    """Convert submitted records into a panel and serialize engine results."""
    panel = pd.DataFrame(record.model_dump() for record in request.records)
    return _to_response(create_validation_report(panel))


def analyze_synthetic_request(
    request: SimulationConfigRequest,
) -> ValidationReportResponse:
    """Generate a deterministic synthetic panel and return its validation report."""
    config = SimulationConfig(**request.model_dump())
    return _to_response(create_validation_report(generate_synthetic_panel(config)))


def _to_response(report: ValidationReport) -> ValidationReportResponse:
    did_response = None
    if report.did_result is not None:
        did = report.did_result
        did_response = DidResultResponse(
            effect_estimate=did.effect_estimate,
            confidence_interval_lower=did.confidence_interval_lower,
            confidence_interval_upper=did.confidence_interval_upper,
            p_value=did.p_value,
            standard_error=did.standard_error,
            n_observations=did.n_observations,
            n_treated_units=did.n_treated_units,
            n_control_units=did.n_control_units,
            n_clusters=did.n_clusters,
            n_pre_observations=did.n_pre_observations,
            n_post_observations=did.n_post_observations,
            standard_error_type=did.standard_error_type,
        )

    event_study_response = None
    if report.event_study_result is not None:
        event = report.event_study_result
        event_study_response = EventStudyResponse(
            effects=[EventStudyEffectResponse(**row) for row in event.effects.to_dict("records")],
            reference_period=event.reference_period,
            zero_reference_line=event.zero_reference_line,
            n_clusters=event.n_clusters,
            standard_error_type=event.standard_error_type,
        )

    return ValidationReportResponse(
        did_result=did_response,
        event_study_result=event_study_response,
        diagnostics=[
            DiagnosticResultResponse(
                name=result.name,
                severity=result.severity,
                explanation=result.explanation,
                metrics=dict(result.metrics),
            )
            for result in report.diagnostic_report.results
        ],
        verdict=VerdictResponse(
            label=report.verdict.label,
            severity=report.verdict.severity,
            reasons=list(report.verdict.reasons),
            recommended_next_steps=list(report.verdict.recommended_next_steps),
            methodological_caveat=report.verdict.methodological_caveat,
        ),
        model_unavailable_reason=report.model_unavailable_reason,
    )
