"""Report metadata and schedule models for Phase 6."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_col, uuid_pk


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_created_at", "created_at"),)

    id: Mapped[str] = uuid_pk()
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    config: Mapped[dict | None] = mapped_column("config", JSON, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = created_at_col()

    def __repr__(self) -> str:
        return f"<Report {self.type}.{self.format} {self.status}>"


class ReportScheduleModel(Base):
    __tablename__ = "report_schedules"
    __table_args__ = (Index("ix_report_schedules_active_next_run", "active", "next_run"),)

    id: Mapped[str] = uuid_pk()
    report_type: Mapped[str] = mapped_column(String(30), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    day_of_week: Mapped[str | None] = mapped_column(String(10), nullable=True)
    time_of_day: Mapped[str] = mapped_column(String(5), nullable=False)
    email_recipients: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    auto_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = created_at_col()

    def __repr__(self) -> str:
        return f"<ReportSchedule {self.report_type} {self.frequency} active={self.active}>"
