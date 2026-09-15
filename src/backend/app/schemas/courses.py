"""
Pydantic schemas for the course retrieval, generation, and edit APIs.

GET   /api/courses          → list[CourseListItem]
GET   /api/courses/{id}     → CourseDetail
POST  /api/v1/courses/generate → GenerateCourseResponse  (see generate.py)
PATCH /api/courses/{id}     → CourseDetail
PATCH /api/modules/{id}     → ModuleOut
PATCH /api/topics/{id}      → TopicOut
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Nested output schemas (shared by list + detail)
# ─────────────────────────────────────────────────────────────────────────────

class TopicOut(BaseModel):
    """A single topic inside a module."""

    id: uuid.UUID
    title: str
    description: str | None = None
    order_no: int
    # Derived convenience flags — content/quiz not yet generated at creation time
    has_content: bool = False
    has_quiz: bool = False

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    """A module with its child topics."""

    id: uuid.UUID
    title: str
    description: str | None = None
    order_no: int
    topics: list[TopicOut] = []

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Course list item  (GET /api/courses)
# ─────────────────────────────────────────────────────────────────────────────

class CourseListItem(BaseModel):
    """
    Lightweight course representation for list responses.
    Does NOT include the full module/topic tree to keep the payload small.
    Includes computed aggregate counts so the frontend can show progress bars
    without fetching each course individually.
    """

    id: uuid.UUID
    title: str
    description: str | None = None
    status: str = "ready"          # always "ready" for DB-backed courses
    created_at: datetime
    updated_at: datetime
    # Aggregate counts computed from related rows
    total_modules: int = 0
    total_topics: int = 0
    completed_topics: int = 0      # always 0 until progress tracking is added

    model_config = {"from_attributes": True}


class CoursesListResponse(BaseModel):
    """Envelope for GET /api/courses."""

    courses: list[CourseListItem]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# Course detail  (GET /api/courses/{course_id})
# ─────────────────────────────────────────────────────────────────────────────

class CourseDetail(BaseModel):
    """
    Full course representation including the module + topic hierarchy.
    Returned by GET /api/courses/{course_id}.
    """

    id: uuid.UUID
    title: str
    description: str | None = None
    syllabus_text: str | None = None
    status: str = "ready"
    created_at: datetime
    updated_at: datetime
    modules: list[ModuleOut] = []
    # Aggregate convenience fields
    total_topics: int = 0
    completed_topics: int = 0

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Edit request schemas  (PATCH endpoints)
# ─────────────────────────────────────────────────────────────────────────────

class CourseUpdate(BaseModel):
    """Body for PATCH /api/courses/{course_id}. All fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


class ModuleUpdate(BaseModel):
    """Body for PATCH /api/modules/{module_id}. All fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


class TopicUpdate(BaseModel):
    """Body for PATCH /api/topics/{topic_id}. All fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
