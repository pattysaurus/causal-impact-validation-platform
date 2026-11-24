# Causal Impact Validation Platform (CIVP)

Difference-in-Differences decision support for intervention analysis.

## Architecture

React + TypeScript frontend → FastAPI REST API → independent Python causal engine

The platform generates and analyzes single-intervention synthetic panels, reports a baseline DiD estimate and event study, checks diagnostic evidence, and presents a caveated verdict. A verdict is decision support only: it cannot establish causality.

## Run locally

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API health endpoint is `http://localhost:8000/api/v1/health`.

## Verify

```powershell
cd backend
python -m pytest -q

cd ../frontend
npm run build
```

For local containers, run `docker compose up --build`. See [API documentation](docs/API.md), [deployment instructions](docs/DEPLOYMENT.md), [methodology](docs/methodology.md), and the [Delhi Odd-Even/CPCB protocol](docs/CASE_STUDY.md).
