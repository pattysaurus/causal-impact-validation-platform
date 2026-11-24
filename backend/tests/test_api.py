import json

import pytest
from pydantic import ValidationError

from app.api.routes import analyze_synthetic, health_check, router
from app.schemas import PanelAnalysisRequest, SimulationConfigRequest
from app.services import analyze_panel_request, analyze_synthetic_request
from causal_engine.config import SimulationConfig
from causal_engine.simulation import generate_synthetic_panel


def test_api_router_registers_expected_contract() -> None:
    paths = {route.path for route in router.routes}

    assert paths == {"/api/v1/health", "/api/v1/analysis", "/api/v1/synthetic-analysis"}


def test_route_handlers_delegate_to_the_service_layer() -> None:
    response = analyze_synthetic(SimulationConfigRequest(random_seed=42))

    assert health_check() == {"status": "ok"}
    assert response.verdict.label == "Credible"


def test_synthetic_analysis_returns_clean_report() -> None:
    response = analyze_synthetic_request(SimulationConfigRequest(random_seed=42))

    assert response.verdict.label == "Credible"
    assert response.did_result is not None
    assert response.did_result.standard_error_type == "unit-clustered"
    assert response.event_study_result is not None
    assert response.event_study_result.reference_period == -1


def test_synthetic_analysis_returns_broken_report() -> None:
    response = analyze_synthetic_request(
        SimulationConfigRequest(
            pre_trend_difference=2.0, noise_std=1.0, random_seed=42
        )
    )

    assert response.verdict.label == "Don't trust this estimate"


def test_panel_analysis_accepts_serialized_panel_data() -> None:
    panel = generate_synthetic_panel(SimulationConfig(random_seed=42))
    records = json.loads(
        panel.drop(
            columns=["treatment_effect_applied", "fake_pre_treatment_effect_applied"]
        ).to_json(orient="records", date_format="iso")
    )

    response = analyze_panel_request(PanelAnalysisRequest(records=records))

    assert response.did_result is not None
    assert response.did_result.n_observations == len(panel)


def test_missing_outcomes_withhold_model_outputs() -> None:
    response = analyze_synthetic_request(
        SimulationConfigRequest(missing_data_rate=0.10, random_seed=42)
    )

    assert response.did_result is None
    assert response.model_unavailable_reason is not None


def test_invalid_panel_data_fails_schema_validation() -> None:
    with pytest.raises(ValidationError):
        PanelAnalysisRequest(records=[{"unit_id": "only-id"}])
