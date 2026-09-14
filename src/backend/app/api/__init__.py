"""API package — registers all routers."""
from fastapi import APIRouter
from .health import router as health_router
from .syllabus import router as syllabus_router

api_router = APIRouter()

# Milestone 1 — liveness
api_router.include_router(health_router)

# Milestone 2+ — versioned API
api_router.include_router(syllabus_router, prefix="/api/v1")
