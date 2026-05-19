"""
Pydantic Settings — single source of truth for all environment configuration.

Ref: 04-middlewares.md § Pydantic Settings
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── App ──────────────────────────────────────────
    APP_NAME: str = "CleanPlates"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str  # JWT signing key — MUST be set in .env

    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cleanplates.db"

    # ── Redis ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── JWT ──────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Security ─────────────────────────────────────
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # ── Email (optional until Phase 6) ───────────────
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@cleanplates.local"

    # ── CORS ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    # ── File Storage ─────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    BACKUPS_DIR: str = "./backups"

    # ── Data Retention ───────────────────────────────
    AUDIT_RETENTION_DAYS: int = 90
    LOG_RETENTION_DAYS: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
