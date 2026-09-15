"""
Pydantic schemas for the topic content / quiz / revision APIs.

POST /api/topics/{id}/generate-content → TopicContentResponse
GET  /api/topics/{id}/content          → TopicContentResponse
POST /api/topics/{id}/generate-quiz    → QuizResponse
GET  /api/topics/{id}/quiz             → QuizResponse
POST /api/topics/{id}/generate-revision → RevisionResponse
GET  /api/courses/{id}/revision        → RevisionResponse
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Topic content schemas
# ─────────────────────────────────────────────────────────────────────────────

class KeyConcept(BaseModel):
    """A single key concept with its definition."""
    term: str
    definition: str


class ContentExample(BaseModel):
    """An illustrative example within topic content."""
    title: str = ""
    content: str


class TopicContentResponse(BaseModel):
    """
    Full learning content for a topic.
    Returned by GET/POST /api/topics/{id}/content.
    """
    topic_id: uuid.UUID
    title: str
    objectives: list[str] = []
    explanation: str = ""
    key_concepts: list[KeyConcept] = []
    examples: list[ContentExample] = []
    summary: str = ""
    further_reading: list[str] = []
    generated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Quiz schemas
# ─────────────────────────────────────────────────────────────────────────────

class QuizOption(BaseModel):
    """A single MCQ answer choice."""
    id: str
    text: str


class QuizQuestion(BaseModel):
    """
    A single quiz question.
    correct_index is the 0-based index into the options list.
    """
    id: str
    text: str
    options: list[QuizOption]
    correct_index: int
    explanation: str = ""


class QuizResponse(BaseModel):
    """
    A complete quiz for a topic.
    Returned by GET/POST /api/topics/{id}/quiz.
    """
    id: uuid.UUID
    topic_id: uuid.UUID
    title: str
    questions: list[QuizQuestion]
    generated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Revision schemas
# ─────────────────────────────────────────────────────────────────────────────

class RevisionQuestion(BaseModel):
    """A practice or question-bank item."""
    id: str
    text: str
    options: list[QuizOption]
    correct_index: int
    explanation: str = ""


class RevisionResponse(BaseModel):
    """
    Revision materials for an entire course.
    Returned by GET/POST /api/courses/{id}/revision.
    """
    course_id: uuid.UUID
    quick_notes: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    practice_questions: list[RevisionQuestion] = Field(default_factory=list)
    question_bank: list[RevisionQuestion] = Field(default_factory=list)
    generated_at: datetime

    model_config = {"from_attributes": True}
