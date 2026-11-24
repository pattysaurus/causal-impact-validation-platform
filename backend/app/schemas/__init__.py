
"""Typed HTTP request and response contracts for the CIVP API."""

from datetime import datetime

from pydantic import BaseModel, Field


class SimulationConfigRequest(BaseModel):
    treatment_effect: float = 20.0
    noise_std: float = Field(default=5.0, ge=0)
    n_treated_units: int = Field(default=20, ge=1)
    n_control_units: int = Field(default=20, ge=1)
    n_pre_periods: int = Field(default=12, ge=1)
    n_post_periods: int = Field(default=12, ge=1)
    random_seed: int = 42
    common_time_trend: float = 1.0
    unit_effect_std: float = Field(default=5.0, ge=0)
    pre_trend_difference: float = 0.0
    fake_pre_treatment_effect: float = 0.0
    missing_data_rate: float = Field(default=0.0, ge=0, lt=1)


class PanelRecord(BaseModel):
    date: datetime
    unit_id: str
    outcome: float | None
    treated: bool
    post: bool
    intervention_date: datetime


class PanelAnalysisRequest(BaseModel):
    records: list[PanelRecord] = Field(min_length=1)


class DidResultResponse(BaseModel):
    effect_estimate: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    standard_error: float
    n_observations: int
    n_treated_units: int
    n_control_units: int
    n_clusters: int
    n_pre_observations: int
    n_post_observations: int
    standard_error_type: str


class EventStudyEffectResponse(BaseModel):
    relative_time: int
    estimate: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    period_type: str
    is_pre_period: bool
    is_reference_period: bool
    label: str


class EventStudyResponse(BaseModel):
    effects: list[EventStudyEffectResponse]
    reference_period: int
    zero_reference_line: float
    n_clusters: int
    standard_error_type: str


class DiagnosticResultResponse(BaseModel):
    name: str
    severity: str
    explanation: str
    metrics: dict[str, float | int | bool]


class VerdictResponse(BaseModel):
    label: str
    severity: str
    reasons: list[str]
    recommended_next_steps: list[str]
    methodological_caveat: str


class ValidationReportResponse(BaseModel):
    did_result: DidResultResponse | None
    event_study_result: EventStudyResponse | None
    diagnostics: list[DiagnosticResultResponse]
    verdict: VerdictResponse
    model_unavailable_reason: str | None
