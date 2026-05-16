"""
Rule engine schemas prepared in Phase 3 for Phase 4 route wiring.

Ref: docs/plans/05-schemas.md section 6.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import PaginatedBase


class ConditionSchema(BaseModel):
    field: str
    operator: str
    value: Any

    @field_validator("field", "operator", mode="before")
    @classmethod
    def _strip_condition_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class ConditionGroupSchema(BaseModel):
    logic: str = "AND"
    conditions: list[ConditionSchema] = Field(default_factory=list)

    @field_validator("logic")
    @classmethod
    def _valid_logic(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"AND", "OR"}:
            raise ValueError("logic must be AND or OR")
        return normalized


class TimeConstraintSchema(BaseModel):
    window: str | None = None
    lookback_days: int | None = Field(default=None, ge=1)


class ScopeSchema(BaseModel):
    target: str = "student"
    filters: dict[str, Any] = Field(default_factory=dict)


class ActionSchema(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type", mode="before")
    @classmethod
    def _strip_type(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


def _validate_actions(actions: list[ActionSchema] | None) -> list[ActionSchema] | None:
    if not actions:
        return actions
    allowed = {
        "generate_warning",
        "send_email",
        "increase_penalty",
        "trigger_escalation",
        "classify_student",
        "create_audit_log",
    }
    for action in actions:
        if action.type not in allowed:
            raise ValueError(f"unsupported action type: {action.type}")

        params = action.params or {}
        if action.type == "generate_warning" and ("level" not in params or "reason" not in params):
            raise ValueError("generate_warning requires level and reason")
        if action.type == "increase_penalty" and "points" not in params:
            raise ValueError("increase_penalty requires points")
        if action.type == "trigger_escalation" and ("escalated_to_role" not in params or "reason" not in params):
            raise ValueError("trigger_escalation requires escalated_to_role and reason")
        if action.type == "classify_student" and "status" not in params:
            raise ValueError("classify_student requires status")
        if action.type == "create_audit_log" and "summary" not in params:
            raise ValueError("create_audit_log requires summary")
        if action.type == "send_email" and not (
            params.get("template_id") or (params.get("subject") and params.get("body"))
        ):
            raise ValueError("send_email requires template_id or subject and body")

    classifications = {
        action.params.get("status")
        for action in actions
        if action.type == "classify_student" and action.params.get("status") is not None
    }
    if len(classifications) > 1:
        raise ValueError("actions cannot contain contradictory classify_student statuses")
    escalation_roles = {
        action.params.get("escalated_to_role")
        for action in actions
        if action.type == "trigger_escalation" and action.params.get("escalated_to_role") is not None
    }
    if len(escalation_roles) > 1:
        raise ValueError("actions cannot contain contradictory trigger_escalation roles")
    return actions


class RuleCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    type: str
    priority: str
    active: bool = True
    conditions: list[ConditionGroupSchema]
    time_constraints: TimeConstraintSchema | None = None
    scope: ScopeSchema = Field(default_factory=ScopeSchema)
    actions: list[ActionSchema]
    chain_to_rule_id: UUID | None = None

    @model_validator(mode="after")
    def _check_actions(self):
        _validate_actions(self.actions)
        return self

    @field_validator("type", "priority", mode="before")
    @classmethod
    def _strip_rule_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RuleUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: str | None = None
    active: bool | None = None
    conditions: list[ConditionGroupSchema] | None = None
    time_constraints: TimeConstraintSchema | None = None
    scope: ScopeSchema | None = None
    actions: list[ActionSchema] | None = None
    chain_to_rule_id: UUID | None = None

    @model_validator(mode="after")
    def _check_actions(self):
        _validate_actions(self.actions)
        return self

    @field_validator("priority", mode="before")
    @classmethod
    def _strip_priority(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RuleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    type: str
    priority: str
    active: bool
    conditions: list[ConditionGroupSchema]
    time_constraints: TimeConstraintSchema | None = None
    scope: ScopeSchema | None = None
    actions: list[ActionSchema]
    chain_to_rule_id: UUID | None = None
    execution_count: int
    last_triggered_at: datetime | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class TestPayloadSchema(BaseModel):
    waste_grams: float | None = None
    meal_type: str | None = None
    severity: str | None = None
    student_branch: str | None = None
    student_year: int | None = None
    frequency_count: int | None = None
    warning_count: int | None = None
    penalty_count: int | None = None
    sustainability_score: float | None = None


class TestResultSchema(BaseModel):
    rule_id: UUID
    matched: bool
    matched_conditions: list[dict[str, Any]]
    would_execute_actions: list[dict[str, Any]]
    reason: str


class SimulationResultSchema(BaseModel):
    rule_id: UUID
    period_from: date
    period_to: date
    total_events_evaluated: int
    matched_count: int
    projected_warnings: int
    projected_penalties: int
    projected_emails: int
    sample_matches: list[dict[str, Any]]


class RuleExecutionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    trigger_event_type: str
    student_id: UUID | None = None
    matched_conditions: list[dict[str, Any]] | dict[str, Any]
    executed_actions: list[dict[str, Any]] | dict[str, Any]
    result_status: str
    executed_at: datetime


class FieldOptionSchema(BaseModel):
    field: str
    label: str
    type: str
    operators: list[str]
    enum_values: list[str] | None = None


class ChainNodeSchema(BaseModel):
    id: UUID
    name: str
    type: str


class ChainEdgeSchema(BaseModel):
    from_rule_id: UUID
    to_rule_id: UUID


class ChainDataSchema(BaseModel):
    nodes: list[ChainNodeSchema]
    edges: list[ChainEdgeSchema]


class OperatorOptionSchema(BaseModel):
    operator: str
    label: str
    applies_to: list[str]


class ActionOptionSchema(BaseModel):
    type: str
    label: str
    required_params: list[str]
    optional_params: list[str]


class PaginatedRules(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[RuleSchema]


class PaginatedExecutions(PaginatedBase):
    model_config = ConfigDict(from_attributes=True)

    items: list[RuleExecutionSchema]
