"""
Tests for course API endpoints.

Covers:
  GET  /api/courses                 → list, empty list, structure
  GET  /api/courses/{id}            → detail, 404, 400 (invalid UUID)
  POST /api/v1/courses/generate     → success (mocked DeepSeek), owner not found,
                                      DeepSeek error, invalid response

Uses the same StaticPool strategy as test_generate_endpoint.py so this module
is fully self-contained — it creates its own in-memory SQLite engine and overrides
the FastAPI `get_db` dependency so the TestClient uses that engine.

Run with:
    pytest src/backend/tests/ -v
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

# ── conftest.py already sets DATABASE_URL=sqlite:///:memory: before any import ──

from backend.app.main import app
from backend.database.models import Base, Course, Module, Topic, User
from backend.database.session import get_db
from backend.app.services.deepseek_client import get_deepseek_client

# ── Dedicated in-memory engine for this test module ──────────────────────────
# StaticPool: all sessions share the same underlying connection so in-memory
# tables created in the fixture are visible to the TestClient's sessions too.
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_fk_pragma(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)

# ── Constants ─────────────────────────────────────────────────────────────────
DEMO_OWNER_ID = "00000000-0000-0000-0000-000000000001"
GENERATE_ENDPOINT = "/api/v1/courses/generate"
LIST_ENDPOINT = "/api/courses"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _create_tables():
    """Create all tables once for this module, drop them at teardown."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def db(_create_tables) -> Session:
    """
    Provide a rolled-back session so each test starts with a clean state.
    The same session is injected into the TestClient via dependency override.
    """
    session = _TestSession()
    yield session
    session.rollback()
    session.close()


