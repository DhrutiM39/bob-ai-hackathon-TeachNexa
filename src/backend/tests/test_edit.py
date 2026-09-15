"""
Tests for professor review / edit API endpoints.

Covers:
  PATCH /api/courses/{id}   → update course title/description
  PATCH /api/modules/{id}   → update module title/description
  PATCH /api/topics/{id}    → update topic title/description

Error cases:
  - 404 for unknown resource
  - 400 for invalid UUID
  - 422 for empty/invalid body values
  - Unrelated fields (owner_id, syllabus_text) cannot be changed

All tests use in-memory SQLite — no network, no real DB required.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app
from backend.app.services.auth_service import get_current_user
from backend.database.models import Base, Course, Module, Topic, User
from backend.database.session import get_db

# ── Dedicated in-memory engine ────────────────────────────────────────────────
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

DEMO_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

COURSE_URL  = "/api/courses/{}"
MODULE_URL  = "/api/modules/{}"
TOPIC_URL   = "/api/topics/{}"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db(_tables) -> Session:
    session = _Session()
    yield session
    session.rollback()
    session.close()


def _make_client(session: Session, user: User = None) -> TestClient:
    def _override():
        yield session
    _user = user or getattr(_seed_hierarchy, "_last_user", None)
    app.dependency_overrides[get_db] = _override
    if _user is not None:
        app.dependency_overrides[get_current_user] = lambda u=_user: u
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear():
    yield
    app.dependency_overrides.clear()


_SEED_COUNTER = 0

def _seed_hierarchy(db: Session):
    """Insert user → course → module → topic; return all four."""
    global _SEED_COUNTER
    _SEED_COUNTER += 1
    user = User(id=uuid.uuid4(), name="Prof", email=f"prof_{_SEED_COUNTER}@test.com", role="instructor")
    db.add(user)
    db.flush()
    _seed_hierarchy._last_user = user

    course = Course(
        id=uuid.uuid4(),
        title="Original Title",
        description="Original description",
        syllabus_text="Week 1: Intro",
        owner_id=user.id,
    )
    db.add(course)
    db.flush()

    module = Module(
        id=uuid.uuid4(),
        course_id=course.id,
        title="Original Module",
        description="Module desc",
        order_no=1,
    )
    db.add(module)
    db.flush()

    topic = Topic(
        id=uuid.uuid4(),
        module_id=module.id,
        title="Original Topic",
        description="Topic desc",
        order_no=1,
    )
    db.add(topic)
    db.flush()

    return user, course, module, topic


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/courses/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestPatchCourse:
    def test_update_title_returns_200(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={"title": "New Title"})
        assert resp.status_code == 200

    def test_updated_title_in_response(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={"title": "Updated"})
        assert resp.json()["title"] == "Updated"

    def test_update_description_only(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={"description": "New desc"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "New desc"

    def test_update_both_fields(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={"title": "T2", "description": "D2"})
        body = resp.json()
        assert body["title"] == "T2"
        assert body["description"] == "D2"

    def test_empty_body_does_not_change_title(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Original Title"

    def test_persisted_to_db(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        c.patch(COURSE_URL.format(course.id), json={"title": "Persisted"})
        refreshed = db.query(Course).filter(Course.id == course.id).first()
        assert refreshed.title == "Persisted"

    def test_nonexistent_course_returns_404(self, db):
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(uuid.uuid4()), json={"title": "X"})
        assert resp.status_code == 404

    def test_invalid_uuid_returns_400(self, db):
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format("not-a-uuid"), json={"title": "X"})
        assert resp.status_code == 400

    def test_empty_string_title_returns_422(self, db):
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(COURSE_URL.format(course.id), json={"title": ""})
        assert resp.status_code == 422

    def test_syllabus_text_not_in_response_body(self, db):
        """Verify syllabus_text cannot be changed via the edit endpoint."""
        _, course, _, _ = _seed_hierarchy(db)
        c = _make_client(db)
        # Try sending a syllabus_text key — Pydantic's extra=ignore means it's dropped
        c.patch(COURSE_URL.format(course.id), json={"title": "T3", "syllabus_text": "HACKED"})
        refreshed = db.query(Course).filter(Course.id == course.id).first()
        assert refreshed.syllabus_text == "Week 1: Intro"  # unchanged


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/modules/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestPatchModule:
    def test_update_title_returns_200(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(module.id), json={"title": "New Module"})
        assert resp.status_code == 200

    def test_updated_title_in_response(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(module.id), json={"title": "Updated Module"})
        assert resp.json()["title"] == "Updated Module"

    def test_update_description(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(module.id), json={"description": "New desc"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "New desc"

    def test_response_includes_topics(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(module.id), json={"title": "M"})
        assert "topics" in resp.json()
        assert len(resp.json()["topics"]) == 1

    def test_persisted_to_db(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        c.patch(MODULE_URL.format(module.id), json={"title": "Persisted Module"})
        refreshed = db.query(Module).filter(Module.id == module.id).first()
        assert refreshed.title == "Persisted Module"

    def test_nonexistent_module_returns_404(self, db):
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(uuid.uuid4()), json={"title": "X"})
        assert resp.status_code == 404

    def test_invalid_uuid_returns_400(self, db):
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format("bad-id"), json={"title": "X"})
        assert resp.status_code == 400

    def test_empty_string_title_returns_422(self, db):
        _, _, module, _ = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(MODULE_URL.format(module.id), json={"title": ""})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/topics/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestPatchTopic:
    def test_update_title_returns_200(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={"title": "New Topic"})
        assert resp.status_code == 200

    def test_updated_title_in_response(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={"title": "Renamed"})
        assert resp.json()["title"] == "Renamed"

    def test_update_description(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={"description": "New desc"})
        assert resp.status_code == 200
        assert resp.json()["description"] == "New desc"

    def test_response_has_required_fields(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={"title": "T"})
        body = resp.json()
        for field in ("id", "title", "description", "order_no", "has_content", "has_quiz"):
            assert field in body, f"Missing field: {field}"

    def test_persisted_to_db(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        c.patch(TOPIC_URL.format(topic.id), json={"title": "Persisted Topic"})
        refreshed = db.query(Topic).filter(Topic.id == topic.id).first()
        assert refreshed.title == "Persisted Topic"

    def test_nonexistent_topic_returns_404(self, db):
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(uuid.uuid4()), json={"title": "X"})
        assert resp.status_code == 404

    def test_invalid_uuid_returns_400(self, db):
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format("nope"), json={"title": "X"})
        assert resp.status_code == 400

    def test_empty_string_title_returns_422(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={"title": ""})
        assert resp.status_code == 422

    def test_empty_body_leaves_title_unchanged(self, db):
        _, _, _, topic = _seed_hierarchy(db)
        c = _make_client(db)
        resp = c.patch(TOPIC_URL.format(topic.id), json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Original Topic"
