"""
FastAPI application entry point.

- Lifespan: initializes ARQ Redis pool on startup, closes on shutdown.
- Middleware registration order per 04-middlewares.md § Middleware Registration Order.
- Static file serving for uploads.
- Router registration with /api/v1 prefix.

Ref: 06-phase-wise-plan.md Phase 1
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

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

    yield

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
from app.routers.students import router as students_router  # noqa: E402
from app.routers.warnings import router as warnings_router  # noqa: E402
from app.routers.waste import router as waste_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(waste_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(warnings_router, prefix="/api/v1")
