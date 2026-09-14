"""Syllabus API router — POST /api/v1/syllabus"""
from fastapi import APIRouter
from ..schemas.syllabus import SyllabusRequest, SyllabusResponse
from ..services.syllabus_service import process_syllabus

router = APIRouter(tags=["Syllabus"])


@router.post(
    "/syllabus",
    response_model=SyllabusResponse,
    status_code=201,
    summary="Submit a course syllabus",
    responses={
        201: {"description": "Syllabus accepted and validated."},
        422: {"description": "Validation error — check request body fields."},
    },
)
def submit_syllabus(request: SyllabusRequest) -> SyllabusResponse:
    """
    Accept a course syllabus for processing.

    - **course_name**: Non-blank name of the course.
    - **syllabus_text**: Full syllabus content (minimum 20 characters).

    Returns a normalised syllabus record with a unique submission ID.
    """
    return process_syllabus(request)
