"""Role management schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    permissions: dict
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleUpdateSchema(BaseModel):
    permissions: dict = Field(default_factory=dict)
    description: str | None = None
