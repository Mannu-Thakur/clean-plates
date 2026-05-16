"""
Student router - Phase 2 student mapping endpoints.

Ref: docs/plans/03-routes.md section 3. Student intelligence and warning
routes are added in Phase 3 after waste/warning models exist.
"""

from __future__ import annotations

from uuid import UUID

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import student_controller
from app.core.redis import get_arq_pool
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.students import (
    BulkWarnSchema,
    FoodBreakdownSchema,
    ImprovementSchema,
    ImportResultSchema,
    MappingCreateSchema,
    MappingUpdateSchema,
    MealPatternSchema,
    PaginatedStudents,
    StudentDetailSchema,
    StudentProfileUpdateSchema,
    StudentSchema,
    TimelineSchema,
    WasteStatsSchema,
)
from app.schemas.warnings import (
    PenaltyCreateSchema,
    PenaltySchema,
    StudentWarningsSchema,
    WarningCreateSchema,
    WarningSchema,
)
from app.schemas.waste import PaginatedEntries

router = APIRouter(prefix="/students", tags=["Students"])

STUDENT_READ_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")
STUDENT_WRITE_ROLES = ("super_admin", "institution_admin", "mess_admin")


@router.get("/", response_model=PaginatedStudents)
async def list_students(
    status_filter: str | None = Query(default=None, alias="status"),
    hostel: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1, le=4),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.list_students(
        db,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )


@router.get("/export")
async def export_students(
    export_format: str = Query(default="csv", alias="format"),
    status_filter: str | None = Query(default=None, alias="status"),
    hostel: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1, le=4),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    content, media_type, filename = await student_controller.export_students(
        db,
        export_format=export_format,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
        sort=sort,
        order=order,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import-mapping", response_model=ImportResultSchema)
async def import_mapping_csv(
    csv_file: UploadFile = File(...),
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.import_mapping_csv(db, csv_file, current_user=current_user)


@router.post("/bulk/warn", response_model=MessageSchema)
async def bulk_warn(
    body: BulkWarnSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    await student_controller.bulk_warn(db, body, current_user=current_user, arq_pool=arq_pool)
    return MessageSchema(message="Warnings issued")


@router.get("/{student_id}", response_model=StudentDetailSchema)
async def get_student(
    student_id: UUID,
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_student(db, str(student_id))


@router.post("/{student_id}/map", response_model=StudentSchema)
async def map_student_id(
    student_id: UUID,
    body: MappingCreateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.map_student_id(db, str(student_id), body, current_user=current_user)


@router.patch("/{student_id}/map", response_model=StudentSchema)
async def update_mapping(
    student_id: UUID,
    body: MappingUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.update_mapping(db, str(student_id), body, current_user=current_user)


@router.get("/{student_id}/stats", response_model=WasteStatsSchema)
async def get_student_stats(
    student_id: UUID,
    period: str = Query(default="30d"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_student_stats(db, str(student_id), period)


@router.get("/{student_id}/timeline", response_model=TimelineSchema)
async def get_student_timeline(
    student_id: UUID,
    period: str = Query(default="30d"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_student_timeline(db, str(student_id), period)


@router.get("/{student_id}/food-breakdown", response_model=FoodBreakdownSchema)
async def get_food_breakdown(
    student_id: UUID,
    period: str = Query(default="30d"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_food_breakdown(db, str(student_id), period)


@router.get("/{student_id}/meal-pattern", response_model=MealPatternSchema)
async def get_meal_pattern(
    student_id: UUID,
    period: str = Query(default="30d"),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_meal_pattern(db, str(student_id), period)


@router.get("/{student_id}/improvement", response_model=ImprovementSchema)
async def get_improvement_trend(
    student_id: UUID,
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_improvement_trend(db, str(student_id))


@router.get("/{student_id}/history", response_model=PaginatedEntries)
async def get_student_history(
    student_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*STUDENT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_student_history(db, str(student_id), page=page, size=size)


@router.get("/{student_id}/warnings", response_model=StudentWarningsSchema)
async def get_student_warnings(
    student_id: UUID,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.get_student_warnings(db, str(student_id))


@router.post("/{student_id}/warnings", response_model=WarningSchema, status_code=201)
async def create_warning(
    student_id: UUID,
    body: WarningCreateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await student_controller.create_warning(
        db,
        str(student_id),
        body,
        current_user=current_user,
        arq_pool=arq_pool,
    )


@router.post("/{student_id}/penalties", response_model=PenaltySchema, status_code=201)
async def create_penalty_direct(
    student_id: UUID,
    body: PenaltyCreateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await student_controller.create_penalty_direct(
        db,
        str(student_id),
        body,
        current_user=current_user,
        arq_pool=arq_pool,
    )


@router.patch("/{student_id}", response_model=StudentSchema)
async def update_student_profile(
    student_id: UUID,
    body: StudentProfileUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.update_student_profile(db, str(student_id), body, current_user=current_user)
