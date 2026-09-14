"""Pydantic schemas for the syllabus API."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Minimum character length we accept for a syllabus body.
# Too-short strings (e.g. "AI") carry no usable structure.
SYLLABUS_MIN_LENGTH = 20


class SyllabusRequest(BaseModel):
    """Payload for POST /api/v1/syllabus."""

    course_name: str = Field(
        ...,
        min_length=1,
        description="Name of the course (must not be blank).",
        examples=["Introduction to Artificial Intelligence"],
    )
    syllabus_text: str = Field(
        ...,
        description="Raw syllabus content submitted by the professor.",
        examples=["Module 1: Introduction to AI\nModule 2: Search Algorithms"],
    )

    @field_validator("course_name")
    @classmethod
    def course_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("course_name must not be blank or whitespace only.")
        return v.strip()

    @field_validator("syllabus_text")
    @classmethod
    def syllabus_text_valid(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("syllabus_text must not be blank or whitespace only.")
        if len(stripped) < SYLLABUS_MIN_LENGTH:
            raise ValueError(
                f"syllabus_text is too short (minimum {SYLLABUS_MIN_LENGTH} characters). "
                "Please provide a meaningful syllabus."
            )
        return stripped


class SyllabusResponse(BaseModel):
    """Response for a successfully validated syllabus submission."""

    status: str = Field(default="accepted", description="Processing status.")
    syllabus_id: str = Field(description="Unique identifier for this submission.")
    course_name: str = Field(description="Normalised course name.")
    syllabus_text: str = Field(description="Normalised (stripped) syllabus text.")
    character_count: int = Field(description="Character count of the normalised syllabus.")
    message: str = Field(description="Human-readable confirmation message.")
