"""
Redis / ARQ connection pool.

The ArqRedis pool is created once in FastAPI's lifespan and stored on
``app.state.arq_pool``.  It doubles as a general Redis client (INCR/EXPIRE
for rate limiting) because ArqRedis subclasses redis.asyncio.Redis.

Ref: 06-phase-wise-plan.md Phase 1 & Phase 4 (C1-fix)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from arq.connections import ArqRedis, RedisSettings, create_pool
from fastapi import Request

from app.core.config import settings

if TYPE_CHECKING:
    pass


async def init_arq_pool() -> ArqRedis:
    """Create and return the shared ARQ Redis pool."""
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


def get_arq_pool(request: Request) -> ArqRedis:
    """FastAPI dependency — returns the lifespan-initialized ARQ pool.

    ARQ workers should use ``ctx['redis']`` instead.
    """
    return request.app.state.arq_pool
