"""
Tests for the file-upload-to-course-generation flow.

These tests verify that text extracted from a syllabus file (TXT) is accepted by
POST /api/v1/courses/generate exactly the same way as manually typed text.

Background
----------
CreateCourse.jsx now calls extractSyllabusText(file) when syllabusText is empty,
then passes the result as `syllabus_text` in the JSON body.  From the backend's
perspective the content is indistinguishable from pasted text — both arrive as a
plain UTF-8 string.  These tests therefore cover:

  1. Text-only generation (baseline — existing behaviour)
  2. File-extracted text generation (same JSON contract; mimics what the frontend
     sends after extracting a .txt file via FileReader.readAsText())
  3. Both text + file: frontend uses text; backend sees only that text
  4. Empty syllabus_text: rejected by Pydantic before reaching the service
  5. Whitespace-only syllabus_text: rejected by Pydantic
  6. Syllabus below minimum length: rejected by Pydantic (min_length=50)

All tests are hermetic — no live database or DeepSeek API key required.
"""

from __future__ import annotations

import json
import os
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.app.main import app  # noqa: E402
from backend.app.config import Settings  # noqa: E402
from backend.app.services.auth_service import get_current_user  # noqa: E402
from backend.app.services.deepseek_client import DeepSeekClient, get_deepseek_client  # noqa: E402
from backend.database.models import Base, User  # noqa: E402
import backend.database.models  # noqa: E402, F401
from backend.database.session import get_db  # noqa: E402

# ── Shared in-memory SQLite ───────────────────────────────────────────────────

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
def db_session(_tables) -> Session:
    s = _Session()
    yield s
    s.rollback()
    s.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

_FAKE_MODULES = {
    "modules": [
        {
            "title": "Module 1 — Foundations",
            "description": "Core ideas.",
            "topics": [
                {"title": "Overview", "description": "Big picture."},
                {"title": "History", "description": "How it started."},
            ],
        }
    ]
}

# A realistic, long-enough syllabus string that mirrors what FileReader would
# produce when reading a plain-text .txt syllabus file.
_TXT_FILE_CONTENT = (
    "CS 101 Introduction to Computer Science\n"
    "Week 1: What is computing? History of computers.\n"
    "Week 2: Binary numbers, logic gates, and Boolean algebra.\n"
    "Week 3: Programming basics — variables, loops, conditionals.\n"
    "Week 4: Functions and modular design.\n"
    "Week 5: Data structures — arrays and linked lists.\n"
    "Week 6: Algorithms — sorting and searching.\n"
)

assert len(_TXT_FILE_CONTENT) >= 50, "test fixture must satisfy min_length=50"


def _fake_ds() -> DeepSeekClient:
    """DeepSeekClient whose SDK is fully mocked to return _FAKE_MODULES."""
    ds = DeepSeekClient(
        settings=Settings(
            gemini_api_key="test-gemini-key",
            gemini_model="gemini-1.5-flash",
            deepseek_api_key="test-key",
            deepseek_model="deepseek-chat",
            database_url="sqlite://",
            app_env="development",
        )
    )
    msg = MagicMock()
    msg.content = json.dumps(_FAKE_MODULES)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    mock_sdk = MagicMock()
    mock_sdk.chat.completions.create.return_value = resp
    ds._client = mock_sdk
    return ds


_DEMO_UUID = "00000000-0000-0000-0000-000000000001"


def _insert_demo_user(session: Session) -> User:
    import uuid as _uuid
    existing = session.query(User).filter(User.id == _uuid.UUID(_DEMO_UUID)).first()
    if existing:
        return existing
    user = User(
        id=_uuid.UUID(_DEMO_UUID),
        name="Demo Professor",
        email="demo@coursegenie.ai",
        role="instructor",
    )
    session.add(user)
    session.flush()
    return user


