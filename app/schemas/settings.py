"""Settings schemas for user management, backup, and maintenance APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreateSchema(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    role: str
    password: str | None = None

    @field_validator("role", mode="before")
    @classmethod
    def _clean_role(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value


class UserUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = None
    email: EmailStr | None = None

    @field_validator("role", mode="before")
    @classmethod
    def _clean_role(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value


class BackupSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_size: int | None = None
    backup_type: str
    status: str
    triggered_by: str | None = None
    created_at: datetime
