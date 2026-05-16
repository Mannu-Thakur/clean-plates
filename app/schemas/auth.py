"""
Auth schemas — request/response models for authentication endpoints.

Ref: 05-schemas.md §1
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str  # min 8 chars validated in service


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID stored as string in SQLite
    email: str
    name: str
    role: str
    is_active: bool
    last_login: datetime | None = None


class LoginResponseSchema(BaseModel):
    tokens: TokenPairSchema
    user: UserSchema
