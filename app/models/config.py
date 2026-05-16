"""
ConfigModel — system-wide key-value configuration store.

Ref: 01-models.md §19
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuid_pk, _utcnow


class ConfigModel(Base):
    __tablename__ = "system_config"
    __table_args__ = (
        UniqueConstraint("section", "key", name="uq_config_section_key"),
    )

    id: Mapped[str] = uuid_pk()
    section: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Config {self.section}.{self.key}>"
