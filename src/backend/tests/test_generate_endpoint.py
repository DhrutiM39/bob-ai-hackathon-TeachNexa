"""
Tests for the DeepSeek service and the POST /api/v1/courses/generate endpoint.

Strategy:
  - DeepSeekClient tests: mock _get_client() so the API is never called.
  - Endpoint tests: use FastAPI's TestClient with the db and ds dependencies
    overridden so no live DB or AI service is required.

All tests are hermetic — no network or PostgreSQL connection needed.
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

# ── Ensure SQLite is used before any backend module is imported ───────────────
# conftest.py (for test_database.py) already sets this, but set it again
# here to be explicit — os.environ is global so it's already set.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from backend.app.config import Settings  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.services.deepseek_client import DeepSeekClient  # noqa: E402
from backend.database.models import Base  # noqa: E402
import backend.database.models  # noqa: E402, F401
from backend.database.session import get_db  # noqa: E402
from backend.app.services.deepseek_client import get_deepseek_client  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Dedicated SQLite engine for endpoint tests
# StaticPool + same_thread=False + a single connection shared across the
# module scope keeps the in-memory tables visible to all sessions.
# ─────────────────────────────────────────────────────────────────────────────
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # all sessions share the same underlying connection
)


@event.listens_for(_test_engine, "connect")
def _set_fk_pragma(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="module", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def db_session(_create_tables) -> Session:
    """Session that rolls back after each test."""
    session = _TestSession()
    yield session
    session.rollback()
    session.close()


def _fake_settings(**overrides) -> Settings:
    defaults = dict(
        deepseek_api_key="test-key",
        deepseek_model="deepseek-chat",
        database_url="sqlite://",
        app_env="development",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _insert_user(session: Session) -> str:
    """Insert a minimal User row and return its id string."""
    import uuid as _uuid
    from backend.database.models import User
    user = User(
        id=_uuid.uuid4(),
        name="Test User",
        email=f"test_{_uuid.uuid4().hex[:8]}@example.com",
        role="instructor",
    )
    session.add(user)
    session.flush()
    return str(user.id)


_VALID_MODULES_JSON = {
    "modules": [
        {
            "title": "Module 1 — Introduction",
            "description": "Overview of core concepts.",
            "topics": [
                {"title": "What is Python?", "description": "History and philosophy."},
                {"title": "Setting up the environment", "description": "Install Python and VS Code."},
            ],
        },
        {
            "title": "Module 2 — Data Types",
            "description": "Primitive and complex data types.",
            "topics": [
                {"title": "Integers and Floats", "description": "Numeric types."},
                {"title": "Strings", "description": "Text manipulation."},
            ],
        },
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# DeepSeekClient unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDeepSeekClient:
    def _client_with_mock(self, response_text: str) -> DeepSeekClient:
        """Build a DeepSeekClient whose OpenAI client is fully mocked."""
        client = DeepSeekClient(settings=_fake_settings())
        # Simulate openai.OpenAI().chat.completions.create() return value
        mock_message = MagicMock()
        mock_message.content = response_text
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai
        return client

    def test_generate_returns_modules_and_model_id(self):
        client = self._client_with_mock(json.dumps(_VALID_MODULES_JSON))
        modules, model_id = client.generate_course_structure("Week 1: Intro. Week 2: Data types.")
        assert len(modules) == 2
        assert modules[0]["title"] == "Module 1 — Introduction"
        assert len(modules[0]["topics"]) == 2
        assert model_id == "deepseek-chat"

    def test_markdown_fences_are_stripped(self):
        fenced = f"```json\n{json.dumps(_VALID_MODULES_JSON)}\n```"
        client = self._client_with_mock(fenced)
        modules, _ = client.generate_course_structure("Some syllabus content here.")
        assert len(modules) == 2

    def test_invalid_json_raises_value_error(self):
        client = self._client_with_mock("not json at all")
        with pytest.raises(ValueError, match="invalid JSON"):
            client.generate_course_structure("Some syllabus content here.")

    def test_missing_modules_key_raises_value_error(self):
        client = self._client_with_mock(json.dumps({"data": []}))
        with pytest.raises(ValueError, match="missing top-level 'modules'"):
            client.generate_course_structure("Some syllabus content here.")

    def test_empty_modules_list_raises_value_error(self):
        client = self._client_with_mock(json.dumps({"modules": []}))
        with pytest.raises(ValueError, match="non-empty list"):
            client.generate_course_structure("Some syllabus content here.")

    def test_module_missing_title_raises_value_error(self):
        bad = {"modules": [{"description": "No title here", "topics": []}]}
        client = self._client_with_mock(json.dumps(bad))
        with pytest.raises(ValueError, match="missing 'title'"):
            client.generate_course_structure("Some syllabus content here.")

    def test_sdk_exception_raises_runtime_error(self):
        client = DeepSeekClient(settings=_fake_settings())
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("network timeout")
        client._client = mock_openai
        with pytest.raises(RuntimeError, match="DeepSeek call failed"):
            client.generate_course_structure("Some syllabus content here.")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint integration tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateEndpoint:
    """
    Test POST /api/v1/courses/generate.

    db is overridden with a generator that yields the test session.
    ds is overridden with a pre-canned DeepSeekClient that needs no API key.
    """

    def _make_client(self, session: Session, ds: DeepSeekClient) -> TestClient:
        def _override_db():
            yield session

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_deepseek_client] = lambda: ds
        return TestClient(app, raise_server_exceptions=True)

    def _ds_ok(self) -> DeepSeekClient:
        ds = DeepSeekClient(settings=_fake_settings())
        mock_message = MagicMock()
        mock_message.content = json.dumps(_VALID_MODULES_JSON)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        ds._client = mock_openai
        return ds

    def teardown_method(self, _method):
        app.dependency_overrides.clear()

    def _insert_demo_user(self, session: Session) -> None:
        """Insert the demo user that the server now requires server-side."""
        from backend.database.models import User
        existing = session.query(User).filter(
            User.id == uuid.UUID("00000000-0000-0000-0000-000000000001")
        ).first()
        if existing:
            return
        session.add(User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Demo Professor",
            email="demo@coursegenie.ai",
            role="instructor",
        ))
        session.flush()

    def test_generate_returns_201_with_full_structure(self, db_session):
        self._insert_demo_user(db_session)
        client = self._make_client(db_session, self._ds_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Introduction to Python",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types and control flow. Week 3: Functions.",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "Introduction to Python"
        assert len(body["modules"]) == 2
        assert body["modules"][0]["title"] == "Module 1 — Introduction"
        assert len(body["modules"][0]["topics"]) == 2
        assert body["model_used"] == "deepseek-chat"
        assert "course_id" in body

    def test_generate_persists_to_database(self, db_session):
        from backend.database.models import Course, Module, Topic

        self._insert_demo_user(db_session)
        client = self._make_client(db_session, self._ds_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types and control flow. Week 3: Functions.",
            },
        )
        assert resp.status_code == 201, resp.text
        course_id = uuid.UUID(resp.json()["course_id"])

        course = db_session.query(Course).filter_by(id=course_id).first()
        assert course is not None
        assert course.title == "Python Course"

        modules = db_session.query(Module).filter_by(course_id=course_id).all()
        assert len(modules) == 2

        for mod in modules:
            topics = db_session.query(Topic).filter_by(module_id=mod.id).all()
            assert len(topics) == 2

    def test_generate_validates_short_syllabus(self, db_session):
        client = self._make_client(db_session, self._ds_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "too short",
            },
        )
        assert resp.status_code == 422

    def test_generate_validates_missing_title(self, db_session):
        client = self._make_client(db_session, self._ds_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions and control flow.",
            },
        )
        assert resp.status_code == 422

    def test_generate_returns_502_on_sdk_error(self, db_session):
        self._insert_demo_user(db_session)
        ds = DeepSeekClient(settings=_fake_settings())
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("network timeout")
        ds._client = mock_openai
        client = self._make_client(db_session, ds)
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions.",
            },
        )
        assert resp.status_code == 502

    def test_generate_returns_422_on_bad_model_json(self, db_session):
        self._insert_demo_user(db_session)
        ds = DeepSeekClient(settings=_fake_settings())
        mock_message = MagicMock()
        mock_message.content = "this is not json"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        ds._client = mock_openai
        client = self._make_client(db_session, ds)
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions.",
            },
        )
        assert resp.status_code == 422

    def test_health_endpoint(self, db_session):
        client = self._make_client(db_session, self._ds_ok())
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
