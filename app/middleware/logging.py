"""
Structured request/response logging middleware.

⚠ G2-fix: Implemented as a pure ASGI middleware (not BaseHTTPMiddleware) to
avoid breaking WebSocket connections. WebSocket scopes are passed through
without logging to reduce noise.

Ref: 04-middlewares.md §3
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("cleanplates.access")

# Paths to skip logging for (reduce noise)
_SKIP_PATHS = frozenset({"/health", "/metrics"})


class RequestLoggingMiddleware:
    """Pure ASGI middleware — logs HTTP requests and safely bypasses WebSockets."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Bypass non-HTTP scopes (WebSocket, lifespan)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Skip noisy health/metrics paths
        if path in _SKIP_PATHS or path.startswith("/ws"):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "?")
        start = time.perf_counter()
        status_code = 0

        async def _send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request",
                extra={
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
