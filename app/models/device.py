"""
Device models for Raspberry Pi identity and health snapshots.

Ref: docs/plans/01-models.md sections 3 and 4.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, _utcnow, created_at_col, updated_at_col, uuid_pk


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[str] = uuid_pk()
    device_serial: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    edge_node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(200), nullable=False)
    institution_code: Mapped[str] = mapped_column(String(50), nullable=False)
    campus_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mess_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mess_id: Mapped[str] = mapped_column(String(50), nullable=False)
    hostel_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hostel_block: Mapped[str | None] = mapped_column(String(50), nullable=True)
    floor_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wing_section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meal_capacity_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="online", nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active_since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    managed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    health_records = relationship(
        "DeviceHealthModel",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="desc(DeviceHealthModel.recorded_at)",
    )

    def __repr__(self) -> str:
        return f"<Device {self.device_serial} status={self.status}>"


class DeviceHealthModel(Base):
    __tablename__ = "device_health"

    id: Mapped[str] = uuid_pk()
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id"), nullable=False, index=True
    )
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    ram_percent: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    connectivity: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)

    device = relationship("DeviceModel", back_populates="health_records")

    def __repr__(self) -> str:
        return f"<DeviceHealth device_id={self.device_id} recorded_at={self.recorded_at}>"
