"""
Food catalog model used for waste entry tagging.

Ref: docs/plans/01-models.md section 7.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_col, uuid_pk


class FoodItemModel(Base):
    __tablename__ = "food_items"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    def __repr__(self) -> str:
        return f"<FoodItem {self.name} category={self.category}>"
