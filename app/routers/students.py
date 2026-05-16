"""
Student router - Phase 2 student mapping endpoints.

Ref: docs/plans/03-routes.md section 3. Student intelligence and warning
routes are added in Phase 3 after waste/warning models exist.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import student_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.students import (
    ImportResultSchema,
    MappingCreateSchema,
    MappingUpdateSchema,
    PaginatedStudents,
    StudentDetailSchema,
    StudentProfileUpdateSchema,
    StudentSchema,
)

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


@router.patch("/{student_id}", response_model=StudentSchema)
async def update_student_profile(
    student_id: UUID,
    body: StudentProfileUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*STUDENT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await student_controller.update_student_profile(db, str(student_id), body, current_user=current_user)
