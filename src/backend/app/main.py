"""
CourseGenie AI — FastAPI application entry point.

Start with:
    uvicorn backend.app.main:app --reload --port 8000 --app-dir src
or (from src/backend/):
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import get_settings, settings
from .routers import courses

logging.basicConfig(
    level=logging.DEBUG if settings.app_env == "development" else logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered professor assistant that transforms a syllabus "
        "into a complete, structured learning experience. "
        "Powered by IBM watsonx.ai and PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Existing milestone routes: GET /health, POST /api/v1/syllabus
app.include_router(api_router)

# Database-backed course generation: POST /api/v1/courses/generate
app.include_router(courses.router)
