"""
SQLAlchemy session factory and FastAPI dependency.

Usage in a FastAPI route:

    from backend.database import get_db
    from sqlalchemy.orm import Session

    @router.get("/courses")
    def list_courses(db: Session = Depends(get_db)):
        return db.query(Course).all()
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .connection import engine

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a scoped session and always closes it
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session for the duration of a request.

    Typical FastAPI usage::

        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
