"""schemas package — re-exports all Pydantic request/response models."""

# Health schemas
from .health import HealthResponse

# Syllabus schemas
from .syllabus import SyllabusRequest, SyllabusResponse

# Course generation schemas
from .generate import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    ModuleOut,
    TopicOut,
    ErrorResponse,
)

__all__ = [
    "HealthResponse",
    "SyllabusRequest",
    "SyllabusResponse",
    "GenerateCourseRequest",
    "GenerateCourseResponse",
    "ModuleOut",
    "TopicOut",
    "ErrorResponse",
]
