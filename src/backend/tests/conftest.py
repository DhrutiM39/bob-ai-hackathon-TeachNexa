"""
Shared pytest fixtures for database tests.

Tests use an in-memory SQLite database so they run without a live PostgreSQL
server.  SQLite does not support every PostgreSQL feature (e.g. JSONB native
type, UUID native type), but SQLAlchemy maps these gracefully for testing:

  - UUID columns → CHAR(36)
  - JSONB columns → TEXT (stored as JSON string)
  - Foreign-key enforcement is enabled via PRAGMA foreign_keys = ON.

DATABASE_URL must be set to sqlite:///:memory: BEFORE backend modules are
imported, so this module sets it at the top.
"""

import os

# ── Set test DATABASE_URL before any backend module is imported ──────────────
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

from backend.database.connection import Base, engine  # noqa: E402
import backend.database.models  # noqa: E402, F401 — registers all ORM models


# ---------------------------------------------------------------------------
# Enable foreign-key enforcement on SQLite
# ---------------------------------------------------------------------------
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Session-scoped: create all tables once for the test run
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Per-test transactional rollback — keeps each test isolated
# ---------------------------------------------------------------------------
@pytest.fixture()
def db(create_tables) -> Session:
    """
    Provide a database session that is rolled back after each test.
    This keeps the database clean without recreating tables for every test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestSession()

    yield session

    session.close()
    try:
        transaction.rollback()
    except Exception:
        pass  # transaction may have already been rolled back by the DB on error
    connection.close()
