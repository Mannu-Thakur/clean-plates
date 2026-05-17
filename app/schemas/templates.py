"""Email template schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TemplateCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=30)
    subject: str = Field(min_length=1, max_length=300)
    body_html: str = Field(min_length=1)
    variables: list[str] = Field(default_factory=list)

    @field_validator("type", mode="before")
    @classmethod
    def _clean_type(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value


class TemplateUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    subject: str | None = Field(default=None, min_length=1, max_length=300)
    body_html: str | None = Field(default=None, min_length=1)
    variables: list[str] | None = None


class EmailTemplateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: str
    subject: str
    body_html: str
    variables: list[str]
    is_default: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class SampleDataSchema(BaseModel):
    variables: dict = Field(default_factory=dict)


class RenderedHtmlSchema(BaseModel):
    html: str
