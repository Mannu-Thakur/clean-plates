"""
Warning, penalty, and escalation routers.

Ref: docs/plans/03-routes.md section 6.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import warning_controller
from app.core.redis import get_arq_pool
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.warnings import (
    BulkResolveSchema,
    EscalateWarningSchema,
    EscalationSchema,
    PaginatedPenalties,
    PaginatedWarnings,
    PenaltySchema,
    ResolveWarningSchema,
    RevokePenaltySchema,
    ReviewEscalationSchema,
    WarningSummarySchema,
)

router = APIRouter(tags=["Warnings"])
warnings_router = APIRouter(prefix="/warnings", tags=["Warnings"])
penalties_router = APIRouter(prefix="/penalties", tags=["Penalties"])
escalations_router = APIRouter(prefix="/escalations", tags=["Escalations"])

WARNING_READ_ROLES = ("super_admin", "institution_admin", "mess_admin")
WARNING_ADMIN_ROLES = ("super_admin", "institution_admin")


@warnings_router.get("/", response_model=PaginatedWarnings)
async def list_warnings(
    status_filter: str | None = Query(default=None, alias="status"),
    level: str | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await warning_controller.list_warnings(
        db,
        status_filter=status_filter,
        level=level,
        student_id=str(student_id) if student_id else None,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


@warnings_router.get("/stats", response_model=WarningSummarySchema)
async def get_warning_stats(
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await warning_controller.get_warning_stats(db)


@warnings_router.get("/export")
async def export_warnings(
    export_format: str = Query(alias="format"),
    status_filter: str | None = Query(default=None, alias="status"),
    level: str | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    content, media_type, filename = await warning_controller.export_warnings(
        db,
        export_format=export_format,
        status_filter=status_filter,
        level=level,
        student_id=str(student_id) if student_id else None,
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@warnings_router.patch("/bulk/resolve", response_model=MessageSchema)
async def bulk_resolve(
    body: BulkResolveSchema,
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await warning_controller.bulk_resolve(db, body, current_user=current_user)
    return MessageSchema(message="Warnings resolved")


@warnings_router.patch("/{warning_id}/resolve", response_model=MessageSchema)
async def resolve_warning(
    warning_id: UUID,
    body: ResolveWarningSchema,
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await warning_controller.resolve_warning(db, str(warning_id), body, current_user=current_user)
    return MessageSchema(message="Warning resolved")


@warnings_router.post("/{warning_id}/escalate", response_model=EscalationSchema)
async def escalate_warning(
    warning_id: UUID,
    body: EscalateWarningSchema,
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await warning_controller.escalate_warning(db, str(warning_id), body, current_user=current_user)


@warnings_router.post("/{warning_id}/apply-penalty", response_model=PenaltySchema)
async def apply_penalty(
    warning_id: UUID,
    current_user: UserSchema = Depends(require_roles(*WARNING_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await warning_controller.apply_penalty(db, str(warning_id), current_user=current_user, arq_pool=arq_pool)


@penalties_router.get("/", response_model=PaginatedPenalties)
async def list_penalties(
    status_filter: str | None = Query(default=None, alias="status"),
    student_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*WARNING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await warning_controller.list_penalties(
        db,
        status_filter=status_filter,
        student_id=str(student_id) if student_id else None,
        page=page,
        size=size,
    )


@penalties_router.patch("/{penalty_id}/revoke", response_model=MessageSchema)
async def revoke_penalty(
    penalty_id: UUID,
    body: RevokePenaltySchema,
    current_user: UserSchema = Depends(require_roles(*WARNING_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await warning_controller.revoke_penalty(db, str(penalty_id), body, current_user=current_user)
    return MessageSchema(message="Penalty revoked")


@escalations_router.get("/", response_model=list[EscalationSchema])
async def list_escalations(
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: UserSchema = Depends(require_roles(*WARNING_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await warning_controller.list_escalations(db, status_filter=status_filter)


@escalations_router.post("/{escalation_id}/review", response_model=MessageSchema)
async def review_escalation(
    escalation_id: UUID,
    body: ReviewEscalationSchema,
    current_user: UserSchema = Depends(require_roles(*WARNING_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    await warning_controller.review_escalation(
        db, str(escalation_id), body, current_user=current_user, arq_pool=arq_pool
    )
    return MessageSchema(message="Escalation reviewed")


router.include_router(warnings_router)
router.include_router(penalties_router)
router.include_router(escalations_router)
