"""
Security headers middleware.

⚠ G2-fix: Pure ASGI middleware — bypasses WebSocket scopes.

Ref: 04-middlewares.md §10
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class SecurityHeadersMiddleware:
    """Injects security response headers on every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Bypass WebSocket / lifespan scopes
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for name, value in _SECURITY_HEADERS.items():
                    headers.append((name.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, _send_wrapper)
