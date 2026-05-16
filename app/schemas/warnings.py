"""
Warning, escalation, and penalty schemas.

Ref: docs/plans/05-schemas.md section 5.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedBase

WARNING_LEVELS = {"level_1", "level_2", "level_3"}
WARNING_STATUSES = {"active", "resolved", "escalated", "converted_to_penalty"}
ESCALATION_DECISIONS = {"approved", "rejected"}
PENALTY_STATUSES = {"active", "revoked"}


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class WarningCreateSchema(BaseModel):
    level: str = Field(max_length=20)
    reason: str = Field(min_length=1, max_length=500)
    send_email: bool = False
    rule_id: UUID | None = None
    waste_entry_id: UUID | None = None

    @field_validator("level")
    @classmethod
    def _valid_level(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in WARNING_LEVELS:
            raise ValueError("level must be one of level_1, level_2, level_3")
        return normalized

    @field_validator("reason", mode="before")
    @classmethod
    def _strip_reason(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class WarningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    level: str
    reason: str
    status: str
    rule_id: UUID | None = None
    issued_by: UUID | None = None
    email_sent: bool
    created_at: datetime
    student_name: str | None = None


class WarningSummarySchema(BaseModel):
    total_warnings: int
    active_warnings: int
    pending_escalations: int
    total_penalties: int


class ResolveWarningSchema(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=500)

    @field_validator("resolution_note", mode="before")
    @classmethod
    def _strip_note(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class EscalateWarningSchema(BaseModel):
    escalated_to_role: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("escalated_to_role", "reason", mode="before")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class EscalationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    warning_id: UUID
    student_id: UUID
    reason: str
    escalated_to_role: str
    escalated_by: UUID | None = None
    status: str
    reviewed_by: UUID | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


class ReviewEscalationSchema(BaseModel):
    decision: str = Field(max_length=20)
    review_note: str | None = Field(default=None, max_length=500)

    @field_validator("decision")
    @classmethod
    def _valid_decision(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ESCALATION_DECISIONS:
            raise ValueError("decision must be approved or rejected")
        return normalized

    @field_validator("review_note", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return _clean_optional_string(value)


class PenaltyCreateSchema(BaseModel):
    points: int = Field(ge=1, le=100)
    reason: str = Field(min_length=1, max_length=500)
    send_email: bool = False
    rule_id: UUID | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def _strip_reason(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class PenaltySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    points: int
    reason: str
    status: str
    warning_id: UUID | None = None
    issued_by: UUID | None = None
    email_sent: bool
    created_at: datetime
    student_name: str | None = None


class RevokePenaltySchema(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def _strip_reason(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class BulkResolveSchema(BaseModel):
    warning_ids: list[UUID] = Field(min_length=1, max_length=500)
    resolution_note: str = Field(min_length=1, max_length=500)


class StudentWarningsSchema(BaseModel):
    warnings: list[WarningSchema]
    penalties: list[PenaltySchema]


class PaginatedWarnings(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[WarningSchema]


class PaginatedPenalties(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[PenaltySchema]
