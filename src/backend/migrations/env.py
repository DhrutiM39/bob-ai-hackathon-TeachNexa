"""
Alembic environment script.

Reads DATABASE_URL from the environment so the same .env used by the app
also drives migrations — no duplication of connection strings.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Make the backend package importable when running alembic from the repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Load .env so DATABASE_URL is available (no-op if already set in environment)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url with the value from the environment if present
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file's logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import all models so Alembic can detect schema changes (autogenerate)
# ---------------------------------------------------------------------------
from backend.database.connection import Base  # noqa: E402
import backend.database.models  # noqa: E402, F401 — registers all models

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (SQL script output)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
