"""Notification center routes."""

from __future__ import annotations

from uuid import UUID

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import notification_controller
from app.core.redis import get_arq_pool
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
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

router = APIRouter(prefix="/notifications", tags=["Notifications"])

NOTIF_ROLES = ("super_admin", "institution_admin", "mess_admin")
NOTIF_ADMIN_ROLES = ("super_admin", "institution_admin")


@router.get("/", response_model=PaginatedNotifications)
async def list_notifications(
    tab: str | None = Query(default=None),
    type_filter: str | None = Query(default=None, alias="type"),
    channel: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await notification_controller.list_notifications(
        db,
        tab=tab,
        type_filter=type_filter,
        channel=channel,
        status_filter=status_filter,
        is_read=is_read,
        page=page,
        size=size,
    )


@router.get("/stats", response_model=NotifStatsSchema)
async def get_notification_stats(
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await notification_controller.get_notification_stats(db)


@router.post("/", response_model=NotificationSchema, status_code=201)
async def send_notification(
    body: NotificationCreateSchema,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await notification_controller.send_notification(db, body, current_user=current_user, arq_pool=arq_pool)


@router.post("/broadcast", response_model=BroadcastResultSchema)
async def send_broadcast(
    body: BroadcastSchema,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await notification_controller.send_broadcast(db, body, current_user=current_user, arq_pool=arq_pool)


@router.post("/schedule", response_model=NotificationSchema, status_code=201)
async def schedule_notification(
    body: ScheduleNotifSchema,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await notification_controller.schedule_notification(db, body, current_user=current_user)


@router.post("/mark-all-read", response_model=MessageSchema)
async def mark_all_read(
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    count = await notification_controller.mark_all_read(db, current_user=current_user)
    return MessageSchema(message=f"Marked {count} notifications as read")


@router.get("/{notif_id}/delivery", response_model=DeliveryStatusSchema)
async def get_delivery_status(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await notification_controller.get_delivery_status(db, str(notif_id))


@router.get("/{notif_id}", response_model=NotificationDetailSchema)
async def get_notification(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await notification_controller.get_notification(db, str(notif_id))


@router.patch("/{notif_id}/read", response_model=MessageSchema)
async def mark_read(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await notification_controller.mark_read(db, str(notif_id), current_user=current_user)
    return MessageSchema(message="Notification marked as read")


@router.delete("/{notif_id}", response_model=MessageSchema)
async def delete_notification(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await notification_controller.delete_notification(db, str(notif_id), current_user=current_user)
    return MessageSchema(message="Notification deleted")


@router.post("/{notif_id}/retry", response_model=MessageSchema)
async def retry_failed(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*NOTIF_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    await notification_controller.retry_failed(db, str(notif_id), current_user=current_user, arq_pool=arq_pool)
    return MessageSchema(message="Notification retry queued")
