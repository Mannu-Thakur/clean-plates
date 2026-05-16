"""
Waste entry and ML ingestion schemas.

Ref: docs/plans/05-schemas.md section 4.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedBase
from app.schemas.devices import HeartbeatSchema


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class FoodItemEntrySchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grams: float | None = Field(default=None, ge=0)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class WasteEntryCreateSchema(BaseModel):
    student_device_id: str = Field(min_length=1, max_length=100)
    device_serial: str = Field(min_length=1, max_length=100)
    weight_grams: float = Field(ge=0)
    meal_type: str | None = Field(default=None, max_length=20)
    food_items: list[FoodItemEntrySchema] = Field(default_factory=list)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    plate_image_path: str | None = Field(default=None, max_length=500)
    timestamp: datetime

    @field_validator("student_device_id", "device_serial", mode="before")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("meal_type", "plate_image_path", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class DetectionPayload(WasteEntryCreateSchema):
    """Alias schema used by the ML detection endpoint."""


class BulkWasteIngestSchema(BaseModel):
    entries: list[WasteEntryCreateSchema] = Field(min_length=1, max_length=1000)


class WasteEntrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    device_id: UUID
    weight_grams: float
    meal_type: str
    food_items: list[FoodItemEntrySchema]
    severity: str
    session_date: date
    timestamp: datetime
    student_name: str | None = None
    student_device_id: str


class WasteEntryDetailSchema(WasteEntrySchema):
    confidence_score: float | None = None
    plate_image_path: str | None = None
    rule_evaluated: bool


class PaginatedEntries(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[WasteEntrySchema]


class SessionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_name: str
    meal_type: str
    start_time: str
    end_time: str
    entry_count_today: int
    total_waste_today_grams: float
    is_active: bool


class SyncResultSchema(BaseModel):
    total_received: int
    inserted: int
    skipped: int
    errors: list[dict]


class HeartbeatPayload(HeartbeatSchema):
    """ML heartbeat payload; the authenticated API key supplies the device."""
