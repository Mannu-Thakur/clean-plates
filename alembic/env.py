"""
Alembic environment — async migration runner with SQLite batch mode.

Key safety measures:
  - ``render_as_batch=True``: enables SQLite batch migration mode to avoid
    ALTER TABLE crashes.
  - ``PRAGMA foreign_keys=OFF`` before migrations: prevents batch mode from
    failing when dropping/recreating tables with FK constraints.
  - Imports all models so autogenerate discovers every table.

Ref: 06-phase-wise-plan.md Phase 1 — Alembic
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Ensure DB directory exists
_db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)

# Import all models so Base.metadata is fully populated
from app.models import Base  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the app's setting
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL script."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite batch mode
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # SQLite batch mode
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    async with connectable.connect() as connection:
        # ⚠ FK Batch Bug fix: disable FKs during migration to prevent
        # batch mode from failing when recreating tables
        await connection.execute(text("PRAGMA foreign_keys=OFF"))

        await connection.run_sync(do_run_migrations)

        # Re-enable FKs after migration
        await connection.execute(text("PRAGMA foreign_keys=ON"))

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — delegates to async runner."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
