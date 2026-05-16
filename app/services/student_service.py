"""
Student service - list, map, update, import, and export student records.

Ref: docs/plans/02-controllers.md section 3.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from datetime import UTC, datetime
from typing import Any
from xml.sax.saxutils import escape

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import StudentMappingModel, StudentModel
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
from app.services import audit_service


_CARD_CONFLICT_MESSAGE = (
    "This card ID is already mapped to another student. "
    "Deactivate that student first or use a different card ID."
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _audit_user(current_user: UserSchema | None) -> dict:
    if current_user is None:
        return {}
    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_role": current_user.role,
    }


def _mapping_state(mapping: StudentMappingModel | None) -> dict | None:
    if mapping is None:
        return None
    return {
        "student_id": mapping.student_id,
        "device_id": mapping.device_id,
        "name": mapping.name,
        "roll_number": mapping.roll_number,
        "branch": mapping.branch,
        "year": mapping.year,
        "hostel": mapping.hostel,
        "room_number": mapping.room_number,
        "email": mapping.email,
        "mapped_by": mapping.mapped_by,
    }


def _student_state(student: StudentModel) -> dict:
    return {
        "id": student.id,
        "device_id": student.device_id,
        "status": student.status,
        "is_status_manual": student.is_status_manual,
        "sustainability_score": student.sustainability_score,
        "warning_count": student.warning_count,
        "penalty_count": student.penalty_count,
        "total_waste_grams": student.total_waste_grams,
        "avg_waste_grams": student.avg_waste_grams,
        "is_active": student.is_active,
    }


def _student_schema(student: StudentModel) -> StudentSchema:
    return StudentSchema.model_validate(student)


def _student_detail_schema(student: StudentModel) -> StudentDetailSchema:
    return StudentDetailSchema.model_validate(student)


async def _get_student_or_404(db: AsyncSession, student_id: str) -> StudentModel:
    result = await db.execute(
        select(StudentModel)
        .options(selectinload(StudentModel.mapping))
        .where(StudentModel.id == student_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


async def _get_student_by_device_id(db: AsyncSession, device_id: str) -> StudentModel | None:
    result = await db.execute(
        select(StudentModel)
        .options(selectinload(StudentModel.mapping))
        .where(StudentModel.device_id == device_id)
    )
    return result.scalar_one_or_none()


async def _get_mapping_by_student_id(db: AsyncSession, student_id: str) -> StudentMappingModel | None:
    result = await db.execute(
        select(StudentMappingModel).where(StudentMappingModel.student_id == student_id)
    )
    return result.scalar_one_or_none()


async def _ensure_card_not_mapped_to_other(db: AsyncSession, device_id: str, student_id: str) -> None:
    result = await db.execute(
        select(StudentMappingModel).where(
            StudentMappingModel.device_id == device_id,
            StudentMappingModel.student_id != student_id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CARD_CONFLICT_MESSAGE)


def _apply_student_filters(
    stmt,
    *,
    status_filter: str | None = None,
    hostel: str | None = None,
    branch: str | None = None,
    year: int | None = None,
):
    if status_filter:
        stmt = stmt.where(StudentModel.status == status_filter.strip().lower())
    if hostel:
        stmt = stmt.where(StudentMappingModel.hostel == hostel.strip())
    if branch:
        stmt = stmt.where(StudentMappingModel.branch == branch.strip())
    if year is not None:
        stmt = stmt.where(StudentMappingModel.year == year)
    return stmt


def _sort_expression(sort: str, order: str):
    sort_map = {
        "created_at": StudentModel.created_at,
        "status": StudentModel.status,
        "warning_count": StudentModel.warning_count,
        "penalty_count": StudentModel.penalty_count,
        "avg_waste_grams": StudentModel.avg_waste_grams,
        "sustainability_score": StudentModel.sustainability_score,
        "name": StudentMappingModel.name,
        "roll_number": StudentMappingModel.roll_number,
        "branch": StudentMappingModel.branch,
        "year": StudentMappingModel.year,
        "hostel": StudentMappingModel.hostel,
    }
    column = sort_map.get((sort or "created_at").strip(), StudentModel.created_at)
    return column.desc() if (order or "desc").lower() == "desc" else column.asc()


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
    page = max(page, 1)
    size = min(max(size, 1), 100)

    count_stmt = select(func.count(StudentModel.id)).outerjoin(StudentMappingModel)
    count_stmt = _apply_student_filters(
        count_stmt,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
    )
    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)

    stmt = select(StudentModel).outerjoin(StudentMappingModel).options(selectinload(StudentModel.mapping))
    stmt = _apply_student_filters(
        stmt,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
    )
    stmt = stmt.order_by(_sort_expression(sort, order), StudentModel.id.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    students = result.scalars().all()

    return PaginatedStudents(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[_student_schema(student) for student in students],
    )


async def get_student(db: AsyncSession, student_id: str) -> StudentDetailSchema:
    student = await _get_student_or_404(db, student_id)
    return _student_detail_schema(student)


async def map_student_id(
    db: AsyncSession,
    student_id: str,
    body: MappingCreateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    student = await _get_student_or_404(db, student_id)
    if body.device_id != student.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapping device_id must match the student's card ID",
        )

    await _ensure_card_not_mapped_to_other(db, body.device_id, student.id)
    mapping = await _get_mapping_by_student_id(db, student.id)
    before = _mapping_state(mapping)

    if mapping is None:
        mapping = StudentMappingModel(
            student_id=student.id,
            device_id=body.device_id,
            mapped_by=current_user.id,
            **body.model_dump(exclude={"device_id"}),
        )
        db.add(mapping)
    else:
        for field, value in body.model_dump().items():
            setattr(mapping, field, value)
        mapping.mapped_by = current_user.id

    await db.flush()
    student = await _get_student_or_404(db, student_id)

    await audit_service.log(
        db,
        event_type="student.mapped",
        action="create" if before is None else "update",
        resource_type="student",
        resource_id=student.id,
        summary=f"Mapped student card '{student.device_id}'",
        before_state=before,
        after_state=_mapping_state(student.mapping),
        **_audit_user(current_user),
    )
    return _student_schema(student)


async def update_mapping(
    db: AsyncSession,
    student_id: str,
    body: MappingUpdateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    student = await _get_student_or_404(db, student_id)
    mapping = student.mapping
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student mapping not found")

    data = body.model_dump(exclude_unset=True)
    for field in ("name", "roll_number", "branch", "year"):
        if field in data and data[field] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} cannot be null")

    if not data:
        return _student_schema(student)

    before = _mapping_state(mapping)
    for field, value in data.items():
        setattr(mapping, field, value)

    await db.flush()
    student = await _get_student_or_404(db, student_id)

    await audit_service.log(
        db,
        event_type="student.mapping_updated",
        action="update",
        resource_type="student",
        resource_id=student.id,
        summary=f"Updated mapping for card '{student.device_id}'",
        before_state=before,
        after_state=_mapping_state(student.mapping),
        **_audit_user(current_user),
    )
    return _student_schema(student)


async def update_student_profile(
    db: AsyncSession,
    student_id: str,
    body: StudentProfileUpdateSchema,
    *,
    current_user: UserSchema,
) -> StudentSchema:
    student = await _get_student_or_404(db, student_id)
    data = body.model_dump(exclude_unset=True)
    if "is_active" not in data or data["is_active"] is None:
        return _student_schema(student)

    before = _student_state(student)
    student.is_active = data["is_active"]
    await db.flush()
    student = await _get_student_or_404(db, student_id)

    await audit_service.log(
        db,
        event_type="student.profile_updated",
        action="update",
        resource_type="student",
        resource_id=student.id,
        summary=f"Updated active status for card '{student.device_id}'",
        before_state=before,
        after_state=_student_state(student),
        **_audit_user(current_user),
    )
    return _student_schema(student)


def _decode_csv_upload(raw: bytes) -> str:
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file must be text")


def _row_value(row: dict[str, Any], *names: str) -> str | None:
    normalized = {str(key).strip().lower(): value for key, value in row.items() if key is not None}
    for name in names:
        value = normalized.get(name)
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return None


def _row_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "device_id": _row_value(row, "device_id", "card_id", "rfid"),
        "name": _row_value(row, "name", "student_name"),
        "roll_number": _row_value(row, "roll_number", "roll", "roll_no", "roll number"),
        "branch": _row_value(row, "branch", "department"),
        "year": _row_value(row, "year"),
        "hostel": _row_value(row, "hostel", "hostel_name"),
        "room_number": _row_value(row, "room_number", "room", "room_no", "room number"),
        "email": _row_value(row, "email", "email_address"),
    }


def _validation_error_message(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        messages.append(f"{field}: {error['msg']}")
    return "; ".join(messages) or "Invalid row"


async def import_mapping_csv(
    db: AsyncSession,
    csv_file: UploadFile,
    *,
    current_user: UserSchema,
) -> ImportResultSchema:
    filename = csv_file.filename or "mapping.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

    text = _decode_csv_upload(await csv_file.read())
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file has no header row")

    total_rows = 0
    successful = 0
    errors: list[dict] = []
    seen_device_ids: set[str] = set()

    for row_number, row in enumerate(reader, start=2):
        if not any(str(value).strip() for value in row.values() if value is not None):
            continue

        total_rows += 1
        payload = _row_payload(row)
        device_id_for_error = payload.get("device_id")

        try:
            mapping_data = MappingCreateSchema.model_validate(payload)
            if mapping_data.device_id in seen_device_ids:
                raise ValueError("Duplicate device_id in CSV file")
            seen_device_ids.add(mapping_data.device_id)

            student = await _get_student_by_device_id(db, mapping_data.device_id)
            existing_mapping_result = await db.execute(
                select(StudentMappingModel).where(StudentMappingModel.device_id == mapping_data.device_id)
            )
            existing_mapping = existing_mapping_result.scalar_one_or_none()
            if existing_mapping is not None and (student is None or existing_mapping.student_id != student.id):
                raise ValueError(_CARD_CONFLICT_MESSAGE)

            if student is None:
                student = StudentModel(device_id=mapping_data.device_id)
                db.add(student)
                await db.flush()

            mapping = await _get_mapping_by_student_id(db, student.id)
            if mapping is None:
                db.add(
                    StudentMappingModel(
                        student_id=student.id,
                        device_id=mapping_data.device_id,
                        mapped_by=current_user.id,
                        **mapping_data.model_dump(exclude={"device_id"}),
                    )
                )
            else:
                for field, value in mapping_data.model_dump().items():
                    setattr(mapping, field, value)
                mapping.mapped_by = current_user.id

            successful += 1
        except ValidationError as exc:
            errors.append(
                {
                    "row": row_number,
                    "device_id": device_id_for_error,
                    "error": _validation_error_message(exc),
                }
            )
        except ValueError as exc:
            errors.append({"row": row_number, "device_id": device_id_for_error, "error": str(exc)})

    await db.flush()
    failed = len(errors)

    await audit_service.log(
        db,
        event_type="student.mapping_imported",
        action="import",
        resource_type="student_mapping",
        summary=f"Imported student mappings from '{filename}'",
        metadata={
            "filename": filename,
            "total_rows": total_rows,
            "successful": successful,
            "failed": failed,
            "errors_preview": errors[:20],
        },
        **_audit_user(current_user),
    )

    return ImportResultSchema(
        total_rows=total_rows,
        successful=successful,
        failed=failed,
        errors=errors,
    )


async def _export_rows(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    hostel: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> list[list[Any]]:
    stmt = select(StudentModel).outerjoin(StudentMappingModel).options(selectinload(StudentModel.mapping))
    stmt = _apply_student_filters(
        stmt,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
    )
    stmt = stmt.order_by(_sort_expression(sort, order), StudentModel.id.asc())
    result = await db.execute(stmt)
    students = result.scalars().all()

    rows: list[list[Any]] = []
    for student in students:
        mapping = student.mapping
        rows.append(
            [
                student.id,
                student.device_id,
                student.status,
                "yes" if student.is_active else "no",
                mapping.name if mapping else "",
                mapping.roll_number if mapping else "",
                mapping.branch if mapping else "",
                mapping.year if mapping else "",
                mapping.hostel if mapping and mapping.hostel else "",
                mapping.room_number if mapping and mapping.room_number else "",
                mapping.email if mapping and mapping.email else "",
                student.warning_count,
                student.penalty_count,
                student.sustainability_score,
                student.avg_waste_grams,
                student.total_waste_grams,
                student.created_at.isoformat(sep=" ", timespec="seconds"),
            ]
        )
    return rows


def _csv_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _xlsx_col_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _xlsx_sheet_xml(headers: list[str], rows: list[list[Any]]) -> str:
    all_rows = [headers, *rows]
    sheet_rows = []
    for row_idx, row in enumerate(all_rows, start=1):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            ref = f"{_xlsx_col_name(col_idx)}{row_idx}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        "</worksheet>"
    )


def _xlsx_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/docProps/core.xml" '
            'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
            'Target="docProps/app.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Students" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        archive.writestr("xl/worksheets/sheet1.xml", _xlsx_sheet_xml(headers, rows))
        archive.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>CleanPlates Student Export</dc:title>"
            "</cp:coreProperties>",
        )
        archive.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            "<Application>CleanPlates</Application>"
            "</Properties>",
        )
    return output.getvalue()


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
    headers = [
        "student_id",
        "device_id",
        "status",
        "is_active",
        "name",
        "roll_number",
        "branch",
        "year",
        "hostel",
        "room_number",
        "email",
        "warning_count",
        "penalty_count",
        "sustainability_score",
        "avg_waste_grams",
        "total_waste_grams",
        "created_at",
    ]
    rows = await _export_rows(
        db,
        status_filter=status_filter,
        hostel=hostel,
        branch=branch,
        year=year,
        sort=sort,
        order=order,
    )

    timestamp = _utcnow().strftime("%Y%m%d_%H%M%S")
    normalized_format = (export_format or "csv").strip().lower()
    if normalized_format == "csv":
        return _csv_bytes(headers, rows), "text/csv; charset=utf-8", f"students_{timestamp}.csv"
    if normalized_format in {"excel", "xlsx"}:
        return (
            _xlsx_bytes(headers, rows),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            f"students_{timestamp}.xlsx",
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="format must be 'csv' or 'excel'")
