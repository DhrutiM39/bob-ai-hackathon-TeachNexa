"""
POST /api/v1/courses/generate

Accepts a validated syllabus, calls DeepSeek to generate a structured
module/topic outline, persists a Course + Modules + Topics to the database,
and returns the full hierarchy.

Design principles:
  - Route handler stays thin: validate → call service → persist → respond.
  - No SDK calls or SQL inside this file.
  - DeepSeekClient is injected via Depends() so it can be swapped in tests.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.schemas import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    ModuleOut,
    TopicOut,
)
from backend.app.services.deepseek_client import DeepSeekClient, get_deepseek_client
from backend.database.models import Course, Module, Topic
from backend.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/courses/generate
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GenerateCourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a structured course from a syllabus",
    description=(
        "Sends the provided syllabus to DeepSeek, which returns a "
        "structured hierarchy of modules and topics. The result is persisted "
        "to the database and the full Course object is returned."
    ),
)
def generate_course(
    body: GenerateCourseRequest,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
) -> GenerateCourseResponse:
    """
    1. Call DeepSeek to parse the syllabus into modules/topics.
    2. Persist a Course row, then Module rows, then Topic rows.
    3. Return the full hierarchy as a GenerateCourseResponse.
    """

    # ── 1. Generate structure via DeepSeek ───────────────────────────────
    try:
        raw_modules, model_used = ds.generate_course_structure(body.syllabus_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DeepSeek returned an invalid response: {exc}",
        )
    except RuntimeError as exc:
        logger.error("DeepSeek call failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service unavailable: {exc}",
        )

    # ── 2. Persist to database ────────────────────────────────────────────
    course = Course(
        id=uuid.uuid4(),
        title=body.title,
        description=body.description,
        syllabus_text=body.syllabus_text,
        owner_id=body.owner_id,
    )
    db.add(course)
    db.flush()  # obtain course.id before inserting children

    module_outs: list[ModuleOut] = []

    for mod_order, raw_mod in enumerate(raw_modules, start=1):
        module = Module(
            id=uuid.uuid4(),
            course_id=course.id,
            title=raw_mod.get("title", f"Module {mod_order}"),
            description=raw_mod.get("description"),
            order_no=mod_order,
        )
        db.add(module)
        db.flush()  # obtain module.id before inserting topics

        topic_outs: list[TopicOut] = []
        raw_topics: list[dict] = raw_mod.get("topics", [])

        for topic_order, raw_topic in enumerate(raw_topics, start=1):
            topic = Topic(
                id=uuid.uuid4(),
                module_id=module.id,
                title=raw_topic.get("title", f"Topic {topic_order}"),
                description=raw_topic.get("description"),
                order_no=topic_order,
            )
            db.add(topic)
            db.flush()

            topic_outs.append(
                TopicOut(
                    id=topic.id,
                    title=topic.title,
                    description=topic.description,
                    order_no=topic.order_no,
                )
            )

        module_outs.append(
            ModuleOut(
                id=module.id,
                title=module.title,
                description=module.description,
                order_no=module.order_no,
                topics=topic_outs,
            )
        )

    # db.commit() is handled by get_db() on successful yield
    logger.info(
        "Generated course '%s' (%s): %d modules, model=%s",
        course.title,
        course.id,
        len(module_outs),
        model_used,
    )

    # ── 3. Return response ────────────────────────────────────────────────
    return GenerateCourseResponse(
        course_id=course.id,
        title=course.title,
        description=course.description,
        syllabus_text=course.syllabus_text,
        modules=module_outs,
        model_used=model_used,
    )
