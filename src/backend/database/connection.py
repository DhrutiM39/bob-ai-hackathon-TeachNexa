"""
Database connection setup.

Reads DATABASE_URL from the environment (set via .env → loaded by the app
entrypoint or by python-dotenv in development).  Creates the SQLAlchemy
engine and declarative Base that every model inherits from.
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/coursegenie",
)

# SQLite (used in tests) does not support pool_size / max_overflow.
_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs: dict = {
    "pool_pre_ping": not _is_sqlite,
    "echo": os.environ.get("APP_ENV", "production") == "development",
}
if not _is_sqlite:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# ---------------------------------------------------------------------------
# Declarative base — all ORM models inherit from this
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# Convenience helper to verify the connection is alive
# ---------------------------------------------------------------------------
def verify_connection() -> bool:
    """Return True if a SELECT 1 succeeds, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover
        print(f"[database] connection check failed: {exc}")
        return False