def _make_client(session: Session, mock_ds=None) -> TestClient:
    """Build a TestClient that injects *session* and an optional mock DS client."""
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
    """Reset dependency overrides after every test so they never bleed."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def demo_user(db) -> User:
    """Insert (or reuse) the demo owner row that generate tests require."""
    existing = db.query(User).filter(User.id == uuid.UUID(DEMO_OWNER_ID)).first()
    if existing:
        return existing
    user = User(
        id=uuid.UUID(DEMO_OWNER_ID),
        name="Demo Professor",
        email="demo@coursegenie.ai",
        role="instructor",
    )
    db.add(user)
    db.flush()
    return user


def _make_course(db: Session, owner: User, *, title="Test Course", n_modules=2, n_topics=3) -> Course:
    """Helper: insert a full Course → Modules → Topics hierarchy and return it."""
    course = Course(
        id=uuid.uuid4(),
        title=title,
        description=f"Description for {title}",
        syllabus_text="Week 1: Intro\nWeek 2: Advanced topics",
        owner_id=owner.id,
    )
    db.add(course)
    db.flush()

    for m_idx in range(1, n_modules + 1):
        module = Module(
            id=uuid.uuid4(),
            course_id=course.id,
            title=f"Module {m_idx}",
            description=f"Desc module {m_idx}",
            order_no=m_idx,
        )
        db.add(module)
        db.flush()

        for t_idx in range(1, n_topics + 1):
            topic = Topic(
                id=uuid.uuid4(),
                module_id=module.id,
                title=f"Topic {m_idx}.{t_idx}",
                description=f"Desc topic {m_idx}.{t_idx}",
                order_no=t_idx,
            )
            db.add(topic)
            db.flush()

    return course


def _mock_deepseek(raw_modules=None, model="deepseek-chat"):
    """Return a MagicMock DeepSeekClient whose generate_course_structure returns given data."""
    if raw_modules is None:
        raw_modules = [
            {
                "title": "Introduction",
                "description": "Basics of the course",
                "topics": [
                    {"title": "Overview", "description": "Course overview"},
                    {"title": "History",  "description": "Historical context"},
                ],
            },
            {
                "title": "Core Concepts",
                "description": "Deep dive",
                "topics": [
                    {"title": "Concept A", "description": "Explanation of A"},
                    {"title": "Concept B", "description": "Explanation of B"},
                ],
            },
        ]
    mock = MagicMock()
    mock.generate_course_structure.return_value = (raw_modules, model)
    return mock


VALID_GENERATE_BODY = {
    "title": "Introduction to Computer Science",
    "syllabus_text": (
        "Week 1: Variables and data types\n"
        "Week 2: Control flow — if/else, loops\n"
        "Week 3: Functions and modularity\n"
        "Week 4: Data structures — arrays, linked lists\n"
        "Week 5: Algorithms — sorting, searching\n"
        "Week 6: Object-oriented programming\n"
    ),
    # owner_id intentionally absent — backend assigns it server-side
}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses — empty state
# ─────────────────────────────────────────────────────────────────────────────

class TestListCoursesEmpty:
    def test_empty_returns_200(self, db):
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        assert response.status_code == 200

    def test_empty_response_structure(self, db):
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        body = response.json()
        assert "courses" in body
        assert "total" in body

    def test_empty_courses_list(self, db):
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        body = response.json()
        assert isinstance(body["courses"], list)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses — with data
# ─────────────────────────────────────────────────────────────────────────────

class TestListCoursesWithData:
    def test_returns_courses(self, db, demo_user):
        _make_course(db, demo_user, title="CS 101")
        _make_course(db, demo_user, title="CS 201")
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        assert response.status_code == 200
        body = response.json()
        titles = [c["title"] for c in body["courses"]]
        assert "CS 101" in titles
        assert "CS 201" in titles

    def test_total_matches_courses_length(self, db, demo_user):
        _make_course(db, demo_user, title="Math 101")
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        body = response.json()
        assert body["total"] == len(body["courses"])

    def test_course_item_has_required_fields(self, db, demo_user):
        _make_course(db, demo_user, title="Physics 101")
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        item = next(x for x in response.json()["courses"] if x["title"] == "Physics 101")
        required = {"id", "title", "status", "created_at", "updated_at",
                    "total_modules", "total_topics", "completed_topics"}
        for field in required:
            assert field in item, f"Missing field: {field}"

    def test_aggregate_counts_correct(self, db, demo_user):
        _make_course(db, demo_user, title="Bio 101", n_modules=2, n_topics=3)
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        item = next(x for x in response.json()["courses"] if x["title"] == "Bio 101")
        assert item["total_modules"] == 2
        assert item["total_topics"] == 6   # 2 modules × 3 topics each

    def test_status_is_ready(self, db, demo_user):
        _make_course(db, demo_user, title="Chem 101")
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        item = next(x for x in response.json()["courses"] if x["title"] == "Chem 101")
        assert item["status"] == "ready"

    def test_completed_topics_is_zero(self, db, demo_user):
        _make_course(db, demo_user, title="Hist 101")
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        item = next(x for x in response.json()["courses"] if x["title"] == "Hist 101")
        assert item["completed_topics"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses/{course_id} — success
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCourseDetail:
    def test_returns_200(self, db, demo_user):
        course = _make_course(db, demo_user, title="Detail Test")
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        assert response.status_code == 200

    def test_returns_correct_course(self, db, demo_user):
        course = _make_course(db, demo_user, title="Detail Check")
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        body = response.json()
        assert body["title"] == "Detail Check"
        assert str(body["id"]) == str(course.id)

    def test_includes_modules(self, db, demo_user):
        course = _make_course(db, demo_user, title="Modules Test", n_modules=3, n_topics=2)
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        body = response.json()
        assert "modules" in body
        assert len(body["modules"]) == 3

    def test_modules_include_topics(self, db, demo_user):
        course = _make_course(db, demo_user, title="Topics Test", n_modules=2, n_topics=4)
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        body = response.json()
        for mod in body["modules"]:
            assert "topics" in mod
            assert len(mod["topics"]) == 4

    def test_topic_has_required_fields(self, db, demo_user):
        course = _make_course(db, demo_user, title="Topic Fields")
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        topic = response.json()["modules"][0]["topics"][0]
        required = {"id", "title", "description", "order_no", "has_content", "has_quiz"}
        for field in required:
            assert field in topic, f"Missing topic field: {field}"

    def test_has_content_false_by_default(self, db, demo_user):
        course = _make_course(db, demo_user, title="No Content Yet")
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        topic = response.json()["modules"][0]["topics"][0]
        assert topic["has_content"] is False
        assert topic["has_quiz"] is False

    def test_syllabus_text_included(self, db, demo_user):
        course = _make_course(db, demo_user, title="Syllabus Check")
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        body = response.json()
        assert body["syllabus_text"] is not None

    def test_total_topics_count(self, db, demo_user):
        course = _make_course(db, demo_user, title="Count Test", n_modules=3, n_topics=2)
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/{course.id}")
        body = response.json()
        assert body["total_topics"] == 6  # 3 × 2


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses/{course_id} — error cases
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCourseErrors:
    def test_nonexistent_id_returns_404(self, db):
        c = _make_client(db)
        fake_id = str(uuid.uuid4())
        response = c.get(f"{LIST_ENDPOINT}/{fake_id}")
        assert response.status_code == 404

    def test_404_has_detail(self, db):
        c = _make_client(db)
        fake_id = str(uuid.uuid4())
        response = c.get(f"{LIST_ENDPOINT}/{fake_id}")
        assert "detail" in response.json()

    def test_invalid_uuid_returns_400(self, db):
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/not-a-uuid")
        assert response.status_code == 400

    def test_invalid_uuid_has_detail(self, db):
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/not-a-uuid")
        assert "detail" in response.json()

    def test_random_string_id_returns_400(self, db):
        c = _make_client(db)
        response = c.get(f"{LIST_ENDPOINT}/abc123xyz")
        assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/courses/generate — success
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateCourseSuccess:
    def test_returns_201(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        assert response.status_code == 201

    def test_response_has_course_id(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        body = response.json()
        assert "course_id" in body
        uuid.UUID(body["course_id"])  # must parse as valid UUID

    def test_response_has_modules(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        body = response.json()
        assert "modules" in body
        assert len(body["modules"]) == 2  # matches _mock_deepseek default

    def test_modules_have_topics(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        for mod in response.json()["modules"]:
            assert len(mod["topics"]) == 2

    def test_course_persisted_to_db(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        course_id = uuid.UUID(response.json()["course_id"])
        # Same session sees the committed data (StaticPool shares connection)
        course = db.query(Course).filter(Course.id == course_id).first()
        assert course is not None
        assert course.title == VALID_GENERATE_BODY["title"]

    def test_model_used_returned(self, db, demo_user):
        c = _make_client(db, _mock_deepseek(model="deepseek-chat"))
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        assert response.json()["model_used"] == "deepseek-chat"

    def test_syllabus_text_stored(self, db, demo_user):
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        body = response.json()
        assert body["syllabus_text"] == VALID_GENERATE_BODY["syllabus_text"].strip()


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/courses/generate — error cases
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateCourseErrors:
    def test_client_supplied_owner_id_is_ignored(self, db, demo_user):
        """owner_id in the request body must be silently ignored (extra fields)."""
        body = {**VALID_GENERATE_BODY, "owner_id": str(uuid.uuid4())}
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=body)
        # Extra fields are discarded by Pydantic — the request still succeeds
        # and the course is owned by the demo user, not the supplied UUID.
        assert response.status_code == 201

    def test_course_owner_is_always_demo_user(self, db, demo_user):
        """Even if a client somehow constructs a body with owner_id, it is ignored."""
        from backend.database.models import Course as CourseModel
        other_uuid = str(uuid.uuid4())
        body = {**VALID_GENERATE_BODY, "owner_id": other_uuid}
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=body)
        assert response.status_code == 201
        course_id = uuid.UUID(response.json()["course_id"])
        course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
        assert str(course.owner_id) == DEMO_OWNER_ID

    def test_missing_demo_user_returns_503(self, db):
        """If the demo user row is absent, generate must return 503."""
        # Explicitly delete the demo user to isolate this test from prior state
        db.query(User).filter(User.id == uuid.UUID(DEMO_OWNER_ID)).delete()
        db.flush()
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        assert response.status_code == 503
        assert "detail" in response.json()

    def test_deepseek_value_error_returns_422(self, db, demo_user):
        mock_ds = MagicMock()
        mock_ds.generate_course_structure.side_effect = ValueError("Invalid JSON from model")
        c = _make_client(db, mock_ds)
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        assert response.status_code == 422

    def test_deepseek_runtime_error_returns_502(self, db, demo_user):
        mock_ds = MagicMock()
        mock_ds.generate_course_structure.side_effect = RuntimeError("Connection refused")
        c = _make_client(db, mock_ds)
        response = c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)
        assert response.status_code == 502

    def test_missing_title_returns_422(self, db, demo_user):
        body = {k: v for k, v in VALID_GENERATE_BODY.items() if k != "title"}
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=body)
        assert response.status_code == 422

    def test_empty_title_returns_422(self, db, demo_user):
        body = {**VALID_GENERATE_BODY, "title": "ab"}  # min_length=3
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=body)
        assert response.status_code == 422

    def test_syllabus_too_short_returns_422(self, db, demo_user):
        body = {**VALID_GENERATE_BODY, "syllabus_text": "Too short"}
        c = _make_client(db, _mock_deepseek())
        response = c.post(GENERATE_ENDPOINT, json=body)
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/courses — demo owner isolation
# ─────────────────────────────────────────────────────────────────────────────

class TestListCoursesOwnerFilter:
    """GET /api/courses must return only courses owned by the demo user."""

    def test_courses_from_other_owner_not_returned(self, db, demo_user):
        """A course owned by a different user must not appear in the list."""
        other_user = User(
            id=uuid.uuid4(),
            name="Other Prof",
            email="other@example.com",
            role="instructor",
        )
        db.add(other_user)
        db.flush()

        _make_course(db, demo_user, title="My Course")
        _make_course(db, other_user, title="Their Course")

        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        assert response.status_code == 200
        titles = [item["title"] for item in response.json()["courses"]]
        assert "My Course" in titles
        assert "Their Course" not in titles

    def test_empty_when_no_demo_owner_courses(self, db):
        """If no courses exist for the demo user, the list must be empty."""
        # demo_user NOT inserted in this test — no fixture, no courses
        c = _make_client(db)
        response = c.get(LIST_ENDPOINT)
        assert response.status_code == 200
        assert response.json()["courses"] == []
        assert response.json()["total"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Transaction / rollback behaviour
# ─────────────────────────────────────────────────────────────────────────────

class TestTransactionBehaviour:
    def test_failed_deepseek_does_not_persist_course(self, db, demo_user):
        """When DeepSeek raises RuntimeError, no Course row must remain in the DB."""
        mock_ds = MagicMock()
        mock_ds.generate_course_structure.side_effect = RuntimeError("AI down")

        initial_count = db.query(Course).count()
        c = _make_client(db, mock_ds)
        c.post(GENERATE_ENDPOINT, json=VALID_GENERATE_BODY)

        # Same session (StaticPool) sees the final state after rollback
        final_count = db.query(Course).count()
        assert final_count == initial_count
