"""
Warning, escalation, and penalty models.

Ref: docs/plans/01-models.md sections 9-11.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk


class WarningModel(Base):
    __tablename__ = "warnings"

    id: Mapped[str] = uuid_pk()
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rules.id"), nullable=True)
    waste_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("waste_entries.id"), nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    student = relationship("StudentModel")
    waste_entry = relationship("WasteEntryModel")
    escalations = relationship("EscalationModel", back_populates="warning")
    penalties = relationship("PenaltyModel", back_populates="warning")

    def __repr__(self) -> str:
        return f"<Warning student_id={self.student_id} level={self.level} status={self.status}>"


class EscalationModel(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = uuid_pk()
    warning_id: Mapped[str] = mapped_column(String(36), ForeignKey("warnings.id"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    escalated_to_role: Mapped[str] = mapped_column(String(50), nullable=False)
    escalated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = created_at_col()

    warning = relationship("WarningModel", back_populates="escalations")
    student = relationship("StudentModel")

    def __repr__(self) -> str:
        return f"<Escalation warning_id={self.warning_id} status={self.status}>"


class PenaltyModel(Base):
    __tablename__ = "penalties"

    id: Mapped[str] = uuid_pk()
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    warning_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("warnings.id"), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rules.id"), nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    revoked_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    student = relationship("StudentModel")
    warning = relationship("WarningModel", back_populates="penalties")

    def __repr__(self) -> str:
        return f"<Penalty student_id={self.student_id} points={self.points} status={self.status}>"
