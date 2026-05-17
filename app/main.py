"""
FastAPI application entry point.

- Lifespan: initializes ARQ Redis pool on startup, closes on shutdown.
- Middleware registration order per 04-middlewares.md § Middleware Registration Order.
- Static file serving for uploads.
- Router registration with /api/v1 prefix.

Ref: 06-phase-wise-plan.md Phase 1
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from contextlib import suppress

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.redis import init_arq_pool
from app.middleware.error_handler import register_error_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services import backup_service, ws_service

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("cleanplates")


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    # Startup — initialize ARQ Redis pool
    logger.info("Starting CleanPlates backend v%s", settings.APP_VERSION)
    try:
        app.state.arq_pool = await init_arq_pool()
        logger.info("ARQ Redis pool connected at %s", settings.REDIS_URL)
    except Exception as e:
        logger.warning("Could not connect to Redis: %s — rate limiting and background jobs will be unavailable", e)
        app.state.arq_pool = None

    app.state.ws_subscriber_task = asyncio.create_task(ws_service.subscriber_loop())
    logger.info("WebSocket Redis subscriber task started")
    app.state.restart_lock_task = asyncio.create_task(backup_service.watch_restart_lock())
    logger.info("Restart-lock watcher task started")

    yield

    restart_task = getattr(app.state, "restart_lock_task", None)
    if restart_task is not None:
        restart_task.cancel()
        with suppress(asyncio.CancelledError):
            await restart_task
        logger.info("Restart-lock watcher task stopped")

    ws_task = getattr(app.state, "ws_subscriber_task", None)
    if ws_task is not None:
        ws_task.cancel()
        with suppress(asyncio.CancelledError):
            await ws_task
        logger.info("WebSocket Redis subscriber task stopped")
    await ws_service.close()

    # Shutdown — close Redis pool
    if app.state.arq_pool is not None:
        await app.state.arq_pool.aclose()
        logger.info("ARQ Redis pool closed")


# ── App instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ── Middleware registration (outermost first) ────────────────────────────────
# Order matters in Starlette — first added = outermost wrapper.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# ── Exception handlers ──────────────────────────────────────────────────────
register_error_handlers(app)


# ── Static file serving ─────────────────────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# ── Router registration ─────────────────────────────────────────────────────
from app.routers.health import router as health_router  # noqa: E402
from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.devices import router as devices_router  # noqa: E402
from app.routers.ml import router as ml_router  # noqa: E402
from app.routers.rules import router as rules_router  # noqa: E402
from app.routers.students import router as students_router  # noqa: E402
from app.routers.warnings import router as warnings_router  # noqa: E402
from app.routers.waste import router as waste_router  # noqa: E402
from app.routers.analytics import router as analytics_router  # noqa: E402
from app.routers.filter_presets import router as filter_presets_router  # noqa: E402
from app.routers.notifications import router as notifications_router  # noqa: E402
from app.routers.templates import router as templates_router  # noqa: E402
from app.routers.config import router as config_router  # noqa: E402
from app.routers.reports import router as reports_router  # noqa: E402
from app.routers.monitoring import router as monitoring_router  # noqa: E402
from app.routers.settings import router as settings_router  # noqa: E402
from app.routers.audit import router as audit_router  # noqa: E402
from app.routers.roles import router as roles_router  # noqa: E402
from app.routers.ws import router as ws_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(waste_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(warnings_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(filter_presets_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(ws_router)
