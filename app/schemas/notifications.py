"""Notification request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedBase

NOTIFICATION_CHANNELS = {"email", "dashboard", "both"}
RECIPIENT_TYPES = {"individual", "branch", "hostel", "year", "all"}


def _strip(value: str) -> str:
    return value.strip()


class NotificationCreateSchema(BaseModel):
    type: str = Field(min_length=1, max_length=30)
    channel: str = Field(max_length=20)
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
    recipient_type: str = Field(max_length=20)
    recipient_ids: list[str] = Field(default_factory=list)
    template_id: UUID | None = None

    @field_validator("type", "channel", "recipient_type", mode="before")
    @classmethod
    def _clean_lower(cls, value: str) -> str:
        return _strip(value).lower() if isinstance(value, str) else value

    @field_validator("channel")
    @classmethod
    def _valid_channel(cls, value: str) -> str:
        if value not in NOTIFICATION_CHANNELS:
            raise ValueError("channel must be email, dashboard, or both")
        return value

    @field_validator("recipient_type")
    @classmethod
    def _valid_recipient_type(cls, value: str) -> str:
        if value not in RECIPIENT_TYPES:
            raise ValueError("recipient_type must be individual, branch, hostel, year, or all")
        return value

    @field_validator("subject", mode="before")
    @classmethod
    def _clean_subject(cls, value: str) -> str:
        return _strip(value) if isinstance(value, str) else value


class BroadcastSchema(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
    channel: str = Field(max_length=20)
    recipient_type: str = Field(max_length=20)
    recipient_filter: dict = Field(default_factory=dict)
    template_id: UUID | None = None

    @field_validator("channel", "recipient_type", mode="before")
    @classmethod
    def _clean_lower(cls, value: str) -> str:
        return _strip(value).lower() if isinstance(value, str) else value

    @field_validator("channel")
    @classmethod
    def _valid_channel(cls, value: str) -> str:
        if value not in NOTIFICATION_CHANNELS:
            raise ValueError("channel must be email, dashboard, or both")
        return value

    @field_validator("recipient_type")
    @classmethod
    def _valid_recipient_type(cls, value: str) -> str:
        if value not in {"branch", "hostel", "year", "all"}:
            raise ValueError("recipient_type must be branch, hostel, year, or all")
        return value


class ScheduleNotifSchema(NotificationCreateSchema):
    scheduled_at: datetime


class NotificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    channel: str
    subject: str
    status: str
    recipient_type: str
    is_read: bool
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime


class NotifStatsSchema(BaseModel):
    unread: int
    sent_today: int
    failed: int
    pending: int


class BroadcastResultSchema(BaseModel):
    total_recipients: int
    queued: int
    failed: int


class NotificationDetailSchema(NotificationSchema):
    body: str
    sender_id: UUID | None = None
    recipient_ids: list[str]
    template_id: UUID | None = None
    retry_count: int
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None


class DeliveryStatusItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipient_id: str
    recipient_email: str | None = None
    channel: str
    status: str
    delivered_at: datetime | None = None
    error: str | None = None


class DeliveryStatusSchema(BaseModel):
    notification_id: UUID
    total_recipients: int
    delivered: int
    failed: int
    pending: int
    deliveries: list[DeliveryStatusItemSchema]


class PaginatedNotifications(PaginatedBase):
    items: list[NotificationSchema]
