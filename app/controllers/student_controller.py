"""
Student controller - thin dispatch layer over student_service.

Ref: docs/plans/02-controllers.md section 3.
"""

from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services import student_service


async def list_students(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    hostel: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    page: int = 1,
    size: int = 20,
    sort: str = "created_at",
    order: str = "desc",
) -> PaginatedStudents:
    return await student_service.list_students(
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


async def get_student(db: AsyncSession, student_id: str) -> StudentDetailSchema:
    return await student_service.get_student(db, student_id)


async def map_student_id(
    db: AsyncSession,
    student_id: str,
    body: MappingCreateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    return await student_service.map_student_id(db, student_id, body, current_user=current_user)


async def update_mapping(
    db: AsyncSession,
    student_id: str,
    body: MappingUpdateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    return await student_service.update_mapping(db, student_id, body, current_user=current_user)


async def update_student_profile(
    db: AsyncSession,
    student_id: str,
    body: StudentProfileUpdateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    return await student_service.update_student_profile(db, student_id, body, current_user=current_user)


async def import_mapping_csv(
    db: AsyncSession,
    csv_file: UploadFile,
    *,
    current_user: UserSchema,
) -> ImportResultSchema:
    return await student_service.import_mapping_csv(db, csv_file, current_user=current_user)


async def export_students(
    db: AsyncSession,
    *,
    export_format: str = "csv",
    status_filter: str | None = None,
    hostel: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[bytes, str, str]:
    return await student_service.export_students(
        db,
        export_format=export_format,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
        sort=sort,
        order=order,
    )
