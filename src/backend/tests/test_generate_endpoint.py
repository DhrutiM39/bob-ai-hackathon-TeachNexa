"""
Tests for the watsonx.ai service and the POST /api/v1/courses/generate endpoint.

Strategy:
  - WatsonxClient tests: mock _get_model() so the IBM SDK is never needed.
  - Endpoint tests: use FastAPI's TestClient with the db and wx dependencies
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
from backend.app.services.watsonx_client import WatsonxClient  # noqa: E402
from backend.database.models import Base  # noqa: E402
import backend.database.models  # noqa: E402, F401
from backend.database.session import get_db  # noqa: E402
from backend.app.services.watsonx_client import get_watsonx_client  # noqa: E402


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
        watsonx_api_key="test-key",
        watsonx_project_id="test-project",
        watsonx_url="https://us-south.ml.cloud.ibm.com",
        watsonx_model_id="ibm/granite-13b-instruct-v2",
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
# WatsonxClient unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWatsonxClient:
    def _client_with_mock_model(self, response_text: str) -> WatsonxClient:
        client = WatsonxClient(settings=_fake_settings())
        mock_model = MagicMock()
        mock_model.generate_text.return_value = response_text
        client._model = mock_model
        return client

    def test_generate_returns_modules_and_model_id(self):
        client = self._client_with_mock_model(json.dumps(_VALID_MODULES_JSON))
        modules, model_id = client.generate_course_structure("Week 1: Intro. Week 2: Data types.")
        assert len(modules) == 2
        assert modules[0]["title"] == "Module 1 — Introduction"
        assert len(modules[0]["topics"]) == 2
        assert model_id == "ibm/granite-13b-instruct-v2"

    def test_markdown_fences_are_stripped(self):
        fenced = f"```json\n{json.dumps(_VALID_MODULES_JSON)}\n```"
        client = self._client_with_mock_model(fenced)
        modules, _ = client.generate_course_structure("Some syllabus content here.")
        assert len(modules) == 2

    def test_invalid_json_raises_value_error(self):
        client = self._client_with_mock_model("not json at all")
        with pytest.raises(ValueError, match="invalid JSON"):
            client.generate_course_structure("Some syllabus content here.")

    def test_missing_modules_key_raises_value_error(self):
        client = self._client_with_mock_model(json.dumps({"data": []}))
        with pytest.raises(ValueError, match="missing top-level 'modules'"):
            client.generate_course_structure("Some syllabus content here.")

    def test_empty_modules_list_raises_value_error(self):
        client = self._client_with_mock_model(json.dumps({"modules": []}))
        with pytest.raises(ValueError, match="non-empty list"):
            client.generate_course_structure("Some syllabus content here.")

    def test_module_missing_title_raises_value_error(self):
        bad = {"modules": [{"description": "No title here", "topics": []}]}
        client = self._client_with_mock_model(json.dumps(bad))
        with pytest.raises(ValueError, match="missing 'title'"):
            client.generate_course_structure("Some syllabus content here.")

    def test_sdk_exception_raises_runtime_error(self):
        client = WatsonxClient(settings=_fake_settings())
        mock_model = MagicMock()
        mock_model.generate_text.side_effect = Exception("network timeout")
        client._model = mock_model
        with pytest.raises(RuntimeError, match="watsonx.ai call failed"):
            client.generate_course_structure("Some syllabus content here.")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint integration tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateEndpoint:
    """
    Test POST /api/v1/courses/generate.

    db is overridden with a generator that yields the test session.
    wx is overridden with a pre-canned WatsonxClient that needs no SDK.
    """

    def _make_client(self, session: Session, wx: WatsonxClient) -> TestClient:
        def _override_db():
            yield session

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_watsonx_client] = lambda: wx
        return TestClient(app, raise_server_exceptions=True)

    def _wx_ok(self) -> WatsonxClient:
        wx = WatsonxClient(settings=_fake_settings())
        m = MagicMock()
        m.generate_text.return_value = json.dumps(_VALID_MODULES_JSON)
        wx._model = m
        return wx

    def teardown_method(self, _method):
        app.dependency_overrides.clear()

    def test_generate_returns_201_with_full_structure(self, db_session):
        owner_id = _insert_user(db_session)
        client = self._make_client(db_session, self._wx_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Introduction to Python",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types and control flow. Week 3: Functions.",
                "owner_id": owner_id,
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "Introduction to Python"
        assert len(body["modules"]) == 2
        assert body["modules"][0]["title"] == "Module 1 — Introduction"
        assert len(body["modules"][0]["topics"]) == 2
        assert body["model_used"] == "ibm/granite-13b-instruct-v2"
        assert "course_id" in body

    def test_generate_persists_to_database(self, db_session):
        from backend.database.models import Course, Module, Topic

        owner_id = _insert_user(db_session)
        client = self._make_client(db_session, self._wx_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types and control flow. Week 3: Functions.",
                "owner_id": owner_id,
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
        client = self._make_client(db_session, self._wx_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "too short",
                "owner_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 422

    def test_generate_validates_missing_title(self, db_session):
        client = self._make_client(db_session, self._wx_ok())
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions and control flow.",
                "owner_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 422

    def test_generate_returns_502_on_sdk_error(self, db_session):
        wx = WatsonxClient(settings=_fake_settings())
        m = MagicMock()
        m.generate_text.side_effect = Exception("network timeout")
        wx._model = m
        client = self._make_client(db_session, wx)
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions.",
                "owner_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 502

    def test_generate_returns_422_on_bad_model_json(self, db_session):
        wx = WatsonxClient(settings=_fake_settings())
        m = MagicMock()
        m.generate_text.return_value = "this is not json"
        wx._model = m
        client = self._make_client(db_session, wx)
        resp = client.post(
            "/api/v1/courses/generate",
            json={
                "title": "Python Course",
                "syllabus_text": "Week 1: Python basics. Week 2: Data types. Week 3: Functions.",
                "owner_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 422

    def test_health_endpoint(self, db_session):
        client = self._make_client(db_session, self._wx_ok())
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
