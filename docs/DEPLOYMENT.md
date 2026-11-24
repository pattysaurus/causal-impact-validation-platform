# Deployment

## Local containers

Run `docker compose up --build`. The API is available at `http://localhost:8000/api/v1/health` and the frontend at `http://localhost:5173`.

## Hosted API

`render.yaml` defines both services: a Docker-based API with a health check and a static frontend. Connect this repository to a Render account, create the services from the blueprint, and replace the `onrender.com` names in the blueprint if your chosen service names differ.

The local Vite server proxies `/api` to port 8000. The frontend container's Nginx proxy sends `/api` to the Compose `backend` service, so local container use needs no browser CORS configuration.

Deployment does not alter the methodological caveat: any app result remains decision support and cannot establish causality.
