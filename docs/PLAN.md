# Project Roadmap

## Intended architecture

React frontend → FastAPI REST API → independent Python causal engine

## Tier 1

- Synthetic panel-data generator with known treatment effects
- Tested DiD estimator
- Tested event-study output
- Tested diagnostics: pre-trend, placebo-in-time, data adequacy, control quality, small-cluster warning, precision/power
- Deterministic verdict logic
- FastAPI backend
- One clean and one intentionally broken synthetic demonstration
- Documentation

## Tier 2

- React + TypeScript + Vite frontend
- Docker Compose
- GitHub Actions
- Deployment
- Delhi Odd-Even / CPCB case study
