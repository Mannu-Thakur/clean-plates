"""
Student schemas for card mapping and profile endpoints.

Ref: docs/plans/05-schemas.md section 3.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import PaginatedBase


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class MappingCreateSchema(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=150)
    roll_number: str = Field(min_length=1, max_length=50)
    branch: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1, le=4)
    hostel: str | None = Field(default=None, max_length=100)
    room_number: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    @field_validator("device_id", "name", "roll_number", "branch", mode="before")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("hostel", "room_number", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class MappingUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    roll_number: str | None = Field(default=None, min_length=1, max_length=50)
    branch: str | None = Field(default=None, min_length=1, max_length=50)
    year: int | None = Field(default=None, ge=1, le=4)
    hostel: str | None = Field(default=None, max_length=100)
    room_number: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    @field_validator("name", "roll_number", "branch", "hostel", "room_number", mode="before")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class StudentMappingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    device_id: str
    name: str
    roll_number: str
    branch: str
    year: int
    hostel: str | None = None
    room_number: str | None = None
    email: str | None = None
    mapped_by: UUID
    mapped_at: datetime


class StudentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str
    status: str
    is_status_manual: bool
    sustainability_score: float
    warning_count: int
    penalty_count: int
    avg_waste_grams: float
    is_active: bool
    mapping: StudentMappingSchema | None = None
    created_at: datetime


class StudentDetailSchema(StudentSchema):
    total_waste_grams: float


class StudentProfileUpdateSchema(BaseModel):
    is_active: bool | None = None


class PaginatedStudents(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[StudentSchema]


class ImportResultSchema(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: list[dict]
