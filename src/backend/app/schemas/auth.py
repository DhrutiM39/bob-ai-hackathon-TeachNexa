"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

import uuid
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    name: str
    email: str
    role: str


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}