def _api_client(session: Session, user: User = None) -> TestClient:
    app.dependency_overrides[get_db] = lambda: (yield session)
    app.dependency_overrides[get_deepseek_client] = lambda: _fake_ds()
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda u=user: u
    return TestClient(app, raise_server_exceptions=True)


# ── Test class ────────────────────────────────────────────────────────────────

class TestFileUploadToGenerateFlow:
    """
    Covers all four combinations the frontend can send after the file-extraction fix.
    owner_id is no longer sent by the frontend; the backend assigns it server-side.
    """

    def teardown_method(self, _):
        app.dependency_overrides.clear()

    # ─── 1. Text-only (baseline) ──────────────────────────────────────────────

    def test_text_only_generation_returns_201(self, db_session):
        """Typed / pasted syllabus text reaches the backend and produces a course."""
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "CS 101",
                "syllabus_text": _TXT_FILE_CONTENT,
                # owner_id intentionally absent — backend assigns server-side
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "CS 101"
        assert len(body["modules"]) == 1
        assert "course_id" in body

    # ─── 2. File-extracted text (TXT content read via FileReader) ─────────────

    def test_file_extracted_text_generation_returns_201(self, db_session):
        """
        Simulates what happens after extractSyllabusText() resolves for a .txt file:
        the extracted string is sent as syllabus_text — indistinguishable from
        typed text from the backend's perspective.
        """
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "Introduction to CS",
                "syllabus_text": _TXT_FILE_CONTENT,
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["syllabus_text"] == _TXT_FILE_CONTENT.strip()

    def test_file_extracted_text_persisted_to_db(self, db_session):
        """Course row persisted when syllabus_text originates from file extraction."""
        from backend.database.models import Course

        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "File-sourced Course",
                "syllabus_text": _TXT_FILE_CONTENT,
            },
        )
        assert resp.status_code == 201, resp.text
        course_id = uuid.UUID(resp.json()["course_id"])
        course = db_session.query(Course).filter_by(id=course_id).first()
        assert course is not None
        assert course.title == "File-sourced Course"
        assert _TXT_FILE_CONTENT.strip() in course.syllabus_text

    # ─── 3. Both typed text and file — frontend sends only the typed text ─────

    def test_typed_text_takes_priority_over_file(self, db_session):
        """
        When syllabusText is non-empty, CreateCourse.jsx uses it directly.
        The backend never sees the file — it only ever sees a string.
        This test verifies that the typed text is what arrives.
        """
        typed_text = (
            "Typed syllabus: Module A covers algorithms. "
            "Module B covers data structures. Module C covers system design. "
            "Module D covers operating systems. Module E covers networking basics."
        )
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "Typed Course",
                "syllabus_text": typed_text,
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["syllabus_text"] == typed_text.strip()

    # ─── 4. Empty syllabus_text — caught by Pydantic before hitting the service ─

    def test_empty_syllabus_text_returns_422(self, db_session):
        """
        The frontend validate() prevents submission when both textarea and file are
        absent, but even if an empty string slips through, Pydantic rejects it.
        """
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "Empty Syllabus",
                "syllabus_text": "",
            },
        )
        assert resp.status_code == 422

    def test_whitespace_only_syllabus_returns_422(self, db_session):
        """
        Whitespace stripped by the Pydantic validator leaves an empty string,
        which triggers the min_length=50 check.
        """
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "Whitespace Course",
                "syllabus_text": "     ",
            },
        )
        assert resp.status_code == 422

    # ─── 5. Syllabus too short (mimics unsupported file producing empty string) ─

    def test_too_short_syllabus_returns_422(self, db_session):
        """
        If extraction somehow produced content shorter than 50 chars the
        backend Pydantic schema rejects it with 422 before calling DeepSeek.
        """
        user = _insert_demo_user(db_session)
        c = _api_client(db_session, user=user)
        resp = c.post(
            "/api/v1/courses/generate",
            json={
                "title": "Short Course",
                "syllabus_text": "Too short.",
            },
        )
        assert resp.status_code == 422
