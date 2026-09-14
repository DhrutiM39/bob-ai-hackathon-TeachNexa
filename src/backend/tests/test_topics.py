"""
Tests for topic content / quiz / revision API endpoints.

Covers:
  POST /api/topics/{id}/generate-content  → 201, 404, 400, 422, 502
  GET  /api/topics/{id}/content           → 200, 404
  POST /api/topics/{id}/generate-quiz     → 201, 404, 422, 502
  GET  /api/topics/{id}/quiz              → 200, 404
  POST /api/courses/{id}/generate-revision → 201, 404, 422, 502
  GET  /api/courses/{id}/revision         → 200, 404

All AI calls are mocked — no network required.

Run with:
    pytest src/backend/tests/ -v
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app
from backend.database.models import Base, Content, Course, Module, Quiz, Question, Topic, User
from backend.database.session import get_db
from backend.app.services.deepseek_client import get_deepseek_client

# ── Dedicated StaticPool in-memory engine ────────────────────────────────────
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_fk_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)

# ── Constants ─────────────────────────────────────────────────────────────────
TOPIC_CONTENT_ENDPOINT = "/api/topics/{}/generate-content"
TOPIC_CONTENT_GET = "/api/topics/{}/content"
TOPIC_QUIZ_ENDPOINT = "/api/topics/{}/generate-quiz"
TOPIC_QUIZ_GET = "/api/topics/{}/quiz"
COURSE_REVISION_ENDPOINT = "/api/courses/{}/generate-revision"
COURSE_REVISION_GET = "/api/courses/{}/revision"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def db(_create_tables) -> Session:
    session = _TestSession()
    yield session
    session.rollback()
    session.close()


def _make_client(session: Session, mock_ds=None) -> TestClient:
    def _override_db():
        yield session

    app.dependency_overrides[get_db] = _override_db
    if mock_ds is not None:
        app.dependency_overrides[get_deepseek_client] = lambda: mock_ds
    else:
        app.dependency_overrides.pop(get_deepseek_client, None)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── DB setup helpers ──────────────────────────────────────────────────────────

def _make_hierarchy(db: Session, *, n_topics: int = 2) -> tuple[Course, Module, list[Topic]]:
    """Insert User → Course → Module → Topics and return them."""
    user = User(
        id=uuid.uuid4(),
        name="Prof Test",
        email=f"prof_{uuid.uuid4().hex[:6]}@test.com",
        role="instructor",
    )
    db.add(user)
    db.flush()

    course = Course(
        id=uuid.uuid4(),
        title="Test Course",
        description="A test course",
        syllabus_text="Week 1: Intro",
        owner_id=user.id,
    )
    db.add(course)
    db.flush()

    module = Module(
        id=uuid.uuid4(),
        course_id=course.id,
        title="Module 1",
        description="First module",
        order_no=1,
    )
    db.add(module)
    db.flush()

    topics = []
    for i in range(1, n_topics + 1):
        t = Topic(
            id=uuid.uuid4(),
            module_id=module.id,
            title=f"Topic {i}",
            description=f"Description for topic {i}",
            order_no=i,
        )
        db.add(t)
        db.flush()
        topics.append(t)

    return course, module, topics


# ── Mock DeepSeek helpers ─────────────────────────────────────────────────────

_MOCK_CONTENT_DATA = {
    "title": "History of Computing",
    "objectives": ["Understand key milestones", "Identify key contributors"],
    "explanation": "Computing began with Babbage...\n\nTuring defined computability...\n\nVon Neumann architecture became standard.",
    "key_concepts": [
        {"term": "Turing Machine", "definition": "A theoretical computational model."},
        {"term": "Von Neumann Architecture", "definition": "CPU + memory + stored programs."},
    ],
    "examples": [
        {"title": "ENIAC (1945)", "content": "First general-purpose electronic computer."},
    ],
    "summary": "Computing history spans from mechanical to electronic.",
    "further_reading": ["The Dream Machine by M. Mitchell Waldrop"],
}

_MOCK_QUIZ_DATA = {
    "title": "Quiz: History of Computing",
    "questions": [
        {
            "id": "q1",
            "text": "Who designed the Analytical Engine?",
            "options": [
                {"id": "0", "text": "Alan Turing"},
                {"id": "1", "text": "Charles Babbage"},
                {"id": "2", "text": "John Von Neumann"},
                {"id": "3", "text": "Ada Lovelace"},
            ],
            "correct_index": 1,
            "explanation": "Babbage designed the Analytical Engine.",
        },
        {
            "id": "q2",
            "text": "What is the Von Neumann architecture?",
            "options": [
                {"id": "0", "text": "Parallel processing"},
                {"id": "1", "text": "Stored programs in memory"},
                {"id": "2", "text": "Binary arithmetic"},
                {"id": "3", "text": "Vacuum tubes"},
            ],
            "correct_index": 1,
            "explanation": "Stored-program concept is the key insight.",
        },
    ],
}

_MOCK_REVISION_DATA = {
    "quick_notes": ["Babbage invented Analytical Engine", "Turing defined computability"],
    "key_takeaways": ["Computing is built on successive abstractions"],
    "practice_questions": [
        {
            "id": "pq1",
            "text": "What does Von Neumann architecture mean?",
            "options": [
                {"id": "0", "text": "Parallel CPUs"},
                {"id": "1", "text": "Stored programs"},
                {"id": "2", "text": "Vacuum tubes"},
                {"id": "3", "text": "Punch cards"},
            ],
            "correct_index": 1,
            "explanation": "Stored-program concept.",
        }
    ],
    "question_bank": [
        {
            "id": "bq1",
            "text": "Which device preceded the transistor?",
            "options": [
                {"id": "0", "text": "Punch cards"},
                {"id": "1", "text": "Relays"},
                {"id": "2", "text": "Vacuum tubes"},
                {"id": "3", "text": "Microchips"},
            ],
            "correct_index": 2,
            "explanation": "Vacuum tubes came before transistors.",
        }
    ],
}


def _mock_ds_content(data=None, model="deepseek-chat"):
    mock = MagicMock()
    mock.generate_topic_content.return_value = (data or _MOCK_CONTENT_DATA, model)
    return mock


def _mock_ds_quiz(data=None, model="deepseek-chat"):
    mock = MagicMock()
    mock.generate_quiz.return_value = (data or _MOCK_QUIZ_DATA, model)
    return mock


def _mock_ds_revision(data=None, model="deepseek-chat"):
    mock = MagicMock()
    mock.generate_revision.return_value = (data or _MOCK_REVISION_DATA, model)
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/topics/{id}/generate-content
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateTopicContent:
    def test_returns_201(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_content())
        response = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id))
        assert response.status_code == 201

    def test_response_has_explanation(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_content())
        body = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id)).json()
        assert "explanation" in body
        assert len(body["explanation"]) > 0

    def test_response_has_objectives(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_content())
        body = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id)).json()
        assert isinstance(body["objectives"], list)
        assert len(body["objectives"]) > 0

    def test_response_has_key_concepts(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_content())
        body = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id)).json()
        assert isinstance(body["key_concepts"], list)

    def test_content_persisted_to_db(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_content())
        c.post(TOPIC_CONTENT_ENDPOINT.format(tid))
        content = db.query(Content).filter(Content.topic_id == tid).first()
        assert content is not None

    def test_nonexistent_topic_returns_404(self, db):
        c = _make_client(db, _mock_ds_content())
        response = c.post(TOPIC_CONTENT_ENDPOINT.format(uuid.uuid4()))
        assert response.status_code == 404

    def test_invalid_topic_id_returns_400(self, db):
        c = _make_client(db, _mock_ds_content())
        response = c.post(TOPIC_CONTENT_ENDPOINT.format("not-a-uuid"))
        assert response.status_code == 400

    def test_deepseek_value_error_returns_422(self, db):
        _, _, topics = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_topic_content.side_effect = ValueError("Bad JSON")
        c = _make_client(db, mock_ds)
        response = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id))
        assert response.status_code == 422

    def test_deepseek_runtime_error_returns_502(self, db):
        _, _, topics = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_topic_content.side_effect = RuntimeError("AI down")
        c = _make_client(db, mock_ds)
        response = c.post(TOPIC_CONTENT_ENDPOINT.format(topics[0].id))
        assert response.status_code == 502

    def test_regeneration_replaces_old_content(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_content())
        c.post(TOPIC_CONTENT_ENDPOINT.format(tid))
        c.post(TOPIC_CONTENT_ENDPOINT.format(tid))  # re-generate
        count = db.query(Content).filter(
            Content.topic_id == tid,
            Content.content_type == "lecture",
        ).count()
        assert count == 1  # old one replaced


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/topics/{id}/content
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTopicContent:
    def test_returns_200_after_generation(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_content())
        c.post(TOPIC_CONTENT_ENDPOINT.format(tid))
        response = c.get(TOPIC_CONTENT_GET.format(tid))
        assert response.status_code == 200

    def test_content_matches_generated(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_content())
        c.post(TOPIC_CONTENT_ENDPOINT.format(tid))
        body = c.get(TOPIC_CONTENT_GET.format(tid)).json()
        assert "explanation" in body

    def test_no_content_returns_404(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db)
        response = c.get(TOPIC_CONTENT_GET.format(topics[0].id))
        assert response.status_code == 404

    def test_nonexistent_topic_returns_404(self, db):
        c = _make_client(db)
        response = c.get(TOPIC_CONTENT_GET.format(uuid.uuid4()))
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/topics/{id}/generate-quiz
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateTopicQuiz:
    def test_returns_201(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_quiz())
        response = c.post(TOPIC_QUIZ_ENDPOINT.format(topics[0].id))
        assert response.status_code == 201

    def test_response_has_questions(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_quiz())
        body = c.post(TOPIC_QUIZ_ENDPOINT.format(topics[0].id)).json()
        assert "questions" in body
        assert len(body["questions"]) == 2  # from _MOCK_QUIZ_DATA

    def test_question_has_required_fields(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_quiz())
        body = c.post(TOPIC_QUIZ_ENDPOINT.format(topics[0].id)).json()
        q = body["questions"][0]
        for field in ("id", "text", "options", "correct_index", "explanation"):
            assert field in q, f"Missing field: {field}"

    def test_quiz_persisted_to_db(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_quiz())
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))
        quiz = db.query(Quiz).filter(Quiz.topic_id == tid).first()
        assert quiz is not None

    def test_questions_persisted_to_db(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_quiz())
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))
        quiz = db.query(Quiz).filter(Quiz.topic_id == tid).first()
        questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
        assert len(questions) == 2

    def test_nonexistent_topic_returns_404(self, db):
        c = _make_client(db, _mock_ds_quiz())
        response = c.post(TOPIC_QUIZ_ENDPOINT.format(uuid.uuid4()))
        assert response.status_code == 404

    def test_deepseek_value_error_returns_422(self, db):
        _, _, topics = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_quiz.side_effect = ValueError("Bad response")
        c = _make_client(db, mock_ds)
        response = c.post(TOPIC_QUIZ_ENDPOINT.format(topics[0].id))
        assert response.status_code == 422

    def test_deepseek_runtime_error_returns_502(self, db):
        _, _, topics = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_quiz.side_effect = RuntimeError("Connection failed")
        c = _make_client(db, mock_ds)
        response = c.post(TOPIC_QUIZ_ENDPOINT.format(topics[0].id))
        assert response.status_code == 502

    def test_regeneration_replaces_old_quiz(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_quiz())
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))  # re-generate
        count = db.query(Quiz).filter(Quiz.topic_id == tid).count()
        assert count == 1


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/topics/{id}/quiz
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTopicQuiz:
    def test_returns_200_after_generation(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_quiz())
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))
        response = c.get(TOPIC_QUIZ_GET.format(tid))
        assert response.status_code == 200

    def test_quiz_has_questions(self, db):
        _, _, topics = _make_hierarchy(db)
        tid = topics[0].id
        c = _make_client(db, _mock_ds_quiz())
        c.post(TOPIC_QUIZ_ENDPOINT.format(tid))
        body = c.get(TOPIC_QUIZ_GET.format(tid)).json()
        assert len(body["questions"]) == 2

    def test_no_quiz_returns_404(self, db):
        _, _, topics = _make_hierarchy(db)
        c = _make_client(db)
        response = c.get(TOPIC_QUIZ_GET.format(topics[0].id))
        assert response.status_code == 404

    def test_nonexistent_topic_returns_404(self, db):
        c = _make_client(db)
        response = c.get(TOPIC_QUIZ_GET.format(uuid.uuid4()))
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/courses/{id}/generate-revision
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateCourseRevision:
    def test_returns_201(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_revision())
        response = c.post(COURSE_REVISION_ENDPOINT.format(course.id))
        assert response.status_code == 201

    def test_response_has_quick_notes(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_revision())
        body = c.post(COURSE_REVISION_ENDPOINT.format(course.id)).json()
        assert isinstance(body["quick_notes"], list)
        assert len(body["quick_notes"]) > 0

    def test_response_has_key_takeaways(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_revision())
        body = c.post(COURSE_REVISION_ENDPOINT.format(course.id)).json()
        assert isinstance(body["key_takeaways"], list)

    def test_response_has_question_bank(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_revision())
        body = c.post(COURSE_REVISION_ENDPOINT.format(course.id)).json()
        assert isinstance(body["question_bank"], list)

    def test_response_has_practice_questions(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db, _mock_ds_revision())
        body = c.post(COURSE_REVISION_ENDPOINT.format(course.id)).json()
        assert isinstance(body["practice_questions"], list)

    def test_revision_persisted_to_db(self, db):
        course, _, topics = _make_hierarchy(db)
        topic_ids = [t.id for t in topics]
        c = _make_client(db, _mock_ds_revision())
        c.post(COURSE_REVISION_ENDPOINT.format(course.id))
        content = db.query(Content).filter(
            Content.topic_id.in_(topic_ids),
            Content.content_type == "revision",
        ).first()
        assert content is not None

    def test_nonexistent_course_returns_404(self, db):
        c = _make_client(db, _mock_ds_revision())
        response = c.post(COURSE_REVISION_ENDPOINT.format(uuid.uuid4()))
        assert response.status_code == 404

    def test_deepseek_value_error_returns_422(self, db):
        course, _, _ = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_revision.side_effect = ValueError("Bad response")
        c = _make_client(db, mock_ds)
        response = c.post(COURSE_REVISION_ENDPOINT.format(course.id))
        assert response.status_code == 422

    def test_deepseek_runtime_error_returns_502(self, db):
        course, _, _ = _make_hierarchy(db)
        mock_ds = MagicMock()
        mock_ds.generate_revision.side_effect = RuntimeError("API down")
        c = _make_client(db, mock_ds)
        response = c.post(COURSE_REVISION_ENDPOINT.format(course.id))
        assert response.status_code == 502


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses/{id}/revision
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCourseRevision:
    def test_returns_200_after_generation(self, db):
        course, _, _ = _make_hierarchy(db)
        cid = course.id
        c = _make_client(db, _mock_ds_revision())
        c.post(COURSE_REVISION_ENDPOINT.format(cid))
        response = c.get(COURSE_REVISION_GET.format(cid))
        assert response.status_code == 200

    def test_revision_has_quick_notes(self, db):
        course, _, _ = _make_hierarchy(db)
        cid = course.id
        c = _make_client(db, _mock_ds_revision())
        c.post(COURSE_REVISION_ENDPOINT.format(cid))
        body = c.get(COURSE_REVISION_GET.format(cid)).json()
        assert len(body["quick_notes"]) > 0

    def test_no_revision_returns_404(self, db):
        course, _, _ = _make_hierarchy(db)
        c = _make_client(db)
        response = c.get(COURSE_REVISION_GET.format(course.id))
        assert response.status_code == 404

    def test_nonexistent_course_returns_404(self, db):
        c = _make_client(db)
        response = c.get(COURSE_REVISION_GET.format(uuid.uuid4()))
        assert response.status_code == 404

    def test_invalid_course_id_returns_400(self, db):
        c = _make_client(db)
        response = c.get(COURSE_REVISION_GET.format("not-a-uuid"))
        assert response.status_code == 400
