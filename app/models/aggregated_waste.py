"""
Precomputed waste aggregates used by the Phase 5 analytics engine.

Ref: docs/plans/01-models.md section 22.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _utcnow, uuid_pk


class AggregatedWasteModel(Base):
    __tablename__ = "aggregated_waste"
    __table_args__ = (
        UniqueConstraint(
            "period_type",
            "period_start",
            "scope_type",
            "scope_id",
            name="uq_aggregated_waste_period_scope",
        ),
    )

    id: Mapped[str] = uuid_pk()
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    total_waste_grams: Mapped[float] = mapped_column(Float, nullable=False)
    avg_waste_grams: Mapped[float] = mapped_column(Float, nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    student_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peak_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AggregatedWaste {self.period_type} {self.scope_type}:{self.scope_id}>"
