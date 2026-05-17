"""Report generation and scheduling schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import PaginatedBase

REPORT_FORMATS = {"pdf", "csv", "excel", "xlsx"}
REPORT_FREQUENCIES = {"daily", "weekly", "monthly"}


class ReportConfigSchema(BaseModel):
    type: str = Field(min_length=1, max_length=30)
    format: str = Field(max_length=10)
    date_from: date | None = None
    date_to: date | None = None
    student_id: UUID | None = None
    filters: dict = Field(default_factory=dict)

    @field_validator("type", "format", mode="before")
    @classmethod
    def _clean_lower(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("format")
    @classmethod
    def _valid_format(cls, value: str) -> str:
        if value not in REPORT_FORMATS:
            raise ValueError("format must be pdf, csv, or excel")
        return "excel" if value == "xlsx" else value

    @model_validator(mode="after")
    def _valid_date_window(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        return self


class ReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    format: str
    status: str
    file_size: int | None = None
    generated_by: UUID
    generated_at: datetime | None = None
    created_at: datetime


class ScheduleCreateSchema(BaseModel):
    report_type: str = Field(min_length=1, max_length=30)
    format: str = Field(max_length=10)
    frequency: str = Field(max_length=20)
    day_of_week: str | None = Field(default=None, max_length=10)
    time_of_day: str = Field(pattern=r"^\d{2}:\d{2}$")
    email_recipients: list[str] = Field(default_factory=list)
    auto_email: bool = False
    active: bool = True

    @field_validator("report_type", "format", "frequency", "day_of_week", mode="before")
    @classmethod
    def _clean_lower(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("format")
    @classmethod
    def _valid_format(cls, value: str) -> str:
        if value not in REPORT_FORMATS:
            raise ValueError("format must be pdf, csv, or excel")
        return "excel" if value == "xlsx" else value

    @field_validator("frequency")
    @classmethod
    def _valid_frequency(cls, value: str) -> str:
        if value not in REPORT_FREQUENCIES:
            raise ValueError("frequency must be daily, weekly, or monthly")
        return value


class ReportScheduleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_type: str
    format: str
    frequency: str
    day_of_week: str | None = None
    time_of_day: str
    email_recipients: list[str]
    auto_email: bool
    active: bool
    last_run: datetime | None = None
    next_run: datetime | None = None


class ScheduleUpdateSchema(BaseModel):
    report_type: str | None = None
    format: str | None = None
    frequency: str | None = None
    day_of_week: str | None = None
    time_of_day: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    email_recipients: list[str] | None = None
    auto_email: bool | None = None
    active: bool | None = None

    @field_validator("report_type", "format", "frequency", "day_of_week", mode="before")
    @classmethod
    def _clean_lower(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("format")
    @classmethod
    def _valid_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in REPORT_FORMATS:
            raise ValueError("format must be pdf, csv, or excel")
        return "excel" if value == "xlsx" else value

    @field_validator("frequency")
    @classmethod
    def _valid_frequency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in REPORT_FREQUENCIES:
            raise ValueError("frequency must be daily, weekly, or monthly")
        return value


class PaginatedReports(PaginatedBase):
    items: list[ReportSchema]
