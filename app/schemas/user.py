"""
Pydantic schemas for user and auth endpoints.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ------------- Auth schemas -------------
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only letters, digits, and underscores"
            )
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", v):
            raise ValueError(
                "Full name must contain only letters, spaces, and hyphens"
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh: str


class VerifyEmailRequest(BaseModel):
    token: uuid.UUID


class ProfileUpdateRequest(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=32)
    full_name: str | None = Field(None, min_length=2, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only letters, digits, and underscores"
            )
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", v):
            raise ValueError(
                "Full name must contain only letters, spaces, and hyphens"
            )
        return v


# --------------- Response schemas ---------------
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access: str
    refresh: str


class RegisterResponse(BaseModel):
    user: UserResponse
    verification_token: str
    message: str


class MessageResponse(BaseModel):
    message: str
