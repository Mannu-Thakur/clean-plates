"""
Rule engine models created in Phase 3 so later warning/penalty FKs are stable.

Ref: docs/plans/01-models.md sections 12-13.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk


class RuleModel(Base):
    __tablename__ = "rules"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    time_constraints: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    chain_to_rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rules.id"), nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    chain_to_rule = relationship("RuleModel", remote_side=[id])

    def __repr__(self) -> str:
        return f"<Rule {self.name} type={self.type} active={self.active}>"


class RuleExecutionModel(Base):
    __tablename__ = "rule_executions"

    id: Mapped[str] = uuid_pk()
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("rules.id"), nullable=False, index=True)
    trigger_event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    student_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("students.id"), nullable=True, index=True)
    matched_conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    executed_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    rule = relationship("RuleModel")
    student = relationship("StudentModel")

    def __repr__(self) -> str:
        return f"<RuleExecution rule_id={self.rule_id} status={self.result_status}>"
