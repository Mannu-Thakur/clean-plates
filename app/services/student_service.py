"""
Student service - list, map, update, import, and export student records.

Ref: docs/plans/02-controllers.md section 3.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from xml.sax.saxutils import escape

from arq.connections import ArqRedis
from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import StudentMappingModel, StudentModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.schemas.students import (
    BulkWarnSchema,
    FoodBreakdownItemSchema,
    FoodBreakdownSchema,
    ImprovementPointSchema,
    ImprovementSchema,
    ImportResultSchema,
    MappingCreateSchema,
    MappingImportRowSchema,
    MappingUpdateSchema,
    MealPatternItemSchema,
    MealPatternSchema,
    PaginatedStudents,
    StudentDetailSchema,
    StudentProfileUpdateSchema,
    StudentSchema,
    TimelinePointSchema,
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
from app.services import audit_service
from app.services import config_service


_CARD_CONFLICT_MESSAGE = (
    "This card ID is already mapped to another student. Deactivate that student first or use a different card ID."
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


def _period_date_range(period: str) -> tuple[str, date | None, date | None]:
    today = _utcnow().date()
    normalized = (period or "30d").strip().lower()
    if normalized == "today":
        return normalized, today, today
    if normalized == "yesterday":
        yesterday = today - timedelta(days=1)
        return normalized, yesterday, yesterday
    if normalized == "7d":
        return normalized, today - timedelta(days=6), today
    if normalized == "30d":
        return normalized, today - timedelta(days=29), today
    if normalized == "semester":
        return normalized, today - timedelta(days=180), today
    if normalized == "all":
        return normalized, None, None
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="period must be one of today, yesterday, 7d, 30d, semester, all",
    )


def _entry_in_range(entry: WasteEntryModel, start_date: date | None, end_date: date | None) -> bool:
    if start_date and entry.session_date < start_date:
        return False
    if end_date and entry.session_date > end_date:
        return False
    return True


async def _student_entries_for_period(
    db: AsyncSession,
    student_id: str,
    period: str,
) -> tuple[str, date | None, date | None, list[WasteEntryModel]]:
    normalized, start_date, end_date = _period_date_range(period)
    stmt = select(WasteEntryModel).where(WasteEntryModel.student_id == student_id)
    if start_date:
        stmt = stmt.where(WasteEntryModel.session_date >= start_date)
    if end_date:
        stmt = stmt.where(WasteEntryModel.session_date <= end_date)
    stmt = stmt.order_by(WasteEntryModel.session_date.asc(), WasteEntryModel.timestamp.asc())
    result = await db.execute(stmt)
    return normalized, start_date, end_date, list(result.scalars().all())


def _food_totals(entries: list[WasteEntryModel]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for entry in entries:
        items = entry.food_items or []
        if not items:
            continue
        for item in items:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            grams = item.get("grams")
            totals[name] += float(grams if grams is not None else 0.0)
    return dict(totals)


def _meal_totals(entries: list[WasteEntryModel]) -> dict[str, tuple[float, int]]:
    totals: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
    for entry in entries:
        bucket = totals[entry.meal_type]
        bucket[0] = float(bucket[0]) + float(entry.weight_grams)
        bucket[1] = int(bucket[1]) + 1
    return {meal: (float(total), int(count)) for meal, (total, count) in totals.items()}


def _improvement_pct(previous_avg: float, current_avg: float) -> float | None:
    if previous_avg <= 0:
        return None
    return round(((previous_avg - current_avg) / previous_avg) * 100.0, 2)


async def _get_student_or_404(db: AsyncSession, student_id: str) -> StudentModel:
    result = await db.execute(
        select(StudentModel).options(selectinload(StudentModel.mapping)).where(StudentModel.id == student_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


async def _get_student_by_device_id(db: AsyncSession, device_id: str) -> StudentModel | None:
    result = await db.execute(
        select(StudentModel).options(selectinload(StudentModel.mapping)).where(StudentModel.device_id == device_id)
    )
    return result.scalar_one_or_none()


async def _get_mapping_by_student_id(db: AsyncSession, student_id: str) -> StudentMappingModel | None:
    result = await db.execute(select(StudentMappingModel).where(StudentMappingModel.student_id == student_id))
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
    await _ensure_card_not_mapped_to_other(db, student.device_id, student.id)
    mapping = await _get_mapping_by_student_id(db, student.id)
    before = _mapping_state(mapping)

    if mapping is None:
        mapping = StudentMappingModel(
            student_id=student.id,
            device_id=student.device_id,
            mapped_by=current_user.id,
            **body.model_dump(),
        )
        db.add(mapping)
    else:
        for field, value in body.model_dump().items():
            setattr(mapping, field, value)
        mapping.device_id = student.device_id
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
            mapping_data = MappingImportRowSchema.model_validate(payload)
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


async def bulk_warn(
    db: AsyncSession,
    body: BulkWarnSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> None:
    from app.services import warning_service

    for student_id in body.student_ids:
        await warning_service.create_warning(
            db,
            str(student_id),
            WarningCreateSchema(level=body.level, reason=body.reason, send_email=body.send_email),
            current_user=current_user,
            arq_pool=arq_pool,
        )


async def get_student_stats(db: AsyncSession, student_id: str, period: str = "30d") -> WasteStatsSchema:
    student = await _get_student_or_404(db, student_id)
    normalized, start_date, end_date, entries = await _student_entries_for_period(db, student_id, period)
    total = sum(float(entry.weight_grams) for entry in entries)
    count = len(entries)
    avg = total / count if count else 0.0

    food_totals = _food_totals(entries)
    most_wasted_food = max(food_totals.items(), key=lambda item: item[1])[0] if food_totals else None
    meal_totals = _meal_totals(entries)
    peak_meal = max(meal_totals.items(), key=lambda item: item[1][0])[0] if meal_totals else None

    improvement = None
    if start_date and end_date:
        window_days = (end_date - start_date).days + 1
        previous_start = start_date - timedelta(days=window_days)
        previous_end = start_date - timedelta(days=1)
        previous_result = await db.execute(
            select(func.avg(WasteEntryModel.weight_grams)).where(
                WasteEntryModel.student_id == student_id,
                WasteEntryModel.session_date >= previous_start,
                WasteEntryModel.session_date <= previous_end,
            )
        )
        previous_avg = float(previous_result.scalar_one() or 0.0)
        improvement = _improvement_pct(previous_avg, avg)

    return WasteStatsSchema(
        student_id=student_id,
        period=normalized,
        total_waste_grams=round(total, 2),
        avg_waste_grams=round(avg, 2),
        entry_count=count,
        most_wasted_food=most_wasted_food,
        peak_meal=peak_meal,
        sustainability_score=student.sustainability_score,
        improvement_pct=improvement,
    )


async def get_student_timeline(db: AsyncSession, student_id: str, period: str = "30d") -> TimelineSchema:
    await _get_student_or_404(db, student_id)
    normalized, _, _, entries = await _student_entries_for_period(db, student_id, period)
    totals: dict[date, list[float | int]] = defaultdict(lambda: [0.0, 0])
    for entry in entries:
        bucket = totals[entry.session_date]
        bucket[0] = float(bucket[0]) + float(entry.weight_grams)
        bucket[1] = int(bucket[1]) + 1

    thresholds = await config_service.get_config(db, "thresholds")
    threshold_grams = float(thresholds.get("warning_threshold_grams") or 100.0)
    return TimelineSchema(
        student_id=student_id,
        period=normalized,
        threshold_grams=threshold_grams,
        data=[
            TimelinePointSchema(date=day, total_grams=round(float(total), 2), entry_count=int(count))
            for day, (total, count) in sorted(totals.items(), key=lambda item: item[0])
        ],
    )


async def get_food_breakdown(db: AsyncSession, student_id: str, period: str = "30d") -> FoodBreakdownSchema:
    await _get_student_or_404(db, student_id)
    _, _, _, entries = await _student_entries_for_period(db, student_id, period)
    totals = _food_totals(entries)
    total_food_grams = sum(totals.values())
    items = [
        FoodBreakdownItemSchema(
            food_name=name,
            total_grams=round(grams, 2),
            percentage=round((grams / total_food_grams) * 100.0, 2) if total_food_grams else 0.0,
        )
        for name, grams in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]
    return FoodBreakdownSchema(student_id=student_id, data=items)


async def get_meal_pattern(db: AsyncSession, student_id: str, period: str = "30d") -> MealPatternSchema:
    await _get_student_or_404(db, student_id)
    _, _, _, entries = await _student_entries_for_period(db, student_id, period)
    meal_totals = _meal_totals(entries)
    return MealPatternSchema(
        student_id=student_id,
        data=[
            MealPatternItemSchema(
                meal_type=meal,
                avg_grams=round(total / count, 2) if count else 0.0,
                entry_count=count,
            )
            for meal, (total, count) in sorted(meal_totals.items(), key=lambda item: item[0])
        ],
    )


async def get_improvement_trend(db: AsyncSession, student_id: str) -> ImprovementSchema:
    await _get_student_or_404(db, student_id)
    today = _utcnow().date()
    start = today - timedelta(days=55)
    result = await db.execute(
        select(WasteEntryModel).where(
            WasteEntryModel.student_id == student_id,
            WasteEntryModel.session_date >= start,
            WasteEntryModel.session_date <= today,
        )
    )
    entries = list(result.scalars().all())

    buckets: list[tuple[date, date]] = []
    for offset in range(7, -1, -1):
        week_end = today - timedelta(days=offset * 7)
        week_start = week_end - timedelta(days=6)
        buckets.append((week_start, week_end))

    points: list[ImprovementPointSchema] = []
    previous_avg = 0.0
    for week_start, week_end in buckets:
        week_entries = [entry for entry in entries if _entry_in_range(entry, week_start, week_end)]
        avg = sum(float(entry.weight_grams) for entry in week_entries) / len(week_entries) if week_entries else 0.0
        improvement = _improvement_pct(previous_avg, avg) if previous_avg else 0.0
        points.append(
            ImprovementPointSchema(
                week_label=f"{week_start.isoformat()} to {week_end.isoformat()}",
                avg_grams=round(avg, 2),
                improvement_pct=round(improvement or 0.0, 2),
            )
        )
        previous_avg = avg

    current_improvement = points[-1].improvement_pct if points else 0.0
    if current_improvement > 5:
        direction = "improving"
    elif current_improvement < -5:
        direction = "worsening"
    else:
        direction = "stable"

    return ImprovementSchema(
        student_id=student_id,
        current_improvement_pct=current_improvement,
        direction=direction,
        data=points,
    )


async def get_student_history(
    db: AsyncSession,
    student_id: str,
    *,
    page: int = 1,
    size: int = 20,
) -> PaginatedEntries:
    from app.services import waste_service

    await _get_student_or_404(db, student_id)
    return await waste_service.list_entries(db, student_id=student_id, page=page, size=size)


async def get_student_warnings(db: AsyncSession, student_id: str) -> StudentWarningsSchema:
    from app.services import warning_service

    return await warning_service.get_student_warnings(db, student_id)


async def create_warning(
    db: AsyncSession,
    student_id: str,
    body: WarningCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> WarningSchema:
    from app.services import warning_service

    return await warning_service.create_warning(db, student_id, body, current_user=current_user, arq_pool=arq_pool)


async def create_penalty_direct(
    db: AsyncSession,
    student_id: str,
    body: PenaltyCreateSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> PenaltySchema:
    from app.services import warning_service

    return await warning_service.create_penalty_direct(
        db, student_id, body, current_user=current_user, arq_pool=arq_pool
    )
