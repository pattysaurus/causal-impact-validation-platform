
"""HTTP routes for CIVP analysis requests."""

from fastapi import APIRouter, HTTPException

from app.schemas import (
    PanelAnalysisRequest,
    SimulationConfigRequest,
    ValidationReportResponse,
)
from app.services import analyze_panel_request, analyze_synthetic_request


router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analysis", response_model=ValidationReportResponse)
def analyze_panel(request: PanelAnalysisRequest) -> ValidationReportResponse:
    try:
        return analyze_panel_request(request)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/synthetic-analysis", response_model=ValidationReportResponse)
def analyze_synthetic(request: SimulationConfigRequest) -> ValidationReportResponse:
    try:
        return analyze_synthetic_request(request)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
