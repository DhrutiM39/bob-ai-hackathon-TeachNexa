"""
Topics router — AI-powered content generation for individual topics.

Routes implemented here:

  POST /api/topics/{topic_id}/generate-content   → generate + persist topic content
  GET  /api/topics/{topic_id}/content            → retrieve existing topic content
  POST /api/topics/{topic_id}/generate-quiz      → generate + persist quiz for topic
  GET  /api/topics/{topic_id}/quiz               → retrieve existing quiz
  POST /api/courses/{course_id}/generate-revision → generate + persist revision for course
  GET  /api/courses/{course_id}/revision          → retrieve existing revision materials

Design:
  - Route handlers are thin: validate → service call → respond.
  - All DB writes use a single transaction via get_db's commit-on-yield.
  - DeepSeekClient injected via Depends() — swappable in tests.
  - Content/quiz/revision data stored in the Content/Quiz/Question ORM models.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.schemas import (
    ContentExample,
    KeyConcept,
    QuizOption,
    QuizQuestion,
    QuizResponse,
    RevisionQuestion,
    RevisionResponse,
    TopicContentResponse,
)
from backend.app.services.deepseek_client import DeepSeekClient, get_deepseek_client
from backend.database.models import Content, Course, Module, Quiz, Question, Topic
from backend.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["topics"])


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_topic_or_404(db: Session, topic_id: str) -> Topic:
    """Parse topic_id UUID and return the Topic ORM object, or raise 404/400."""
    try:
        tid = uuid.UUID(topic_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{topic_id}' is not a valid topic ID.",
        )
    topic = db.query(Topic).options(joinedload(Topic.module)).filter(Topic.id == tid).first()
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_id}' not found.",
        )
    return topic


def _get_course_or_404(db: Session, course_id: str) -> Course:
    """Parse course_id UUID and return the Course ORM object, or raise 404/400."""
    try:
        cid = uuid.UUID(course_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{course_id}' is not a valid course ID.",
        )
    course = (
        db.query(Course)
        .options(
            joinedload(Course.modules).joinedload(Module.topics)
        )
        .filter(Course.id == cid)
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_id}' not found.",
        )
    return course


def _content_to_response(content: Content, topic_id: uuid.UUID) -> TopicContentResponse:
    """Convert a Content ORM row to TopicContentResponse."""
    try:
        body = json.loads(content.body) if content.body else {}
    except json.JSONDecodeError:
        body = {}

    key_concepts = [
        KeyConcept(term=kc.get("term", ""), definition=kc.get("definition", ""))
        for kc in (body.get("key_concepts") or [])
        if isinstance(kc, dict)
    ]
    examples = [
        ContentExample(title=ex.get("title", ""), content=ex.get("content", ""))
        for ex in (body.get("examples") or [])
        if isinstance(ex, dict)
    ]
    further_reading = body.get("further_reading") or []
    if isinstance(further_reading, str):
        further_reading = [further_reading]

    return TopicContentResponse(
        topic_id=topic_id,
        title=content.title,
        objectives=body.get("objectives") or [],
        explanation=body.get("explanation") or "",
        key_concepts=key_concepts,
        examples=examples,
        summary=body.get("summary") or "",
        further_reading=further_reading,
        generated_at=content.created_at,
    )


def _quiz_to_response(quiz: Quiz, topic_id: uuid.UUID) -> QuizResponse:
    """Convert a Quiz ORM row (with eager-loaded questions) to QuizResponse."""
    questions_out = []
    for q in sorted(quiz.questions, key=lambda x: x.id):
        raw_options = q.options or []
        if isinstance(raw_options, str):
            try:
                raw_options = json.loads(raw_options)
            except json.JSONDecodeError:
                raw_options = []
        options = [
            QuizOption(id=str(opt.get("id", i)), text=opt.get("text", ""))
            for i, opt in enumerate(raw_options)
            if isinstance(opt, dict)
        ]
        # correct_answer stored as the string index, e.g. "2"
        try:
            correct_index = int(q.correct_answer or 0)
        except (ValueError, TypeError):
            correct_index = 0

        questions_out.append(
            QuizQuestion(
                id=str(q.id),
                text=q.question_text,
                options=options,
                correct_index=correct_index,
                explanation=q.explanation or "",
            )
        )
    return QuizResponse(
        id=quiz.id,
        topic_id=topic_id,
        title=quiz.title,
        questions=questions_out,
        generated_at=quiz.created_at,
    )


def _build_modules_summary(course: Course) -> str:
    """Build a compact text summary of all modules/topics for the revision prompt."""
    lines = []
    for mod in sorted(course.modules, key=lambda m: m.order_no):
        lines.append(f"Module: {mod.title}")
        for topic in sorted(mod.topics, key=lambda t: t.order_no):
            lines.append(f"  - {topic.title}: {topic.description or ''}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/topics/{topic_id}/generate-content
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/api/topics/{topic_id}/generate-content",
    response_model=TopicContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate learning content for a topic",
    responses={
        400: {"description": "Invalid topic ID."},
        404: {"description": "Topic not found."},
        422: {"description": "AI returned an invalid response."},
        502: {"description": "AI service unavailable."},
    },
)
def generate_topic_content(
    topic_id: str,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
) -> TopicContentResponse:
    """
    1. Resolve topic → get course title for context.
    2. Call DeepSeek to generate structured learning content.
    3. Persist or replace a Content row for this topic.
    4. Return the content.
    """
    topic = _get_topic_or_404(db, topic_id)

    # Walk up the hierarchy to find course title
    course = db.query(Course).filter(Course.id == topic.module.course_id).first()
    course_title = course.title if course else "Unknown Course"

    try:
        content_data, model_used = ds.generate_topic_content(
            topic_title=topic.title,
            topic_description=topic.description or "",
            course_title=course_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        logger.error("DeepSeek content generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # Delete any existing content for this topic before re-inserting
    db.query(Content).filter(Content.topic_id == topic.id).delete()
    db.flush()

    content_row = Content(
        id=uuid.uuid4(),
        topic_id=topic.id,
        content_type="lecture",
        title=content_data.get("title") or topic.title,
        body=json.dumps(content_data),
        model_name=model_used,
    )
    db.add(content_row)
    db.flush()

    logger.info("Generated content for topic '%s' (model=%s)", topic.title, model_used)
    return _content_to_response(content_row, topic.id)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/topics/{topic_id}/content
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/topics/{topic_id}/content",
    response_model=TopicContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get existing topic content",
    responses={
        404: {"description": "Topic or content not found."},
        400: {"description": "Invalid topic ID."},
    },
)
def get_topic_content(
    topic_id: str,
    db: Session = Depends(get_db),
) -> TopicContentResponse:
    """Return the most recently generated content for a topic."""
    topic = _get_topic_or_404(db, topic_id)
    content = (
        db.query(Content)
        .filter(Content.topic_id == topic.id)
        .order_by(Content.created_at.desc())
        .first()
    )
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No content found for topic '{topic_id}'. Generate it first.",
        )
    return _content_to_response(content, topic.id)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/topics/{topic_id}/generate-quiz
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/api/topics/{topic_id}/generate-quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a quiz for a topic",
    responses={
        400: {"description": "Invalid topic ID."},
        404: {"description": "Topic not found."},
        422: {"description": "AI returned an invalid response."},
        502: {"description": "AI service unavailable."},
    },
)
def generate_topic_quiz(
    topic_id: str,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
) -> QuizResponse:
    """
    1. Resolve topic.
    2. Call DeepSeek to generate a 5-question MCQ quiz.
    3. Persist or replace Quiz + Question rows.
    4. Return the quiz.
    """
    topic = _get_topic_or_404(db, topic_id)
    course = db.query(Course).filter(Course.id == topic.module.course_id).first()
    course_title = course.title if course else "Unknown Course"

    try:
        quiz_data, model_used = ds.generate_quiz(
            topic_title=topic.title,
            topic_description=topic.description or "",
            course_title=course_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        logger.error("DeepSeek quiz generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # Delete any existing quizzes for this topic
    existing_quizzes = db.query(Quiz).filter(Quiz.topic_id == topic.id).all()
    for eq in existing_quizzes:
        db.delete(eq)
    db.flush()

    quiz_row = Quiz(
        id=uuid.uuid4(),
        topic_id=topic.id,
        title=quiz_data.get("title") or f"Quiz: {topic.title}",
    )
    db.add(quiz_row)
    db.flush()

    raw_questions = quiz_data.get("questions") or []
    for q in raw_questions:
        if not isinstance(q, dict):
            continue
        raw_opts = q.get("options") or []
        try:
            correct_idx = int(q.get("correct_index", 0))
        except (ValueError, TypeError):
            correct_idx = 0

        question_row = Question(
            id=uuid.uuid4(),
            quiz_id=quiz_row.id,
            question_text=q.get("text") or q.get("question") or "",
            question_type="mcq",
            options=raw_opts,
            correct_answer=str(correct_idx),
            explanation=q.get("explanation") or "",
            marks=1,
        )
        db.add(question_row)

    db.flush()

    # Reload with questions
    quiz_with_qs = (
        db.query(Quiz)
        .options(joinedload(Quiz.questions))
        .filter(Quiz.id == quiz_row.id)
        .first()
    )
    logger.info("Generated quiz for topic '%s' (%d questions, model=%s)",
                topic.title, len(raw_questions), model_used)
    return _quiz_to_response(quiz_with_qs, topic.id)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/topics/{topic_id}/quiz
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/topics/{topic_id}/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Get existing quiz for a topic",
    responses={
        404: {"description": "Topic or quiz not found."},
        400: {"description": "Invalid topic ID."},
    },
)
def get_topic_quiz(
    topic_id: str,
    db: Session = Depends(get_db),
) -> QuizResponse:
    """Return the most recently generated quiz for a topic."""
    topic = _get_topic_or_404(db, topic_id)
    quiz = (
        db.query(Quiz)
        .options(joinedload(Quiz.questions))
        .filter(Quiz.topic_id == topic.id)
        .order_by(Quiz.created_at.desc())
        .first()
    )
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No quiz found for topic '{topic_id}'. Generate it first.",
        )
    return _quiz_to_response(quiz, topic.id)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/courses/{course_id}/generate-revision
# ─────────────────────────────────────────────────────────────────────────────

# Revision data is stored in a JSON Content row keyed with content_type="revision"
_REVISION_CONTENT_TYPE = "revision"


def _revision_content_to_response(content: Content, course_id: uuid.UUID) -> RevisionResponse:
    """Convert a Content ORM row (content_type=revision) to RevisionResponse."""
    try:
        body = json.loads(content.body) if content.body else {}
    except json.JSONDecodeError:
        body = {}

    def _to_rev_questions(raw_list) -> list[RevisionQuestion]:
        out = []
        if not isinstance(raw_list, list):
            return out
        for i, q in enumerate(raw_list):
            if not isinstance(q, dict):
                continue
            raw_opts = q.get("options") or []
            options = [
                QuizOption(id=str(opt.get("id", j)), text=opt.get("text", ""))
                for j, opt in enumerate(raw_opts)
                if isinstance(opt, dict)
            ]
            try:
                correct_index = int(q.get("correct_index", 0))
            except (ValueError, TypeError):
                correct_index = 0
            out.append(RevisionQuestion(
                id=q.get("id") or f"rq{i}",
                text=q.get("text") or q.get("question") or "",
                options=options,
                correct_index=correct_index,
                explanation=q.get("explanation") or "",
            ))
        return out

    return RevisionResponse(
        course_id=course_id,
        quick_notes=body.get("quick_notes") or [],
        key_takeaways=body.get("key_takeaways") or [],
        practice_questions=_to_rev_questions(body.get("practice_questions")),
        question_bank=_to_rev_questions(body.get("question_bank")),
        generated_at=content.created_at,
    )


@router.post(
    "/api/courses/{course_id}/generate-revision",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate revision materials for a course",
    responses={
        400: {"description": "Invalid course ID."},
        404: {"description": "Course not found."},
        422: {"description": "AI returned an invalid response."},
        502: {"description": "AI service unavailable."},
    },
)
def generate_course_revision(
    course_id: str,
    db: Session = Depends(get_db),
    ds: DeepSeekClient = Depends(get_deepseek_client),
) -> RevisionResponse:
    """
    Generate revision materials (quick notes, takeaways, question bank) for a whole course.
    Stores the result as a Content row with content_type='revision' under the first topic.
    Returns the RevisionResponse.
    """
    course = _get_course_or_404(db, course_id)
    modules_summary = _build_modules_summary(course)

    try:
        revision_data, model_used = ds.generate_revision(
            course_title=course.title,
            modules_summary=modules_summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        logger.error("DeepSeek revision generation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # Store revision as a special Content row at the course level.
    # We use a sentinel topic_id approach: store under the first topic found,
    # but use content_type="revision" to distinguish it. The revision endpoint
    # retrieves it by course_id via a join.
    # Find all topic IDs for this course for the lookup
    all_topic_ids = [
        t.id
        for m in course.modules
        for t in m.topics
    ]

    if not all_topic_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Course has no topics — cannot generate revision materials.",
        )

    # Delete existing revision rows for this course
    db.query(Content).filter(
        Content.topic_id.in_(all_topic_ids),
        Content.content_type == _REVISION_CONTENT_TYPE,
    ).delete(synchronize_session=False)
    db.flush()

    # Store revision data under the first topic (arbitrary anchor)
    revision_row = Content(
        id=uuid.uuid4(),
        topic_id=all_topic_ids[0],
        content_type=_REVISION_CONTENT_TYPE,
        title=f"Revision: {course.title}",
        body=json.dumps({**revision_data, "_course_id": str(course.id)}),
        model_name=model_used,
    )
    db.add(revision_row)
    db.flush()

    logger.info("Generated revision for course '%s' (model=%s)", course.title, model_used)
    cid = uuid.UUID(course_id)
    return _revision_content_to_response(revision_row, cid)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses/{course_id}/revision
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/courses/{course_id}/revision",
    response_model=RevisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get existing revision materials for a course",
    responses={
        404: {"description": "Course or revision not found."},
        400: {"description": "Invalid course ID."},
    },
)
def get_course_revision(
    course_id: str,
    db: Session = Depends(get_db),
) -> RevisionResponse:
    """Return the most recently generated revision materials for a course."""
    course = _get_course_or_404(db, course_id)

    all_topic_ids = [t.id for m in course.modules for t in m.topics]
    if not all_topic_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course has no topics.",
        )

    revision_content = (
        db.query(Content)
        .filter(
            Content.topic_id.in_(all_topic_ids),
            Content.content_type == _REVISION_CONTENT_TYPE,
        )
        .order_by(Content.created_at.desc())
        .first()
    )
    if revision_content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No revision found for course '{course_id}'. Generate it first.",
        )
    cid = uuid.UUID(course_id)
    return _revision_content_to_response(revision_content, cid)
