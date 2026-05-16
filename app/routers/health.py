"""
Health check route.

Ref: 06-phase-wise-plan.md Phase 1 — Health & Infra
"""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])

_START_TIME = time.time()


@router.get("/health")
async def health_check():
    """Returns basic health status, version, and uptime."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }
