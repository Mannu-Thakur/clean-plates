"""Filter preset schemas for analytics saved views."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FilterPresetCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    filter_state: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class FilterPresetUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    filter_state: dict[str, Any] | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class FilterPresetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    filter_state: dict[str, Any]
    created_at: datetime
