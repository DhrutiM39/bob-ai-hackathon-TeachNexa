"""
Tests for authentication endpoints.

Covers:
  POST /api/auth/signup  → 201 with token, 409 duplicate email, 422 validation
  POST /api/auth/login   → 200 with token, 401 wrong password, 401 unknown email
  GET  /api/auth/me      → 200 with user info, 401 without token
  JWT token round-trip — decode returns correct user_id
  Password hashing — stored hash is never the plain password
  Ownership protection — 401 without token on protected course endpoints

All tests use in-memory SQLite — no PostgreSQL required.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app
from backend.app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.database.models import Base, User
from backend.database.session import get_db

# ── Dedicated in-memory engine ────────────────────────────────────────────────
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _fk_pragma(dbapi_conn, _):
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
    session = _Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _client(session: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: (yield session)
    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────────────────────
# Password helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestPasswordHelpers:
    def test_hash_is_not_plaintext(self):
        h = hash_password("mysecret")
        assert h != "mysecret"
        assert len(h) > 20

    def test_verify_correct_password_returns_true(self):
        h = hash_password("correct")
        assert verify_password("correct", h) is True

    def test_verify_wrong_password_returns_false(self):
        h = hash_password("correct")
        assert verify_password("wrong", h) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses per-hash salts."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestJWTHelpers:
    def test_create_and_decode_round_trip(self):
        uid = uuid.uuid4()
        token = create_access_token(uid)
        decoded = decode_access_token(token)
        assert decoded == str(uid)

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.token") is None

    def test_empty_token_returns_none(self):
        assert decode_access_token("") is None


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/signup
# ─────────────────────────────────────────────────────────────────────────────

class TestSignup:
    def test_signup_returns_201_with_token(self, db):
        c = _client(db)
        resp = c.post("/api/auth/signup", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
        })
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["email"] == "alice@example.com"
        assert body["name"] == "Alice"
        assert body["role"] == "instructor"

    def test_signup_creates_user_in_db(self, db):
        c = _client(db)
        resp = c.post("/api/auth/signup", json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        uid = uuid.UUID(resp.json()["user_id"])
        user = db.query(User).filter(User.id == uid).first()
        assert user is not None
        assert user.email == "bob@example.com"

    def test_signup_stores_hashed_password_not_plaintext(self, db):
        c = _client(db)
        resp = c.post("/api/auth/signup", json={
            "name": "Carol",
            "email": "carol@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        uid = uuid.UUID(resp.json()["user_id"])
        user = db.query(User).filter(User.id == uid).first()
        assert user.password_hash != "secret123"
        assert verify_password("secret123", user.password_hash)

    def test_duplicate_email_returns_409(self, db):
        c = _client(db)
        payload = {"name": "Dave", "email": "dave@example.com", "password": "password123"}
        c.post("/api/auth/signup", json=payload)  # first signup
        resp = c.post("/api/auth/signup", json=payload)  # duplicate
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_short_password_returns_422(self, db):
        c = _client(db)
        resp = c.post("/api/auth/signup", json={
            "name": "Eve",
            "email": "eve@example.com",
            "password": "short",  # < 8 chars
        })
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, db):
        c = _client(db)
        resp = c.post("/api/auth/signup", json={
            "name": "Frank",
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/login
# ─────────────────────────────────────────────────────────────────────────────

class TestLogin:
    def _create_user(self, db, email="login@example.com", password="password123"):
        c = _client(db)
        c.post("/api/auth/signup", json={"name": "LoginUser", "email": email, "password": password})

    def test_login_returns_200_with_token(self, db):
        self._create_user(db, "login1@example.com")
        c = _client(db)
        resp = c.post("/api/auth/login", json={"email": "login1@example.com", "password": "password123"})
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()

    def test_login_wrong_password_returns_401(self, db):
        self._create_user(db, "login2@example.com")
        c = _client(db)
        resp = c.post("/api/auth/login", json={"email": "login2@example.com", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, db):
        c = _client(db)
        resp = c.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
        assert resp.status_code == 401

    def test_login_token_decodes_to_correct_user(self, db):
        self._create_user(db, "login3@example.com")
        c = _client(db)
        resp = c.post("/api/auth/login", json={"email": "login3@example.com", "password": "password123"})
        token = resp.json()["access_token"]
        user_id = decode_access_token(token)
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        assert user is not None
        assert user.email == "login3@example.com"


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/auth/me
# ─────────────────────────────────────────────────────────────────────────────

class TestGetMe:
    def test_me_returns_200_with_valid_token(self, db):
        c = _client(db)
        signup = c.post("/api/auth/signup", json={
            "name": "MeUser",
            "email": "me@example.com",
            "password": "password123",
        })
        token = signup.json()["access_token"]
        resp = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    def test_me_returns_401_without_token(self, db):
        c = _client(db)
        resp = c.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_returns_401_with_invalid_token(self, db):
        c = _client(db)
        resp = c.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Ownership protection — unauthenticated access to protected routes
# ─────────────────────────────────────────────────────────────────────────────

class TestOwnershipProtection:
    """Protected endpoints must return 401 when no Bearer token is provided."""

    def test_list_courses_requires_auth(self, db):
        c = _client(db)
        resp = c.get("/api/courses")
        assert resp.status_code == 401

    def test_get_course_requires_auth(self, db):
        c = _client(db)
        resp = c.get(f"/api/courses/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_generate_course_requires_auth(self, db):
        c = _client(db)
        resp = c.post("/api/v1/courses/generate", json={
            "title": "Test",
            "syllabus_text": "Week 1: Intro " * 10,
        })
        assert resp.status_code == 401
