"""
Common/shared schemas used across all modules.

⚠ B1-fix: Created in Phase 1 — PaginatedBase is imported by every paginated
response schema starting Phase 2.

Ref: 05-schemas.md §13
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PaginatedBase(BaseModel):
    """Base schema for all paginated responses."""
    total: int
    page: int
    size: int
    pages: int


class MessageSchema(BaseModel):
    """Generic success message response."""
    message: str


class ErrorSchema(BaseModel):
    """Generic error response."""
    detail: str


# ── Utility schemas (stubs — completed in Phase 8) ──────────────────────────

class SystemInfoSchema(BaseModel):
    os_version: str
    python_version: str
    app_version: str
    db_size_mb: float
    uptime_seconds: float
    disk_usage_pct: float
    ram_usage_pct: float
    cpu_usage_pct: float


class LogoUrlSchema(BaseModel):
    logo_url: str


class TempPasswordSchema(BaseModel):
    temp_password: str
    message: str


class CacheResultSchema(BaseModel):
    cleared: bool
    keys_removed: int


class OptimizeResultSchema(BaseModel):
    success: bool
    freed_mb: float


class RestoreResultSchema(BaseModel):
    success: bool
    message: str
    restored_at: datetime
