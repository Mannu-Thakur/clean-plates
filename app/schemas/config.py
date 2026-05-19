"""Runtime configuration schemas for Phase 6 config routes."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ThresholdSchema(BaseModel):
    waste_threshold_grams: float = Field(default=150.0, ge=0)
    warning_threshold_grams: float = Field(default=100.0, ge=0)
    penalty_threshold_grams: float = Field(default=200.0, ge=0)
    improvement_target_pct: float = Field(default=25.0, ge=0, le=100)
    reset_duration_days: int = Field(default=30, ge=1)
    warning_count_for_penalty: int = Field(default=5, ge=1)


class MealTimingSchema(BaseModel):
    name: str
    display_name: str
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    is_active: bool = True
    order_index: int = Field(ge=0)

    @field_validator("name", mode="before")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value


class BranchSchema(BaseModel):
    code: str
    name: str

    @field_validator("code", mode="before")
    @classmethod
    def _clean_code(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value


class SystemPolicySchema(BaseModel):
    sync_frequency_minutes: int = Field(default=5, ge=1)
    offline_handling: str = "queue"
    backup_interval_hours: int = Field(default=24, ge=1)
    data_retention_days: int = Field(default=365, ge=1)
    log_retention_days: int = Field(default=30, ge=1)
    audit_retention_days: int = Field(default=90, ge=1)


class AppearanceConfigSchema(BaseModel):
    theme: str = "dark"
    logo_path: str | None = None
    primary_color: str = "#6366f1"
    institution_display_name: str | None = None


class SecurityConfigSchema(BaseModel):
    access_token_expiry_minutes: int = Field(default=1440, ge=5, le=1440)
    refresh_token_expiry_days: int = Field(default=30, ge=1, le=365)
    min_password_length: int = Field(default=8, ge=8, le=128)
    require_uppercase: bool = True
    require_numbers: bool = True
    max_login_attempts: int = Field(default=5, ge=1, le=50)
    lockout_duration_minutes: int = Field(default=15, ge=1, le=1440)
    session_timeout_minutes: int = Field(default=1440, ge=5, le=1440)


class DeviceConfigSchema(BaseModel):
    device_offline_threshold_minutes: int = Field(default=10, ge=1)
    heartbeat_interval_seconds: int = Field(default=60, ge=5)
    sync_batch_size: int = Field(default=100, ge=1, le=10000)


class InstitutionConfigSchema(BaseModel):
    name: str = "CleanPlates Institution"
    code: str = "CP"
    timezone: str = "Asia/Kolkata"
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None


class ConfigDataSchema(BaseModel):
    section: str
    data: dict


class ConfigUpdateSchema(BaseModel):
    data: dict
