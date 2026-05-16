"""
Async SQLAlchemy engine + session factory.

Safety:
  - WAL mode: prevents OperationalError: database is locked under concurrent ARQ workers.
  - Foreign Keys ON: SQLite defaults to OFF, causing silent FK constraint violations.
  - check_same_thread=False: required for async drivers.
  - timeout=15: longer busy timeout for write contention.

Ref: 06-phase-wise-plan.md Phase 1, app/core/database.py
"""

from __future__ import annotations

import os

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Ensure the data directory exists for the SQLite file
_db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={
        "check_same_thread": False,
        "timeout": 15,
    },
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── SQLite PRAGMA hooks ──────────────────────────────────────────────────────
# These run on every new raw connection to ensure WAL and FK enforcement.
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):  # noqa: ARG001
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
