"""
CourseGenie AI — FastAPI application entry point.

Start with:
    uvicorn src.backend.app.main:app --reload --port 8000
or (from src/backend/):
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from .config import get_settings
from .api import api_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered professor assistant that transforms a syllabus "
        "into a complete, structured learning experience."
    ),
)

# Register all API routes
app.include_router(api_router)
