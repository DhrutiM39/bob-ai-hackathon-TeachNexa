"""
Syllabus service — all business logic for syllabus processing.

Keeps the route handler thin: the router validates the HTTP layer,
the service owns the domain logic.

No persistence or AI calls yet (Milestone 2 scope).
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from ..schemas.syllabus import SyllabusRequest, SyllabusResponse


def _generate_syllabus_id(course_name: str, syllabus_text: str) -> str:
    """
    Produce a deterministic-then-unique ID for a submission.

    Format: ``cg-<8-char-content-hash>-<8-char-uuid-fragment>``

    The content hash makes IDs human-traceable; the UUID suffix ensures
    two submissions with identical content still receive distinct IDs.
    """
    content_hash = hashlib.sha256(
        f"{course_name}:{syllabus_text}".encode()
    ).hexdigest()[:8]
    unique_suffix = uuid.uuid4().hex[:8]
    return f"cg-{content_hash}-{unique_suffix}"


def process_syllabus(request: SyllabusRequest) -> SyllabusResponse:
    """
    Validate, normalise, and acknowledge a syllabus submission.

    Validation is enforced by the Pydantic schema; this function handles
    any additional business-level transformations and builds the response.
    """
    syllabus_id = _generate_syllabus_id(request.course_name, request.syllabus_text)

    return SyllabusResponse(
        status="accepted",
        syllabus_id=syllabus_id,
        course_name=request.course_name,
        syllabus_text=request.syllabus_text,
        character_count=len(request.syllabus_text),
        message=(
            f"Syllabus for '{request.course_name}' received and validated successfully. "
            f"Syllabus ID: {syllabus_id}"
        ),
    )
