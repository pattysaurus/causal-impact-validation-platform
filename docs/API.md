# API Contract

The FastAPI app exposes a deliberately thin interface over the independent causal engine. Routes do not implement statistical logic.

## Endpoints

- `GET /api/v1/health` returns `{ "status": "ok" }`.
- `POST /api/v1/synthetic-analysis` accepts any `SimulationConfig` fields and returns a validation report for a deterministic synthetic panel.
- `POST /api/v1/analysis` accepts `{ "records": [...] }`, where every record has `date`, `unit_id`, `outcome`, `treated`, `post`, and `intervention_date`.

Both analysis responses contain the DiD result when outcomes are complete, chart-ready event-study effects, diagnostics, a verdict, and a methodological caveat. Missing outcomes retain diagnostics and the verdict but intentionally withhold model estimates. A `Credible` verdict is consistent with configured checks; it cannot establish causality.

## Run and smoke-test

Run `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` from `backend/`, then request `GET http://127.0.0.1:8000/api/v1/health`. The project has been smoke-tested against this endpoint over real HTTP.
