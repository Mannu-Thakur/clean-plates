"""
Student models for card-backed identities and admin mappings.

Ref: docs/plans/01-models.md sections 5 and 6.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk


class StudentModel(Base):
    __tablename__ = "students"

    id: Mapped[str] = uuid_pk()
    device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="green", nullable=False, index=True)
    is_status_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sustainability_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penalty_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_waste_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_waste_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    mapping = relationship(
        "StudentMappingModel",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student device_id={self.device_id} status={self.status}>"


class StudentMappingModel(Base):
    __tablename__ = "student_mappings"

    id: Mapped[str] = uuid_pk()
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), unique=True, nullable=False, index=True
    )
    device_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hostel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mapped_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    mapped_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    student = relationship("StudentModel", back_populates="mapping")

    def __repr__(self) -> str:
        return f"<StudentMapping student_id={self.student_id} roll={self.roll_number}>"
