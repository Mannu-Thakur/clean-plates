"""Audit log request/response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedBase


class AuditEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    action: str
    resource_type: str
    resource_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    user_role: str | None = None
    ip_address: str | None = None
    summary: str
    created_at: datetime


class AuditEventDetailSchema(AuditEventSchema):
    user_agent: str | None = None
    before_state: dict | None = None
    after_state: dict | None = None
    metadata: dict | None = Field(default=None, validation_alias="metadata_")


class AuditStatsSchema(BaseModel):
    total_today: int
    login_events: int
    config_changes: int
    rule_changes: int
    warning_events: int


class TimelineGroupSchema(BaseModel):
    user_id: str | None = None
    user_name: str
    date: date
    events: list[AuditEventSchema]


class TimelineDataSchema(BaseModel):
    groups: list[TimelineGroupSchema]


class PaginatedAuditEvents(PaginatedBase):
    items: list[AuditEventSchema]
