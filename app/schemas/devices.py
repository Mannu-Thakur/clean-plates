"""
Device schemas for registration, status, and health endpoints.

Ref: docs/plans/05-schemas.md section 2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedBase


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class DeviceCreateSchema(BaseModel):
    device_serial: str = Field(min_length=1, max_length=100)
    edge_node_name: str = Field(min_length=1, max_length=100)
    institution_name: str = Field(min_length=1, max_length=200)
    institution_code: str = Field(min_length=1, max_length=50)
    campus_name: str = Field(min_length=1, max_length=100)
    mess_name: str = Field(min_length=1, max_length=100)
    mess_id: str = Field(min_length=1, max_length=50)
    hostel_name: str | None = Field(default=None, max_length=100)
    hostel_block: str | None = Field(default=None, max_length=50)
    floor_number: int | None = Field(default=None, ge=0)
    wing_section: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=0)
    meal_capacity_per_day: int | None = Field(default=None, ge=0)
    managed_by: str | None = Field(default=None, max_length=100)
    admin_contact: str | None = Field(default=None, max_length=200)

    @field_validator(
        "device_serial",
        "edge_node_name",
        "institution_name",
        "institution_code",
        "campus_name",
        "mess_name",
        "mess_id",
        mode="before",
    )
    @classmethod
    def _strip_required(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("hostel_name", "hostel_block", "wing_section", "managed_by", "admin_contact", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class DeviceUpdateSchema(BaseModel):
    edge_node_name: str | None = Field(default=None, min_length=1, max_length=100)
    mess_name: str | None = Field(default=None, min_length=1, max_length=100)
    hostel_name: str | None = Field(default=None, max_length=100)
    hostel_block: str | None = Field(default=None, max_length=50)
    floor_number: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, ge=0)

    @field_validator("edge_node_name", "mess_name", "hostel_name", "hostel_block", mode="before")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class DeviceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_serial: str
    edge_node_name: str
    institution_name: str
    mess_name: str
    hostel_name: str | None = None
    status: str
    ip_address: str | None = None
    firmware_version: str | None = None
    last_heartbeat: datetime | None = None
    last_sync: datetime | None = None
    active_since: datetime | None = None


class DeviceWithApiKeySchema(DeviceSchema):
    api_key: str


class HeartbeatSchema(BaseModel):
    cpu_percent: float = Field(ge=0, le=100)
    ram_percent: float = Field(ge=0, le=100)
    temperature: float | None = None
    storage_percent: float | None = Field(default=None, ge=0, le=100)
    connectivity: bool = True


class HealthDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: UUID
    cpu_percent: float
    ram_percent: float
    temperature: float | None = None
    storage_percent: float | None = None
    connectivity: bool
    recorded_at: datetime


class HealthHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: UUID
    period: str
    data: list[HealthDataSchema]


class QueuedSyncSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    pending_count: int
    device_id: UUID


class DeviceStatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    edge_node_name: str
    mess_name: str
    status: str
    cpu_percent: float | None = None
    ram_percent: float | None = None
    temperature: float | None = None
    last_heartbeat: datetime | None = None


class PaginatedDevices(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[DeviceSchema]
