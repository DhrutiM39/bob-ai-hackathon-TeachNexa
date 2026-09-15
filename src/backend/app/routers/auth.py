"""
Authentication router — signup, login, current user.

POST /api/auth/signup  → create account + return JWT
POST /api/auth/login   → verify credentials + return JWT
GET  /api/auth/me      → return current user info (requires token)
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut
from backend.app.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database.models import User
from backend.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
    responses={
        409: {"description": "Email already registered."},
        422: {"description": "Validation error."},
    },
)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Register a new user and return a JWT access token."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    user = User(
        id=uuid.uuid4(),
        name=body.name.strip(),
        email=body.email,
        password_hash=hash_password(body.password),
        role="instructor",
    )
    db.add(user)
    db.flush()

    token = create_access_token(user.id)
    logger.info("New user registered: %s", user.email)
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in with email + password",
    responses={
        401: {"description": "Invalid credentials."},
    },
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Verify credentials and return a JWT access token."""
    user = db.query(User).filter(User.email == body.email).first()

    # Constant-time check: always run verify even if user not found
    _dummy_hash = "$2b$12$invalid.hash.for.timing.safety.onlyXXXXXXXXXXXXX"
    stored_hash = user.password_hash if (user and user.password_hash) else _dummy_hash
    ok = verify_password(body.password, stored_hash)

    if not user or not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id)
    logger.info("User logged in: %s", user.email)
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
    responses={401: {"description": "Not authenticated."}},
)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user's profile."""
    return UserOut.model_validate(current_user)
