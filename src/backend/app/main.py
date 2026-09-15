"""
CourseGenie AI — FastAPI application entry point.

Start with:
    uvicorn backend.app.main:app --reload --port 8000 --app-dir src
or (from src/backend/):
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import get_settings, settings
from .routers import courses, topics

logging.basicConfig(
    level=logging.DEBUG if settings.app_env == "development" else logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at application startup before the server starts accepting requests.

    Seeds the demo user (UUID 00000000-0000-0000-0000-000000000001) so that
    course generation always has a valid owner_id foreign key.  The seed is
    idempotent — it is safe to call on every restart.

    NOTE: This is a hackathon-MVP mechanism, not a real authentication system.
    Full per-user auth is future work.
    """
    from .seed import seed_demo_user
    from backend.database.session import SessionLocal

    db = SessionLocal()
    try:
        seed_demo_user(db)
    except Exception:
        logger.exception("Startup seed failed — continuing without demo user")
    finally:
        db.close()

    yield  # application runs here


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered professor assistant that transforms a syllabus "
        "into a complete, structured learning experience. "
        "Powered by DeepSeek AI and PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
# Milestone 1/2 routes: GET /health, POST /api/v1/syllabus
app.include_router(api_router)

# Database-backed course routes:
#   GET  /api/courses
#   GET  /api/courses/{course_id}
#   POST /api/v1/courses/generate
app.include_router(courses.router)

# Topic content / quiz / revision routes:
#   POST /api/topics/{topic_id}/generate-content
#   GET  /api/topics/{topic_id}/content
#   POST /api/topics/{topic_id}/generate-quiz
#   GET  /api/topics/{topic_id}/quiz
#   POST /api/courses/{course_id}/generate-revision
#   GET  /api/courses/{course_id}/revision
app.include_router(topics.router)
