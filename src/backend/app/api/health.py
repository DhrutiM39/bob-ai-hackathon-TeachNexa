"""Health-check router — GET /health"""
from fastapi import APIRouter
from ..schemas.health import HealthResponse
from ..config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check() -> HealthResponse:
    """Returns service liveness status."""
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name)
