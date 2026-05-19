"""Notification controller - thin dispatch layer."""

from __future__ import annotations

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.notifications import (
    BroadcastResultSchema,
    BroadcastSchema,
    DeliveryStatusSchema,
    NotifStatsSchema,
    NotificationCreateSchema,
    NotificationDetailSchema,
    NotificationSchema,
    PaginatedNotifications,
    ScheduleNotifSchema,
)
from app.services import notification_service


async def list_notifications(
    db: AsyncSession,
    *,
    tab: str | None = None,
    type_filter: str | None = None,
    channel: str | None = None,
    status_filter: str | None = None,
    is_read: bool | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedNotifications:
    return await notification_service.list_notifications(
        db,
        tab=tab,
        type_filter=type_filter,
        channel=channel,
        status_filter=status_filter,
        is_read=is_read,
        page=page,
        size=size,
    )


async def get_notification(db: AsyncSession, notification_id: str) -> NotificationDetailSchema:
    return await notification_service.get_notification(db, notification_id)


async def get_delivery_status(db: AsyncSession, notification_id: str) -> DeliveryStatusSchema:
    return await notification_service.get_delivery_status(db, notification_id)


async def mark_read(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    await notification_service.mark_read(db, notification_id, current_user=current_user)


async def mark_all_read(db: AsyncSession, *, current_user: UserSchema) -> int:
    return await notification_service.mark_all_read(db, current_user=current_user)


async def delete_notification(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    await notification_service.delete_notification(db, notification_id, current_user=current_user)


async def send_notification(
    db: AsyncSession,
    body: NotificationCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> NotificationSchema:
    return await notification_service.send_notification(db, body, current_user=current_user, arq_pool=arq_pool)


async def send_broadcast(
    db: AsyncSession,
    body: BroadcastSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> BroadcastResultSchema:
    return await notification_service.send_broadcast(db, body, current_user=current_user, arq_pool=arq_pool)


async def schedule_notification(
    db: AsyncSession,
    body: ScheduleNotifSchema,
    *,
    current_user: UserSchema,
) -> NotificationSchema:
    return await notification_service.schedule_notification(db, body, current_user=current_user)


async def retry_failed(
    db: AsyncSession,
    notification_id: str,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> None:
    await notification_service.retry_failed(db, notification_id, current_user=current_user, arq_pool=arq_pool)


async def get_notification_stats(db: AsyncSession) -> NotifStatsSchema:
    return await notification_service.get_notification_stats(db)
