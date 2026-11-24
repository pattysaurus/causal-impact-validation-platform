
"""FastAPI application entry point for the CIVP decision-support API."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


app = FastAPI(
    title="Causal Impact Validation Platform",
    description="Difference-in-Differences decision support; outputs cannot establish causality.",
    version="0.1.0",
)
allowed_origins = os.getenv("CIVP_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
