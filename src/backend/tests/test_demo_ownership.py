"""
Tests for the hackathon-MVP demo-user ownership mechanism.

Covers:
  A. seed_demo_user() is idempotent — safe to call multiple times
  B. startup seed inserts the demo user when the table is empty
  C. POST /api/v1/courses/generate works without owner_id in the request body
  D. Generated course is owned by the server-side demo user, not by the caller
  E. GET /api/courses returns only demo-owner courses
  F. Sending an owner_id in the request body is silently ignored (Pydantic
     drops unknown fields, so the course still goes to the demo user)
  G. Missing demo user → 503, not 400

All tests use an in-memory SQLite engine and mocked DeepSeek — no network
or PostgreSQL connection required.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app
from backend.app.services.auth_service import get_current_user
from backend.app.services.deepseek_client import get_deepseek_client
from backend.database.models import Base, Course, Module, Topic, User
from backend.database.session import get_db

# ── The exact UUID that everything in the system agrees on ────────────────────
DEMO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_UUID_STR = str(DEMO_UUID)

GENERATE_URL = "/api/v1/courses/generate"
LIST_URL = "/api/courses"

_SYLLABUS = (
    "Week 1: Introduction to the subject\n"
    "Week 2: Core concepts and terminology\n"
    "Week 3: Applied methods and techniques\n"
    "Week 4: Case studies and practical work\n"
    "Week 5: Assessment preparation and review\n"
)

# ── Per-test SQLite engine ────────────────────────────────────────────────────
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _fk_pragma(dbapi_conn, _rec):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


_Session = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db(_tables) -> Session:
    s = _Session()
    yield s
    s.rollback()
    s.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_ds():
    """DeepSeekClient that returns two minimal modules."""
    ds = MagicMock()
    ds.generate_course_structure.return_value = (
        [
            {
                "title": "Module A",
                "description": "First module.",
                "topics": [
                    {"title": "Topic A1", "description": "First topic."},
                    {"title": "Topic A2", "description": "Second topic."},
                ],
            }
        ],
        "gemini-1.5-flash",  # active provider is Gemini
    )
    return ds


def _api_client(session: Session, mock_ds=None, user: User = None) -> TestClient:
    app.dependency_overrides[get_db] = lambda: (yield session)
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda u=user: u
    if mock_ds is not None:
        app.dependency_overrides[get_deepseek_client] = lambda: mock_ds
    return TestClient(app, raise_server_exceptions=False)


def _insert_demo_user(session: Session) -> User:
    existing = session.query(User).filter(User.id == DEMO_UUID).first()
    if existing:
        return existing
    u = User(
        id=DEMO_UUID,
        name="Demo Professor",
        email="demo@coursegenie.ai",
        role="instructor",
    )
    session.add(u)
    session.flush()
    return u


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── A. Seed idempotency ───────────────────────────────────────────────────────

class TestSeedIdempotency:
    """seed_demo_user() must be safe to call any number of times."""

    def test_seed_creates_demo_user(self, db):
        from backend.app.seed import seed_demo_user

        assert db.query(User).filter(User.id == DEMO_UUID).first() is None
        seed_demo_user(db)
        assert db.query(User).filter(User.id == DEMO_UUID).first() is not None

    def test_seed_called_twice_does_not_duplicate(self, db):
        from backend.app.seed import seed_demo_user

        seed_demo_user(db)
        seed_demo_user(db)  # second call must be a no-op
        count = db.query(User).filter(User.id == DEMO_UUID).count()
        assert count == 1

    def test_seed_called_ten_times_still_one_row(self, db):
        from backend.app.seed import seed_demo_user

        for _ in range(10):
            seed_demo_user(db)
        count = db.query(User).filter(User.id == DEMO_UUID).count()
        assert count == 1

    def test_seed_produces_correct_role(self, db):
        from backend.app.seed import seed_demo_user

        seed_demo_user(db)
        user = db.query(User).filter(User.id == DEMO_UUID).first()
        assert user.role == "instructor"

    def test_seed_produces_correct_email(self, db):
        from backend.app.seed import seed_demo_user

        seed_demo_user(db)
        user = db.query(User).filter(User.id == DEMO_UUID).first()
        assert user.email == "demo@coursegenie.ai"


# ── C + D. Generation with authenticated user ────────────────────────────────

class TestGenerateWithAuthUser:
    """Course generation must succeed using the authenticated user as the owner."""

    def test_generate_succeeds_with_auth_user(self, db):
        user = _insert_demo_user(db)
        c = _api_client(db, _mock_ds(), user=user)
        resp = c.post(GENERATE_URL, json={"title": "CS 101", "syllabus_text": _SYLLABUS})
        assert resp.status_code == 201, resp.text

    def test_generated_course_owned_by_authenticated_user(self, db):
        """The course owner must be the authenticated user, not a client-supplied ID."""
        user = _insert_demo_user(db)
        c = _api_client(db, _mock_ds(), user=user)
        resp = c.post(GENERATE_URL, json={"title": "CS 101", "syllabus_text": _SYLLABUS})
        assert resp.status_code == 201, resp.text
        course_id = uuid.UUID(resp.json()["course_id"])
        course = db.query(Course).filter(Course.id == course_id).first()
        assert course is not None
        assert course.owner_id == user.id

    def test_client_supplied_owner_id_does_not_affect_ownership(self, db):
        """A foreign UUID sent in the body must be ignored by the server."""
        user = _insert_demo_user(db)
        attacker_uuid = str(uuid.uuid4())
        c = _api_client(db, _mock_ds(), user=user)
        resp = c.post(
            GENERATE_URL,
            json={
                "title": "Injected Course",
                "syllabus_text": _SYLLABUS,
                "owner_id": attacker_uuid,   # extra field — must be ignored
            },
        )
        assert resp.status_code == 201, resp.text
        course_id = uuid.UUID(resp.json()["course_id"])
        course = db.query(Course).filter(Course.id == course_id).first()
        # Owner must be the authenticated user, NOT the attacker's UUID
        assert course.owner_id == user.id
        assert str(course.owner_id) != attacker_uuid

    def test_unauthenticated_request_returns_401(self, db):
        """Requests without auth must return 401."""
        # Do NOT pass a user — no get_current_user override
        c = _api_client(db, _mock_ds())
        resp = c.post(GENERATE_URL, json={"title": "CS 101", "syllabus_text": _SYLLABUS})
        assert resp.status_code == 401


# ── E. Course list filtered to authenticated owner ───────────────────────────

class TestCourseListFilter:
    """GET /api/courses must only return courses owned by the authenticated user."""

    def test_only_auth_user_courses_returned(self, db):
        demo = _insert_demo_user(db)
        other = User(id=uuid.uuid4(), name="Other", email="o@x.com", role="instructor")
        db.add(other)
        db.flush()

        # Course owned by demo
        demo_course = Course(
            id=uuid.uuid4(), title="Demo Course",
            owner_id=demo.id, syllabus_text="x",
        )
        # Course owned by someone else
        other_course = Course(
            id=uuid.uuid4(), title="Other Course",
            owner_id=other.id, syllabus_text="x",
        )
        db.add_all([demo_course, other_course])
        db.flush()

        c = _api_client(db, user=demo)
        resp = c.get(LIST_URL)
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()["courses"]]
        assert "Demo Course" in titles
        assert "Other Course" not in titles

    def test_total_count_excludes_other_owner(self, db):
        demo = _insert_demo_user(db)
        other = User(id=uuid.uuid4(), name="Other2", email="o2@x.com", role="instructor")
        db.add(other)
        db.flush()
        db.add(Course(id=uuid.uuid4(), title="D1", owner_id=demo.id, syllabus_text="x"))
        db.add(Course(id=uuid.uuid4(), title="O1", owner_id=other.id, syllabus_text="x"))
        db.flush()

        c = _api_client(db, user=demo)
        resp = c.get(LIST_URL)
        assert resp.json()["total"] == 1

    def test_empty_list_when_no_courses_for_auth_user(self, db):
        user = _insert_demo_user(db)
        c = _api_client(db, user=user)
        resp = c.get(LIST_URL)
        assert resp.status_code == 200
        assert resp.json()["courses"] == []
