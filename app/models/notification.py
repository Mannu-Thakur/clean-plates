"""Notification and email template models for Phase 6."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, updated_at_col, uuid_pk


class NotificationModel(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_status_scheduled_at", "status", "scheduled_at"),
    )

    id: Mapped[str] = uuid_pk()
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sender_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recipient_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("email_templates.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = created_at_col()

    deliveries = relationship("NotificationDeliveryModel", back_populates="notification", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Notification {self.type} {self.status}>"


class NotificationDeliveryModel(Base):
    """Per-recipient/channel delivery tracking for notifications."""

    __tablename__ = "notification_deliveries"

    id: Mapped[str] = uuid_pk()
    notification_id: Mapped[str] = mapped_column(String(36), ForeignKey("notifications.id"), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    notification = relationship("NotificationModel", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<NotificationDelivery {self.notification_id} {self.channel}:{self.status}>"


class EmailTemplateModel(Base):
    __tablename__ = "email_templates"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    def __repr__(self) -> str:
        return f"<EmailTemplate {self.type}:{self.name}>"
