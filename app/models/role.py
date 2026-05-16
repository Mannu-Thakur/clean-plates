"""
RoleModel — role definitions with permission sets.

Ref: 01-models.md §23
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    def __repr__(self) -> str:
        return f"<Role {self.name} system={self.is_system}>"
