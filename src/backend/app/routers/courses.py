"""
Course router — database-backed course endpoints.

Routes implemented here:
  GET  /api/courses                   → list all courses (with aggregate counts)
  GET  /api/courses/{course_id}       → full course detail (modules + topics)
  POST /api/v1/courses/generate       → generate course via AI + persist to DB

Design:
  - Route handlers stay thin: validate → service call → respond.
  - No SQL inside this file; all DB access goes through helper functions below.
  - DeepSeekClient is injected via Depends() so it can be swapped in tests.
  - All DB writes use a single transaction (via get_db's commit-on-yield).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.schemas.courses import (
    CourseDetail,
    CourseListItem,
    CoursesListResponse,
    ModuleOut,
    TopicOut,
)
from backend.app.schemas.generate import (
    GenerateCourseRequest,
    GenerateCourseResponse,
)
from backend.app.services.deepseek_client import DeepSeekClient, get_deepseek_client
from backend.database.models import Course, Module, Topic
from backend.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["courses"])


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count_topics_for_course(db: Session, course_id: uuid.UUID) -> int:
    """Return the total number of topics across all modules of a course."""
    return (
        db.query(func.count(Topic.id))
        .join(Module, Topic.module_id == Module.id)
        .filter(Module.course_id == course_id)
        .scalar()
        or 0
    )


def _build_course_detail(db: Session, course: Course) -> CourseDetail:
    """Convert a Course ORM object (with eager-loaded modules/topics) to CourseDetail."""
    modules_out: list[ModuleOut] = []
    total_topics = 0

    for mod in sorted(course.modules, key=lambda m: m.order_no):
        topics_out: list[TopicOut] = []
        for topic in sorted(mod.topics, key=lambda t: t.order_no):
            topics_out.append(
                TopicOut(
                    id=topic.id,
                    title=topic.title,
                    description=topic.description,
                    order_no=topic.order_no,
                    has_content=bool(topic.content_items),
                    has_quiz=bool(topic.quizzes),
                )
            )
            total_topics += 1
        modules_out.append(
            ModuleOut(
                id=mod.id,
                title=mod.title,
                description=mod.description,
                order_no=mod.order_no,
                topics=topics_out,
            )
        )

    return CourseDetail(
        id=course.id,
        title=course.title,
        description=course.description,
        syllabus_text=course.syllabus_text,
        status="ready",
        created_at=course.created_at,
        updated_at=course.updated_at,
        modules=modules_out,
        total_topics=total_topics,
        completed_topics=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/courses",
    response_model=CoursesListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all courses",
    description="Returns all courses with aggregate module/topic counts. "
                "Does NOT include the full module/topic tree.",
)
def list_courses(db: Session = Depends(get_db)) -> CoursesListResponse:
    """Return all courses ordered by creation date (newest first)."""
    courses = (
        db.query(Course)
        .options(
            joinedload(Course.modules).joinedload(Module.topics)
        )
        .order_by(Course.created_at.desc())
        .all()
    )

    items: list[CourseListItem] = []
    for course in courses:
        total_modules = len(course.modules)
        total_topics = sum(len(m.topics) for m in course.modules)
        items.append(
            CourseListItem(
                id=course.id,
                title=course.title,
                description=course.description,
                status="ready",
                created_at=course.created_at,
                updated_at=course.updated_at,
                total_modules=total_modules,
                total_topics=total_topics,
                completed_topics=0,
            )
        )

    return CoursesListResponse(courses=items, total=len(items))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses/{course_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/courses/{course_id}",
    response_model=CourseDetail,
    status_code=status.HTTP_200_OK,
    summary="Get a single course with full hierarchy",
    responses={
        404: {"description": "Course not found."},
        400: {"description": "Invalid course ID format."},
    },
)
def get_course(course_id: str, db: Session = Depends(get_db)) -> CourseDetail:
    """
    Return a single course with its full module + topic tree.

    Raises 400 if ``course_id`` is not a valid UUID.
    Raises 404 if no course with that ID exists.
    """
    # Validate UUID format before hitting the DB
    try:
        parsed_id = uuid.UUID(str(course_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{course_id}' is not a valid course ID.",
        )

    course = (
        db.query(Course)
        .options(
            joinedload(Course.modules)
            .joinedload(Module.topics)
            .joinedload(Topic.content_items),
            joinedload(Course.modules)
            .joinedload(Module.topics)
            .joinedload(Topic.quizzes),
        )
        .filter(Course.id == parsed_id)
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_id}' not found.",
        )

    return _build_course_detail(db, course)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/courses/generate
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/api/v1/courses/generate",
    response_model=GenerateCourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a structured course from a syllabus",
    description=(
        "Sends the provided syllabus to DeepSeek, which returns a "
        "structured hierarchy of modules and topics. The result is persisted "
        "to the database and the full Course object is returned."
    ),
    responses={
        400: {"description": "owner_id does not exist in the database."},
        422: {"description": "DeepSeek returned an invalid response."},
        502: {"description": "AI service temporarily unavailable."},
    },
)
def generate_course(
    body: GenerateCourseRequest,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
) -> GenerateCourseResponse:
    """
    1. Verify the owner_id exists.
    2. Call DeepSeek to parse the syllabus into modules/topics.
    3. Persist a Course row, then Module rows, then Topic rows (single transaction).
    4. Return the full hierarchy as a GenerateCourseResponse.
    """
    from backend.database.models import User

    # ── 0. Verify owner exists (avoid FK violation mid-transaction) ───────
    owner = db.query(User).filter(User.id == body.owner_id).first()
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"User '{body.owner_id}' not found. "
                "Seed a demo user first — see docs/setup-guide.md."
            ),
        )

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
    db.flush()  # get course.id before inserting children

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
        db.flush()  # get module.id before inserting topics

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

    return GenerateCourseResponse(
        course_id=course.id,
        title=course.title,
        description=course.description,
        syllabus_text=course.syllabus_text,
        modules=module_outs,
        model_used=model_used,
    )
