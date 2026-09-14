# database package — exposes the public API for the rest of the backend
from .connection import engine, Base
from .session import get_db, SessionLocal
from . import models  # noqa: F401 — ensure models are registered with Base

__all__ = [
    "engine",
    "Base",
    "get_db",
    "SessionLocal",
    "models",
]
