"""
Saved analytics filter presets.

Ref: docs/plans/01-models.md section 18.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk


class FilterPresetModel(Base):
    __tablename__ = "filter_presets"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    filter_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    user = relationship("UserModel")

    def __repr__(self) -> str:
        return f"<FilterPreset user_id={self.user_id} name={self.name}>"
