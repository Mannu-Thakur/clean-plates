"""
Redis-backed rate limiter middleware.

Uses INCR + EXPIRE on ArqRedis (which subclasses redis.asyncio.Redis).
Implements per-route limits defined in 04-middlewares.md §5.

⚠ G2-fix: Pure ASGI middleware — bypasses WebSocket scopes.
"""

from __future__ import annotations

import logging

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("cleanplates.ratelimit")

# ── Route-specific limits ────────────────────────────────────────────────────
# (prefix, method) → (max_requests, window_seconds)
_ROUTE_LIMITS: list[tuple[str, str | None, int, int]] = [
    ("/api/v1/auth/login", "POST", 10, 60),
    ("/api/v1/auth/forgot-password", "POST", 5, 300),
    ("/api/v1/reports/generate", "POST", 5, 300),
    ("/api/v1/ml/upload-image", "POST", 10000, 60),
    ("/api/v1/ml/", None, 1000, 60),  # all ML routes
]
_DEFAULT_LIMIT = (200, 60)  # 200 req / 60s for general API


class RateLimitMiddleware:
    """Pure ASGI rate-limit middleware backed by Redis INCR/EXPIRE."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        method: str = scope.get("method", "GET")

        # Only rate-limit /api/v1 paths
        if not path.startswith("/api/v1"):
            await self.app(scope, receive, send)
            return

        # Resolve the Redis pool from app.state (set in lifespan)
        app = scope.get("app")
        redis = getattr(getattr(app, "state", None), "arq_pool", None) if app else None

        if redis is None:
            # No Redis available — let request through (dev fallback)
            await self.app(scope, receive, send)
            return

        # Determine rate limit for this route
        max_requests, window = _DEFAULT_LIMIT
        for route_prefix, route_method, limit, win in _ROUTE_LIMITS:
            if path.startswith(route_prefix):
                if route_method is None or route_method == method:
                    max_requests, window = limit, win
                    break

        # Build rate-limit key
        request = Request(scope)
        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{client_ip}:{path}"

        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window)

            if current > max_requests:
                ttl = await redis.ttl(key)
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": str(max(ttl, 1))},
                )
                await response(scope, receive, send)
                return
        except Exception:
            # Redis error — fail open to avoid blocking requests
            logger.warning("Rate limiter Redis error — allowing request through")

        await self.app(scope, receive, send)
