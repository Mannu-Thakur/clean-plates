"""Backup metadata model introduced with Phase 6 for worker recovery."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_col, uuid_pk


class BackupModel(Base):
    __tablename__ = "backups"

    id: Mapped[str] = uuid_pk()
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    backup_type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="creating", nullable=False, index=True)
    triggered_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = created_at_col()

    def __repr__(self) -> str:
        return f"<Backup {self.filename} {self.status}>"
