"""
Waste entry model for plate-detection events.

Ref: docs/plans/01-models.md section 8.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk


class WasteEntryModel(Base):
    __tablename__ = "waste_entries"
    __table_args__ = (
        UniqueConstraint("device_id", "timestamp", name="uq_waste_entries_device_timestamp"),
    )

    id: Mapped[str] = uuid_pk()
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    weight_grams: Mapped[float] = mapped_column(Float, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    food_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    plate_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    rule_evaluated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="ml", nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    student = relationship("StudentModel")
    device = relationship("DeviceModel")

    def __repr__(self) -> str:
        return f"<WasteEntry student_id={self.student_id} grams={self.weight_grams}>"
