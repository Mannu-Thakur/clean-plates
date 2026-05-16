"""
Warning controller - thin dispatch layer over warning_service.

Ref: docs/plans/02-controllers.md section 5.
"""

from __future__ import annotations

from datetime import date

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.warnings import (
    BulkResolveSchema,
    EscalateWarningSchema,
    EscalationSchema,
    PaginatedPenalties,
    PaginatedWarnings,
    PenaltyCreateSchema,
    PenaltySchema,
    ResolveWarningSchema,
    RevokePenaltySchema,
    ReviewEscalationSchema,
    WarningCreateSchema,
    WarningSchema,
    WarningSummarySchema,
)
from app.services import warning_service


async def list_warnings(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    level: str | None = None,
    student_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedWarnings:
    return await warning_service.list_warnings(
        db,
        status_filter=status_filter,
        level=level,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


async def get_warning_stats(db: AsyncSession) -> WarningSummarySchema:
    return await warning_service.get_warning_stats(db)


async def create_warning(
    db: AsyncSession,
    student_id: str,
    body: WarningCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> WarningSchema:
    return await warning_service.create_warning(db, student_id, body, current_user=current_user, arq_pool=arq_pool)


async def resolve_warning(
    db: AsyncSession,
    warning_id: str,
    body: ResolveWarningSchema,
    *,
    current_user: UserSchema,
) -> None:
    await warning_service.resolve_warning(db, warning_id, body, current_user=current_user)


async def escalate_warning(
    db: AsyncSession,
    warning_id: str,
    body: EscalateWarningSchema,
    *,
    current_user: UserSchema,
) -> EscalationSchema:
    return await warning_service.escalate_warning(db, warning_id, body, current_user=current_user)


async def apply_penalty(
    db: AsyncSession,
    warning_id: str,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> PenaltySchema:
    return await warning_service.apply_penalty(db, warning_id, current_user=current_user, arq_pool=arq_pool)


async def bulk_resolve(
    db: AsyncSession,
    body: BulkResolveSchema,
    *,
    current_user: UserSchema,
) -> None:
    await warning_service.bulk_resolve(db, body, current_user=current_user)


async def export_warnings(
    db: AsyncSession,
    *,
    export_format: str,
    status_filter: str | None = None,
    level: str | None = None,
    student_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[bytes, str, str]:
    return await warning_service.export_warnings(
        db,
        export_format=export_format,
        status_filter=status_filter,
        level=level,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
    )


async def list_penalties(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    student_id: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedPenalties:
    return await warning_service.list_penalties(
        db,
        status_filter=status_filter,
        student_id=student_id,
        page=page,
        size=size,
    )


async def create_penalty_direct(
    db: AsyncSession,
    student_id: str,
    body: PenaltyCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> PenaltySchema:
    return await warning_service.create_penalty_direct(
        db, student_id, body, current_user=current_user, arq_pool=arq_pool
    )


async def revoke_penalty(
    db: AsyncSession,
    penalty_id: str,
    body: RevokePenaltySchema,
    *,
    current_user: UserSchema,
) -> None:
    await warning_service.revoke_penalty(db, penalty_id, body, current_user=current_user)


async def list_escalations(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
) -> list[EscalationSchema]:
    return await warning_service.list_escalations(db, status_filter=status_filter)


async def review_escalation(
    db: AsyncSession,
    escalation_id: str,
    body: ReviewEscalationSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> None:
    await warning_service.review_escalation(db, escalation_id, body, current_user=current_user, arq_pool=arq_pool)
