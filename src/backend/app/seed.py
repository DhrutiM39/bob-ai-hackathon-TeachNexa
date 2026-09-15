"""
Seed utility — ensures the demo user exists in the database.

The frontend hard-codes DEMO_OWNER_ID = '00000000-0000-0000-0000-000000000001'
as the course owner until real authentication is added.  This script
idempotently inserts that user so foreign-key constraints don't fail.

Usage:
    # From repo root, with DATABASE_URL in your environment:
    python -m backend.app.seed

    # Or from src/backend/:
    python -m app.seed

    # Or via the helper script:
    python src/backend/seed.py
"""

from __future__ import annotations

import logging
import os
import sys
import uuid

# Make sure src/ is importable when running directly
_src_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

logger = logging.getLogger(__name__)

# ── Demo owner ────────────────────────────────────────────────────────────────
DEMO_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_OWNER_EMAIL = "demo@coursegenie.ai"
DEMO_OWNER_NAME = "Demo Professor"
DEMO_OWNER_ROLE = "instructor"


def seed_demo_user(db) -> None:
    """
    Insert the demo user if it doesn't already exist.
    Safe to call multiple times (idempotent).
    """
    from backend.database.models import User

    existing = db.query(User).filter(User.id == DEMO_OWNER_ID).first()
    if existing:
        logger.info("Demo user already exists — skipping insert.")
        return

    # Also check by email to avoid the unique-email constraint
    existing_email = db.query(User).filter(User.email == DEMO_OWNER_EMAIL).first()
    if existing_email:
        logger.info("Email '%s' already exists — skipping insert.", DEMO_OWNER_EMAIL)
        return

    user = User(
        id=DEMO_OWNER_ID,
        name=DEMO_OWNER_NAME,
        email=DEMO_OWNER_EMAIL,
        role=DEMO_OWNER_ROLE,
    )
    db.add(user)
    db.commit()
    logger.info("Demo user created: id=%s email=%s", DEMO_OWNER_ID, DEMO_OWNER_EMAIL)


def run() -> None:
    """Entry point — loads .env, opens a DB session, seeds, closes."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    except ImportError:
        pass  # python-dotenv optional for this script

    from backend.database.session import SessionLocal
    db = SessionLocal()
    try:
        seed_demo_user(db)
        print("✓ Seed complete.")
    except Exception as exc:
        db.rollback()
        print(f"✗ Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run()
