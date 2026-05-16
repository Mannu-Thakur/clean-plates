"""
SQLAlchemy declarative base with common mixins.

Every model inherits ``Base`` and uses the ``id``, ``created_at``, ``updated_at``
columns provided by the mixin columns below.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Naive UTC — required for SQLite datetime columns.

    SQLite stores datetimes as plain strings without timezone info.
    datetime.now(timezone.utc) produces aware datetimes that compare
    incorrectly against SQLite-read naive datetimes.
    """
    return datetime.utcnow()  # noqa: DTZ003


class Base(DeclarativeBase):
    """Shared declarative base for all CleanPlates models."""
    pass


# ── Common column factories ─────────────────────────────────────────────────
# Used as inline column definitions in each model to keep things explicit.

def uuid_pk() -> Mapped[str]:
    """UUID primary key stored as a 36-char string (SQLite has no native UUID)."""
    return mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


def created_at_col() -> Mapped[datetime]:
    return mapped_column(DateTime, default=_utcnow, nullable=False)


def updated_at_col() -> Mapped[datetime]:
    return mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
