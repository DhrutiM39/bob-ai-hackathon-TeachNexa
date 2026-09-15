"""
Authentication service for CourseGenie AI.

Provides:
  - Password hashing / verification (bcrypt via passlib)
  - JWT access token creation / verification (python-jose)
  - FastAPI dependency get_current_user()

Configuration (all via environment / Settings):
  SECRET_KEY   — random secret for signing JWTs (required in production)
  JWT_ALGORITHM — algorithm (default HS256)
  JWT_EXPIRE_MINUTES — token lifetime in minutes (default 10080 = 7 days)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.database.session import get_db

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------

def _jose():
    from jose import JWTError, jwt
    return jwt, JWTError


# ---------------------------------------------------------------------------
# Password helpers (using bcrypt directly — avoids passlib/bcrypt version conflicts)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt as _bcrypt
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _settings():
    return get_settings()


def create_access_token(user_id: uuid.UUID) -> str:
    s = _settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    jwt_mod, _ = _jose()
    return jwt_mod.encode(payload, s.secret_key, algorithm=s.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Return user_id str or None on any failure."""
    s = _settings()
    jwt_mod, JWTError = _jose()
    try:
        payload = jwt_mod.decode(token, s.secret_key, algorithms=[s.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# FastAPI dependency — require authenticated user
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """
    Extract the user from the Bearer token.
    Raises 401 if the token is missing, invalid, or the user no longer exists.
    """
    from backend.database.models import User

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user = db.query(User).filter(User.id == uid).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Like get_current_user but returns None instead of raising for unauthenticated requests."""
    from backend.database.models import User

    if not credentials:
        return None
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    return db.query(User).filter(User.id == uid).first()
