"""Pydantic schemas for the course generation API."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class GenerateCourseRequest(BaseModel):
    """
    Body for POST /api/v1/courses/generate.

    owner_id is intentionally absent: the backend derives it server-side from
    the demo user constant (DEMO_OWNER_ID in routers/courses.py).  This removes
    the ability for a client to spoof course ownership.

    NOTE: Hackathon MVP — full per-user authentication is future work.
    """

    syllabus_text: Annotated[
        str,
        Field(
            min_length=50,
            max_length=20_000,
            description="Raw syllabus text to parse and expand into a structured course.",
        ),
    ]
    title: Annotated[
        str,
        Field(
            min_length=3,
            max_length=500,
            description="Human-readable course title.",
        ),
    ]
    description: Annotated[
        str | None,
        Field(default=None, max_length=2000, description="Optional short description."),
    ] = None

    @field_validator("syllabus_text", mode="before")
    @classmethod
    def _strip_syllabus(cls, v: str) -> str:
        return v.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class TopicOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    order_no: int

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    order_no: int
    topics: list[TopicOut] = []

    model_config = {"from_attributes": True}


class GenerateCourseResponse(BaseModel):
    """Returned by POST /api/v1/courses/generate."""

    course_id: uuid.UUID
    title: str
    description: str | None
    syllabus_text: str
    modules: list[ModuleOut]
    model_used: str

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
