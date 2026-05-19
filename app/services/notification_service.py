"""Notification CRUD, recipient resolution, and delivery dispatch."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationDeliveryModel, NotificationModel
from app.models.student import StudentMappingModel
from app.models.warning import PenaltyModel, WarningModel
from app.schemas.auth import UserSchema
from app.schemas.notifications import (
    BroadcastResultSchema,
    BroadcastSchema,
    DeliveryStatusItemSchema,
    DeliveryStatusSchema,
    NotifStatsSchema,
    NotificationCreateSchema,
    NotificationDetailSchema,
    NotificationPreferenceSchema,
    NotificationSchema,
    PaginatedNotifications,
    ScheduleNotifSchema,
)
from app.services import audit_service, config_service, email_service

DEFAULT_NOTIFICATION_PREFERENCES = [
    {"type": "warning", "dashboard": True, "email": True},
    {"type": "penalty", "dashboard": True, "email": True},
    {"type": "alert", "dashboard": True, "email": True},
    {"type": "system", "dashboard": True, "email": False},
    {"type": "custom", "dashboard": True, "email": True},
]


@dataclass(slots=True)
class Recipient:
    id: str
    email: str | None = None
    name: str | None = None
    branch: str | None = None
    hostel: str | None = None
    year: int | None = None


@dataclass(slots=True)
class CreatedNotification:
    notification: NotificationModel
    recipient_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _audit_user(current_user: UserSchema | None) -> dict:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _delivery_channels(channel: str) -> list[str]:
    return ["dashboard", "email"] if channel == "both" else [channel]


def _notification_state(notification: NotificationModel) -> dict[str, Any]:
    return {
        "id": notification.id,
        "type": notification.type,
        "channel": notification.channel,
        "subject": notification.subject,
        "status": notification.status,
        "recipient_type": notification.recipient_type,
        "recipient_ids": notification.recipient_ids,
        "scheduled_at": notification.scheduled_at.isoformat() if notification.scheduled_at else None,
    }


def _normalize_preferences(rows: list[dict[str, Any]] | None) -> list[NotificationPreferenceSchema]:
    by_type = {
        str(row.get("type", "")).strip().lower(): row
        for row in rows or []
        if str(row.get("type", "")).strip()
    }
    return [
        NotificationPreferenceSchema.model_validate({**fallback, **by_type.get(fallback["type"], {})})
        for fallback in DEFAULT_NOTIFICATION_PREFERENCES
    ]


async def _notification_or_404(db: AsyncSession, notification_id: str) -> NotificationModel:
    notification = await db.get(NotificationModel, notification_id)
    if notification is None or notification.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


async def _mapping_recipients(stmt_result) -> list[Recipient]:
    recipients: list[Recipient] = []
    seen: set[str] = set()
    for mapping in stmt_result:
        recipient_id = str(mapping.student_id)
        if recipient_id in seen:
            continue
        seen.add(recipient_id)
        recipients.append(
            Recipient(
                id=recipient_id,
                email=mapping.email,
                name=mapping.name,
                branch=mapping.branch,
                hostel=mapping.hostel,
                year=mapping.year,
            )
        )
    return recipients


async def resolve_recipients(
    db: AsyncSession,
    *,
    recipient_type: str,
    recipient_ids: list[str] | None = None,
    recipient_filter: dict[str, Any] | None = None,
) -> list[Recipient]:
    recipient_ids = [str(item).strip() for item in (recipient_ids or []) if str(item).strip()]
    recipient_filter = recipient_filter or {}

    if recipient_type == "individual":
        direct_email_recipients = [
            Recipient(id=item, email=item)
            for item in recipient_ids
            if "@" in item and "." in item.rsplit("@", 1)[-1]
        ]
        lookup_ids = [item for item in recipient_ids if item not in {recipient.id for recipient in direct_email_recipients}]
        recipients = direct_email_recipients
        if lookup_ids:
            result = await db.execute(
                select(StudentMappingModel).where(
                    or_(
                        StudentMappingModel.student_id.in_(lookup_ids),
                        StudentMappingModel.device_id.in_(lookup_ids),
                        StudentMappingModel.email.in_(lookup_ids),
                    )
                )
            )
            recipients.extend(await _mapping_recipients(result.scalars().all()))
            found = {recipient.id for recipient in recipients} | {recipient.email for recipient in recipients if recipient.email}
            for missing in lookup_ids:
                if missing not in found:
                    recipients.append(Recipient(id=missing))
        return recipients

    stmt = select(StudentMappingModel)
    if recipient_type == "branch":
        branches = recipient_ids or [str(recipient_filter.get("branch") or "").strip()]
        branches = [branch for branch in branches if branch]
        if branches:
            stmt = stmt.where(StudentMappingModel.branch.in_(branches))
    elif recipient_type == "hostel":
        hostels = recipient_ids or [str(recipient_filter.get("hostel") or "").strip()]
        hostels = [hostel for hostel in hostels if hostel]
        if hostels:
            stmt = stmt.where(StudentMappingModel.hostel.in_(hostels))
    elif recipient_type == "year":
        years = recipient_ids or [str(recipient_filter.get("year") or "").strip()]
        int_years = [int(year) for year in years if str(year).strip().isdigit()]
        if int_years:
            stmt = stmt.where(StudentMappingModel.year.in_(int_years))
    elif recipient_type != "all":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported recipient_type")

    if recipient_filter.get("branch") and recipient_type != "branch":
        stmt = stmt.where(StudentMappingModel.branch == str(recipient_filter["branch"]).strip())
    if recipient_filter.get("hostel") and recipient_type != "hostel":
        stmt = stmt.where(StudentMappingModel.hostel == str(recipient_filter["hostel"]).strip())
    if recipient_filter.get("year") and recipient_type != "year":
        stmt = stmt.where(StudentMappingModel.year == int(recipient_filter["year"]))

    result = await db.execute(stmt.order_by(StudentMappingModel.name.asc()))
    return await _mapping_recipients(result.scalars().all())


async def create_system_notification(
    db: AsyncSession,
    *,
    notif_type: str,
    channel: str,
    subject: str,
    body: str,
    recipient_type: str,
    recipient_ids: list[str] | None = None,
    recipient_filter: dict[str, Any] | None = None,
    sender_id: str | None = None,
    template_id: str | None = None,
    scheduled_at: datetime | None = None,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
) -> CreatedNotification:
    recipients = await resolve_recipients(
        db,
        recipient_type=recipient_type,
        recipient_ids=recipient_ids,
        recipient_filter=recipient_filter,
    )
    notification = NotificationModel(
        type=notif_type,
        channel=channel,
        subject=subject,
        body=body,
        sender_id=sender_id,
        recipient_type=recipient_type,
        recipient_ids=[recipient.id for recipient in recipients] if recipients else list(recipient_ids or []),
        template_id=template_id,
        status="pending",
        scheduled_at=scheduled_at,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notification)
    await db.flush()

    for recipient in recipients:
        for channel_name in _delivery_channels(channel):
            db.add(
                NotificationDeliveryModel(
                    notification_id=notification.id,
                    recipient_id=recipient.id,
                    recipient_email=recipient.email,
                    channel=channel_name,
                    status="pending",
                )
            )
    if not recipients:
        notification.status = "failed"
    await db.flush()
    return CreatedNotification(notification=notification, recipient_count=len(recipients))


async def enqueue_or_dispatch_notification(
    db: AsyncSession,
    *,
    notification_id: str,
    arq_pool: ArqRedis | None = None,
) -> None:
    if arq_pool is not None:
        await arq_pool.enqueue_job("send_notification_task", notification_id)
        return
    await dispatch_notification(db, notification_id)
    await db.commit()


def _apply_notification_filters(
    stmt,
    *,
    tab: str | None = None,
    type_filter: str | None = None,
    channel: str | None = None,
    status_filter: str | None = None,
    is_read: bool | None = None,
):
    stmt = stmt.where(NotificationModel.is_deleted.is_(False))
    if type_filter:
        stmt = stmt.where(NotificationModel.type == type_filter.strip().lower())
    if channel:
        stmt = stmt.where(NotificationModel.channel == channel.strip().lower())
    if status_filter:
        stmt = stmt.where(NotificationModel.status == status_filter.strip().lower())
    if is_read is not None:
        stmt = stmt.where(NotificationModel.is_read.is_(is_read))
    normalized_tab = (tab or "").strip().lower()
    if normalized_tab == "inbox":
        stmt = stmt.where(NotificationModel.is_read.is_(False), NotificationModel.status.in_(("sent", "partial")))
    elif normalized_tab == "sent":
        stmt = stmt.where(NotificationModel.status.in_(("sent", "partial")))
    elif normalized_tab == "scheduled":
        stmt = stmt.where(NotificationModel.status == "pending", NotificationModel.scheduled_at.is_not(None))
    elif normalized_tab == "failed":
        stmt = stmt.where(NotificationModel.status == "failed")
    elif normalized_tab == "pending":
        stmt = stmt.where(NotificationModel.status == "pending")
    return stmt


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
    page = max(page, 1)
    size = min(max(size, 1), 100)
    count_stmt = _apply_notification_filters(
        select(func.count(NotificationModel.id)),
        tab=tab,
        type_filter=type_filter,
        channel=channel,
        status_filter=status_filter,
        is_read=is_read,
    )
    total = int((await db.execute(count_stmt)).scalar_one() or 0)
    stmt = _apply_notification_filters(
        select(NotificationModel),
        tab=tab,
        type_filter=type_filter,
        channel=channel,
        status_filter=status_filter,
        is_read=is_read,
    )
    stmt = stmt.order_by(NotificationModel.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return PaginatedNotifications(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[NotificationSchema.model_validate(notification) for notification in result.scalars().all()],
    )


async def get_preferences(db: AsyncSession) -> list[NotificationPreferenceSchema]:
    config = await config_service.get_config(db, "notification_preferences")
    rows = config.get("items") if isinstance(config, dict) else None
    return _normalize_preferences(rows if isinstance(rows, list) else None)


async def update_preferences(
    db: AsyncSession,
    rows: list[NotificationPreferenceSchema],
    *,
    current_user: UserSchema,
) -> list[NotificationPreferenceSchema]:
    before = [item.model_dump() for item in await get_preferences(db)]
    after = [item.model_dump() for item in _normalize_preferences([row.model_dump() for row in rows])]
    await config_service.set_config(
        db,
        "notification_preferences",
        {"items": after},
        updated_by=current_user.id,
    )
    await audit_service.log(
        db,
        event_type="notification.preferences_updated",
        action="update",
        resource_type="notification",
        summary="Updated notification preferences",
        before_state={"items": before},
        after_state={"items": after},
        **_audit_user(current_user),
    )
    return [NotificationPreferenceSchema.model_validate(item) for item in after]


async def get_notification(db: AsyncSession, notification_id: str) -> NotificationDetailSchema:
    notification = await _notification_or_404(db, notification_id)
    return NotificationDetailSchema.model_validate(notification)


async def get_delivery_status(db: AsyncSession, notification_id: str) -> DeliveryStatusSchema:
    await _notification_or_404(db, notification_id)
    result = await db.execute(
        select(NotificationDeliveryModel)
        .where(NotificationDeliveryModel.notification_id == notification_id)
        .order_by(NotificationDeliveryModel.channel.asc(), NotificationDeliveryModel.recipient_id.asc())
    )
    deliveries = [DeliveryStatusItemSchema.model_validate(item) for item in result.scalars().all()]
    delivered = sum(1 for item in deliveries if item.status == "delivered")
    failed = sum(1 for item in deliveries if item.status == "failed")
    pending = sum(1 for item in deliveries if item.status == "pending")
    return DeliveryStatusSchema(
        notification_id=notification_id,
        total_recipients=len({item.recipient_id for item in deliveries}),
        delivered=delivered,
        failed=failed,
        pending=pending,
        deliveries=deliveries,
    )


async def mark_read(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    notification = await _notification_or_404(db, notification_id)
    if notification.is_read:
        return
    before = _notification_state(notification)
    notification.is_read = True
    await db.flush()
    await audit_service.log(
        db,
        event_type="notification.read",
        action="update",
        resource_type="notification",
        resource_id=notification.id,
        summary="Marked notification as read",
        before_state=before,
        after_state=_notification_state(notification),
        **_audit_user(current_user),
    )


async def mark_all_read(db: AsyncSession, *, current_user: UserSchema) -> int:
    result = await db.execute(
        select(NotificationModel).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.is_read.is_(False),
            NotificationModel.channel.in_(("dashboard", "both")),
        )
    )
    notifications = result.scalars().all()
    for notification in notifications:
        notification.is_read = True
    await db.flush()
    await audit_service.log(
        db,
        event_type="notification.bulk_read",
        action="update",
        resource_type="notification",
        summary=f"Marked {len(notifications)} notifications as read",
        **_audit_user(current_user),
    )
    return len(notifications)


async def delete_notification(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    notification = await _notification_or_404(db, notification_id)
    before = _notification_state(notification)
    notification.is_deleted = True
    await db.flush()
    await audit_service.log(
        db,
        event_type="notification.deleted",
        action="delete",
        resource_type="notification",
        resource_id=notification.id,
        summary="Deleted notification",
        before_state=before,
        **_audit_user(current_user),
    )


async def send_notification(
    db: AsyncSession,
    body: NotificationCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> NotificationSchema:
    created = await create_system_notification(
        db,
        notif_type=body.type,
        channel=body.channel,
        subject=body.subject,
        body=body.body,
        recipient_type=body.recipient_type,
        recipient_ids=body.recipient_ids,
        sender_id=current_user.id,
        template_id=str(body.template_id) if body.template_id else None,
    )
    await audit_service.log(
        db,
        event_type="notification.sent",
        action="create",
        resource_type="notification",
        resource_id=created.notification.id,
        summary=f"Queued notification '{created.notification.subject}'",
        after_state=_notification_state(created.notification),
        **_audit_user(current_user),
    )
    await db.commit()
    if created.recipient_count:
        await enqueue_or_dispatch_notification(db, notification_id=created.notification.id, arq_pool=arq_pool)
    return NotificationSchema.model_validate(created.notification)


async def send_broadcast(
    db: AsyncSession,
    body: BroadcastSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> BroadcastResultSchema:
    created = await create_system_notification(
        db,
        notif_type="custom",
        channel=body.channel,
        subject=body.subject,
        body=body.body,
        recipient_type=body.recipient_type,
        recipient_filter=body.recipient_filter,
        sender_id=current_user.id,
        template_id=str(body.template_id) if body.template_id else None,
    )
    await audit_service.log(
        db,
        event_type="notification.broadcast",
        action="create",
        resource_type="notification",
        resource_id=created.notification.id,
        summary=f"Queued broadcast '{created.notification.subject}'",
        after_state=_notification_state(created.notification),
        **_audit_user(current_user),
    )
    await db.commit()
    if created.recipient_count:
        await enqueue_or_dispatch_notification(db, notification_id=created.notification.id, arq_pool=arq_pool)
    return BroadcastResultSchema(
        total_recipients=created.recipient_count,
        queued=created.recipient_count if created.recipient_count else 0,
        failed=0 if created.recipient_count else 1,
    )


async def schedule_notification(
    db: AsyncSession,
    body: ScheduleNotifSchema,
    *,
    current_user: UserSchema,
) -> NotificationSchema:
    scheduled_at = body.scheduled_at
    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone(UTC).replace(tzinfo=None)
    if scheduled_at <= _utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_at must be in the future")
    created = await create_system_notification(
        db,
        notif_type=body.type,
        channel=body.channel,
        subject=body.subject,
        body=body.body,
        recipient_type=body.recipient_type,
        recipient_ids=body.recipient_ids,
        sender_id=current_user.id,
        template_id=str(body.template_id) if body.template_id else None,
        scheduled_at=scheduled_at,
    )
    await audit_service.log(
        db,
        event_type="notification.scheduled",
        action="create",
        resource_type="notification",
        resource_id=created.notification.id,
        summary=f"Scheduled notification '{created.notification.subject}'",
        after_state=_notification_state(created.notification),
        **_audit_user(current_user),
    )
    return NotificationSchema.model_validate(created.notification)


async def retry_failed(
    db: AsyncSession,
    notification_id: str,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> None:
    notification = await _notification_or_404(db, notification_id)
    if notification.status not in {"failed", "partial"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed notifications can be retried")
    result = await db.execute(
        select(NotificationDeliveryModel).where(
            NotificationDeliveryModel.notification_id == notification_id,
            NotificationDeliveryModel.status == "failed",
        )
    )
    deliveries = result.scalars().all()
    for delivery in deliveries:
        delivery.status = "pending"
        delivery.error = None
        delivery.delivered_at = None
    notification.status = "pending"
    notification.retry_count += 1
    await db.flush()
    await audit_service.log(
        db,
        event_type="notification.retry",
        action="retry",
        resource_type="notification",
        resource_id=notification.id,
        summary="Retried failed notification delivery",
        **_audit_user(current_user),
    )
    await db.commit()
    await enqueue_or_dispatch_notification(db, notification_id=notification.id, arq_pool=arq_pool)


async def get_notification_stats(db: AsyncSession) -> NotifStatsSchema:
    today = date.today().isoformat()
    unread = await db.scalar(
        select(func.count(NotificationModel.id)).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.is_read.is_(False),
            NotificationModel.channel.in_(("dashboard", "both")),
        )
    )
    sent_today = await db.scalar(
        select(func.count(NotificationModel.id)).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.status.in_(("sent", "partial")),
            func.date(NotificationModel.sent_at) == today,
        )
    )
    failed = await db.scalar(
        select(func.count(NotificationModel.id)).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.status == "failed",
        )
    )
    pending = await db.scalar(
        select(func.count(NotificationModel.id)).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.status == "pending",
        )
    )
    return NotifStatsSchema(
        unread=int(unread or 0),
        sent_today=int(sent_today or 0),
        failed=int(failed or 0),
        pending=int(pending or 0),
    )


async def _delivery_context(db: AsyncSession, delivery: NotificationDeliveryModel) -> dict[str, Any]:
    result = await db.execute(select(StudentMappingModel).where(StudentMappingModel.student_id == delivery.recipient_id))
    mapping = result.scalar_one_or_none()
    if mapping is None:
        return {"recipient_id": delivery.recipient_id, "email": delivery.recipient_email}
    return {
        "recipient_id": delivery.recipient_id,
        "student_id": mapping.student_id,
        "student_name": mapping.name,
        "name": mapping.name,
        "roll_number": mapping.roll_number,
        "branch": mapping.branch,
        "year": mapping.year,
        "hostel": mapping.hostel,
        "room_number": mapping.room_number,
        "email": mapping.email,
    }


async def _sync_related_email_sent(db: AsyncSession, notification: NotificationModel) -> None:
    if notification.related_entity_type == "warning" and notification.related_entity_id:
        warning = await db.get(WarningModel, notification.related_entity_id)
        if warning is not None:
            warning.email_sent = notification.status in {"sent", "partial"}
    elif notification.related_entity_type == "penalty" and notification.related_entity_id:
        penalty = await db.get(PenaltyModel, notification.related_entity_id)
        if penalty is not None:
            penalty.email_sent = notification.status in {"sent", "partial"}


async def _update_notification_status(db: AsyncSession, notification: NotificationModel) -> None:
    result = await db.execute(
        select(NotificationDeliveryModel).where(NotificationDeliveryModel.notification_id == notification.id)
    )
    deliveries = result.scalars().all()
    if not deliveries:
        notification.status = "failed"
        return
    delivered = sum(1 for item in deliveries if item.status == "delivered")
    failed = sum(1 for item in deliveries if item.status == "failed")
    pending = sum(1 for item in deliveries if item.status == "pending")
    if pending:
        notification.status = "pending"
    elif failed == 0:
        notification.status = "sent"
    elif delivered > 0:
        notification.status = "partial"
    else:
        notification.status = "failed"
    if notification.status in {"sent", "partial"} and notification.sent_at is None:
        notification.sent_at = _utcnow()
    await _sync_related_email_sent(db, notification)


async def dispatch_notification(db: AsyncSession, notification_id: str) -> NotificationModel:
    notification = await _notification_or_404(db, notification_id)
    if notification.scheduled_at and notification.scheduled_at > _utcnow():
        return notification
    result = await db.execute(
        select(NotificationDeliveryModel).where(
            NotificationDeliveryModel.notification_id == notification.id,
            NotificationDeliveryModel.status == "pending",
        )
    )
    deliveries = result.scalars().all()
    for delivery in deliveries:
        if delivery.channel == "dashboard":
            delivery.status = "delivered"
            delivery.delivered_at = _utcnow()
            delivery.error = None
            continue
        if delivery.channel != "email":
            delivery.status = "failed"
            delivery.error = f"Unsupported channel: {delivery.channel}"
            continue
        if not delivery.recipient_email:
            delivery.status = "failed"
            delivery.error = "Recipient has no email address"
            continue

        context = await _delivery_context(db, delivery)
        if notification.template_id:
            rendered = await email_service.render_template(db, notification.template_id, context)
            subject = rendered["subject"]
            body_html = rendered["body_html"]
        else:
            subject = email_service.render_string(notification.subject, context)
            body_html = email_service.render_string(notification.body, context)
        send_result = await email_service.send_email(delivery.recipient_email, subject, body_html)
        delivery.status = "delivered" if send_result.success else "failed"
        delivery.delivered_at = _utcnow() if send_result.success else None
        delivery.error = send_result.error
    await _update_notification_status(db, notification)
    await db.flush()
    return notification


async def execute_scheduled_notifications(db: AsyncSession, *, arq_pool: ArqRedis | None = None) -> int:
    result = await db.execute(
        select(NotificationModel).where(
            NotificationModel.is_deleted.is_(False),
            NotificationModel.status == "pending",
            NotificationModel.scheduled_at.is_not(None),
            NotificationModel.scheduled_at <= _utcnow(),
        )
    )
    notifications = result.scalars().all()
    for notification in notifications:
        if arq_pool is not None:
            await arq_pool.enqueue_job("send_notification_task", notification.id)
        else:
            await dispatch_notification(db, notification.id)
    return len(notifications)
