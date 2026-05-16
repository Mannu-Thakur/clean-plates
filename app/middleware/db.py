"""
Database session dependency.

Yields an AsyncSession that auto-commits on success and rolls back on error.
This is the ONLY place ``get_db_session`` is defined — distinct from engine
setup in ``app/core/database.py``.

Ref: 04-middlewares.md §12
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a managed async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
