"""
Warning service - warning, escalation, and penalty lifecycle.

Ref: docs/plans/02-controllers.md section 5.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from datetime import UTC, date, datetime
from typing import Any
from xml.sax.saxutils import escape

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import StudentMappingModel, StudentModel
from app.models.warning import EscalationModel, PenaltyModel, WarningModel
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
    StudentWarningsSchema,
    WarningCreateSchema,
    WarningSchema,
    WarningSummarySchema,
)
from app.services import audit_service
from app.services.rule_event_service import dispatch_rule_event


_UNRESOLVED_WARNING_STATUSES = {"active", "escalated"}


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


async def _get_student_or_404(db: AsyncSession, student_id: str) -> StudentModel:
    student = await db.get(StudentModel, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


async def _get_warning_or_404(db: AsyncSession, warning_id: str) -> WarningModel:
    warning = await db.get(WarningModel, warning_id)
    if warning is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warning not found")
    return warning


async def _get_penalty_or_404(db: AsyncSession, penalty_id: str) -> PenaltyModel:
    penalty = await db.get(PenaltyModel, penalty_id)
    if penalty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Penalty not found")
    return penalty


async def _get_escalation_or_404(db: AsyncSession, escalation_id: str) -> EscalationModel:
    escalation = await db.get(EscalationModel, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    return escalation


async def _student_name(db: AsyncSession, student_id: str) -> str | None:
    result = await db.execute(select(StudentMappingModel.name).where(StudentMappingModel.student_id == student_id))
    return result.scalar_one_or_none()


async def _warning_schema(db: AsyncSession, warning: WarningModel) -> WarningSchema:
    return WarningSchema(
        id=warning.id,
        student_id=warning.student_id,
        level=warning.level,
        reason=warning.reason,
        status=warning.status,
        rule_id=warning.rule_id,
        issued_by=warning.issued_by,
        email_sent=warning.email_sent,
        created_at=warning.created_at,
        student_name=await _student_name(db, warning.student_id),
    )


async def _penalty_schema(db: AsyncSession, penalty: PenaltyModel) -> PenaltySchema:
    return PenaltySchema(
        id=penalty.id,
        student_id=penalty.student_id,
        points=penalty.points,
        reason=penalty.reason,
        status=penalty.status,
        warning_id=penalty.warning_id,
        issued_by=penalty.issued_by,
        email_sent=penalty.email_sent,
        created_at=penalty.created_at,
        student_name=await _student_name(db, penalty.student_id),
    )


def _warning_state(warning: WarningModel) -> dict:
    return {
        "id": warning.id,
        "student_id": warning.student_id,
        "level": warning.level,
        "reason": warning.reason,
        "status": warning.status,
        "rule_id": warning.rule_id,
        "waste_entry_id": warning.waste_entry_id,
    }


def _penalty_state(penalty: PenaltyModel) -> dict:
    return {
        "id": penalty.id,
        "student_id": penalty.student_id,
        "points": penalty.points,
        "reason": penalty.reason,
        "status": penalty.status,
        "warning_id": penalty.warning_id,
        "rule_id": penalty.rule_id,
    }


async def _dispatch_warning_event(
    db: AsyncSession,
    warning: WarningModel,
    *,
    arq_pool: ArqRedis | None,
    event_depth: int,
) -> None:
    count_result = await db.execute(select(StudentModel.warning_count).where(StudentModel.id == warning.student_id))
    current_warning_count = int(count_result.scalar_one_or_none() or 0)
    await dispatch_rule_event(
        arq_pool,
        "warning_issued",
        {
            "student_id": warning.student_id,
            "warning_id": warning.id,
            "level": warning.level,
            "reason": warning.reason,
            "rule_id": warning.rule_id,
            "waste_entry_id": warning.waste_entry_id,
            "current_warning_count": current_warning_count,
        },
        depth=event_depth,
    )


async def _dispatch_penalty_event(
    penalty: PenaltyModel,
    *,
    arq_pool: ArqRedis | None,
    event_depth: int,
) -> None:
    await dispatch_rule_event(
        arq_pool,
        "penalty_applied",
        {
            "student_id": penalty.student_id,
            "penalty_id": penalty.id,
            "points": penalty.points,
            "warning_id": penalty.warning_id,
            "rule_id": penalty.rule_id,
        },
        depth=event_depth,
    )


async def _increment_warning_count(db: AsyncSession, student_id: str) -> None:
    await db.execute(
        update(StudentModel).where(StudentModel.id == student_id).values(warning_count=StudentModel.warning_count + 1)
    )


async def _decrement_warning_count(db: AsyncSession, student_id: str) -> None:
    await db.execute(
        update(StudentModel)
        .where(StudentModel.id == student_id)
        .values(
            warning_count=case(
                (StudentModel.warning_count > 0, StudentModel.warning_count - 1),
                else_=0,
            )
        )
    )


async def _increment_penalty_count(db: AsyncSession, student_id: str) -> None:
    await db.execute(
        update(StudentModel).where(StudentModel.id == student_id).values(penalty_count=StudentModel.penalty_count + 1)
    )


async def _decrement_penalty_count(db: AsyncSession, student_id: str) -> None:
    await db.execute(
        update(StudentModel)
        .where(StudentModel.id == student_id)
        .values(
            penalty_count=case(
                (StudentModel.penalty_count > 0, StudentModel.penalty_count - 1),
                else_=0,
            )
        )
    )


async def _refresh_student_status(db: AsyncSession, student_id: str) -> None:
    from app.services import aggregation_service

    await aggregation_service.update_student_status(db, student_id)


def _apply_warning_filters(
    stmt,
    *,
    status_filter: str | None = None,
    level: str | None = None,
    student_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if status_filter:
        stmt = stmt.where(WarningModel.status == status_filter.strip().lower())
    if level:
        stmt = stmt.where(WarningModel.level == level.strip().lower())
    if student_id:
        stmt = stmt.where(WarningModel.student_id == student_id)
    if date_from:
        stmt = stmt.where(func.date(WarningModel.created_at) >= date_from.isoformat())
    if date_to:
        stmt = stmt.where(func.date(WarningModel.created_at) <= date_to.isoformat())
    return stmt


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
    page = max(page, 1)
    size = min(max(size, 1), 100)

    count_stmt = _apply_warning_filters(
        select(func.count(WarningModel.id)),
        status_filter=status_filter,
        level=level,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
    )
    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)

    stmt = _apply_warning_filters(
        select(WarningModel),
        status_filter=status_filter,
        level=level,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
    )
    stmt = stmt.order_by(WarningModel.created_at.desc(), WarningModel.id.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    warnings = result.scalars().all()
    return PaginatedWarnings(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[await _warning_schema(db, warning) for warning in warnings],
    )


async def get_warning_stats(db: AsyncSession) -> WarningSummarySchema:
    total_warnings = await db.scalar(select(func.count(WarningModel.id)))
    active_warnings = await db.scalar(
        select(func.count(WarningModel.id)).where(WarningModel.status.in_(_UNRESOLVED_WARNING_STATUSES))
    )
    pending_escalations = await db.scalar(
        select(func.count(EscalationModel.id)).where(EscalationModel.status == "pending")
    )
    total_penalties = await db.scalar(select(func.count(PenaltyModel.id)))
    return WarningSummarySchema(
        total_warnings=int(total_warnings or 0),
        active_warnings=int(active_warnings or 0),
        pending_escalations=int(pending_escalations or 0),
        total_penalties=int(total_penalties or 0),
    )


async def create_warning(
    db: AsyncSession,
    student_id: str,
    body: WarningCreateSchema,
    *,
    current_user: UserSchema | None = None,
    arq_pool: ArqRedis | None = None,
    event_depth: int = 1,
) -> WarningSchema:
    await _get_student_or_404(db, student_id)
    warning = WarningModel(
        student_id=student_id,
        level=body.level,
        reason=body.reason,
        rule_id=str(body.rule_id) if body.rule_id else None,
        waste_entry_id=str(body.waste_entry_id) if body.waste_entry_id else None,
        issued_by=current_user.id if current_user else None,
        status="active",
        email_sent=False,
    )
    db.add(warning)
    await db.flush()
    await _increment_warning_count(db, student_id)
    await _refresh_student_status(db, student_id)

    if body.send_email:
        pass  # TODO: Wire EmailService in Phase 6

    await audit_service.log(
        db,
        event_type="warning.issued",
        action="create",
        resource_type="warning",
        resource_id=warning.id,
        summary=f"Issued {warning.level} warning",
        after_state=_warning_state(warning),
        **_audit_user(current_user),
    )
    # P2-fix: commit before enqueue so the ARQ worker (separate process)
    # can read the warning row when it picks up the job immediately.
    await db.commit()
    await _dispatch_warning_event(db, warning, arq_pool=arq_pool, event_depth=event_depth)
    return await _warning_schema(db, warning)


async def resolve_warning(
    db: AsyncSession,
    warning_id: str,
    body: ResolveWarningSchema,
    *,
    current_user: UserSchema,
) -> None:
    warning = await _get_warning_or_404(db, warning_id)
    if warning.status == "resolved":
        return
    if warning.status == "converted_to_penalty":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Converted warnings cannot be resolved")
    if warning.status == "escalated":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Escalated warnings must be resolved via the escalation review endpoint",
        )

    before = _warning_state(warning)
    warning.status = "resolved"
    warning.resolved_by = current_user.id
    warning.resolved_at = _utcnow()
    warning.resolution_note = body.resolution_note
    await db.flush()
    await _decrement_warning_count(db, warning.student_id)
    await _refresh_student_status(db, warning.student_id)

    await audit_service.log(
        db,
        event_type="warning.resolved",
        action="resolve",
        resource_type="warning",
        resource_id=warning.id,
        summary="Resolved warning",
        before_state=before,
        after_state=_warning_state(warning),
        **_audit_user(current_user),
    )


async def escalate_warning(
    db: AsyncSession,
    warning_id: str,
    body: EscalateWarningSchema,
    *,
    current_user: UserSchema | None = None,
) -> EscalationSchema:
    warning = await _get_warning_or_404(db, warning_id)
    if warning.status not in {"active", "escalated"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active warnings can be escalated")

    existing_result = await db.execute(
        select(EscalationModel).where(
            EscalationModel.warning_id == warning.id,
            EscalationModel.status == "pending",
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return EscalationSchema.model_validate(existing)

    before = _warning_state(warning)
    escalation = EscalationModel(
        warning_id=warning.id,
        student_id=warning.student_id,
        reason=body.reason,
        escalated_to_role=body.escalated_to_role,
        escalated_by=current_user.id if current_user else None,
        status="pending",
    )
    db.add(escalation)
    warning.status = "escalated"
    await db.flush()
    await _refresh_student_status(db, warning.student_id)

    await audit_service.log(
        db,
        event_type="warning.escalated",
        action="escalate",
        resource_type="warning",
        resource_id=warning.id,
        summary=f"Escalated warning to {body.escalated_to_role}",
        before_state=before,
        after_state=_warning_state(warning),
        metadata={"escalation_id": escalation.id},
        **_audit_user(current_user),
    )
    return EscalationSchema.model_validate(escalation)


def _penalty_points_for_warning(warning: WarningModel) -> int:
    return {"level_1": 1, "level_2": 2, "level_3": 3}.get(warning.level, 1)


async def apply_penalty(
    db: AsyncSession,
    warning_id: str,
    *,
    current_user: UserSchema | None = None,
    arq_pool: ArqRedis | None = None,
    event_depth: int = 1,
) -> PenaltySchema:
    warning = await _get_warning_or_404(db, warning_id)
    if warning.status == "converted_to_penalty":
        existing_result = await db.execute(select(PenaltyModel).where(PenaltyModel.warning_id == warning.id))
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return await _penalty_schema(db, existing)
    if warning.status not in {"active", "escalated"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only active or escalated warnings can become penalties"
        )

    before_warning = _warning_state(warning)
    penalty = PenaltyModel(
        student_id=warning.student_id,
        points=_penalty_points_for_warning(warning),
        reason=f"Penalty applied from warning: {warning.reason}",
        warning_id=warning.id,
        rule_id=warning.rule_id,
        issued_by=current_user.id if current_user else None,
        status="active",
        email_sent=False,
    )
    db.add(penalty)
    warning.status = "converted_to_penalty"
    await db.flush()
    await _decrement_warning_count(db, warning.student_id)
    await _increment_penalty_count(db, warning.student_id)
    await _refresh_student_status(db, warning.student_id)

    await audit_service.log(
        db,
        event_type="penalty.applied",
        action="create",
        resource_type="penalty",
        resource_id=penalty.id,
        summary="Converted warning to penalty",
        before_state=before_warning,
        after_state=_penalty_state(penalty),
        **_audit_user(current_user),
    )
    # P2-fix: commit before enqueue so the ARQ worker can read the penalty row.
    await db.commit()
    await _dispatch_penalty_event(penalty, arq_pool=arq_pool, event_depth=event_depth)
    return await _penalty_schema(db, penalty)


async def create_penalty_direct(
    db: AsyncSession,
    student_id: str,
    body: PenaltyCreateSchema,
    *,
    current_user: UserSchema | None = None,
    arq_pool: ArqRedis | None = None,
    event_depth: int = 1,
) -> PenaltySchema:
    await _get_student_or_404(db, student_id)
    penalty = PenaltyModel(
        student_id=student_id,
        points=body.points,
        reason=body.reason,
        warning_id=None,
        rule_id=str(body.rule_id) if body.rule_id else None,
        issued_by=current_user.id if current_user else None,
        status="active",
        email_sent=False,
    )
    db.add(penalty)
    await db.flush()
    await _increment_penalty_count(db, student_id)
    await _refresh_student_status(db, student_id)

    if body.send_email:
        pass  # TODO: Wire EmailService in Phase 6

    await audit_service.log(
        db,
        event_type="penalty.applied",
        action="create",
        resource_type="penalty",
        resource_id=penalty.id,
        summary="Applied direct penalty",
        after_state=_penalty_state(penalty),
        **_audit_user(current_user),
    )
    # P2-fix: commit before enqueue so the ARQ worker can read the penalty row.
    await db.commit()
    await _dispatch_penalty_event(penalty, arq_pool=arq_pool, event_depth=event_depth)
    return await _penalty_schema(db, penalty)


async def bulk_resolve(
    db: AsyncSession,
    body: BulkResolveSchema,
    *,
    current_user: UserSchema,
) -> None:
    for warning_id in body.warning_ids:
        await resolve_warning(
            db,
            str(warning_id),
            ResolveWarningSchema(resolution_note=body.resolution_note),
            current_user=current_user,
        )


def _apply_penalty_filters(
    stmt,
    *,
    status_filter: str | None = None,
    student_id: str | None = None,
):
    if status_filter:
        stmt = stmt.where(PenaltyModel.status == status_filter.strip().lower())
    if student_id:
        stmt = stmt.where(PenaltyModel.student_id == student_id)
    return stmt


async def list_penalties(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    student_id: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedPenalties:
    page = max(page, 1)
    size = min(max(size, 1), 100)

    count_stmt = _apply_penalty_filters(
        select(func.count(PenaltyModel.id)), status_filter=status_filter, student_id=student_id
    )
    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)

    stmt = _apply_penalty_filters(select(PenaltyModel), status_filter=status_filter, student_id=student_id)
    stmt = stmt.order_by(PenaltyModel.created_at.desc(), PenaltyModel.id.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    penalties = result.scalars().all()

    return PaginatedPenalties(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[await _penalty_schema(db, penalty) for penalty in penalties],
    )


async def revoke_penalty(
    db: AsyncSession,
    penalty_id: str,
    body: RevokePenaltySchema,
    *,
    current_user: UserSchema,
) -> None:
    penalty = await _get_penalty_or_404(db, penalty_id)
    if penalty.status == "revoked":
        return

    before = _penalty_state(penalty)
    penalty.status = "revoked"
    penalty.revoked_by = current_user.id
    penalty.revoke_reason = body.reason
    penalty.revoked_at = _utcnow()
    await db.flush()
    await _decrement_penalty_count(db, penalty.student_id)
    await _refresh_student_status(db, penalty.student_id)

    await audit_service.log(
        db,
        event_type="penalty.revoked",
        action="revoke",
        resource_type="penalty",
        resource_id=penalty.id,
        summary="Revoked penalty",
        before_state=before,
        after_state=_penalty_state(penalty),
        **_audit_user(current_user),
    )


async def list_escalations(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
) -> list[EscalationSchema]:
    stmt = select(EscalationModel)
    if status_filter:
        stmt = stmt.where(EscalationModel.status == status_filter.strip().lower())
    stmt = stmt.order_by(EscalationModel.created_at.desc(), EscalationModel.id.asc())
    result = await db.execute(stmt)
    return [EscalationSchema.model_validate(row) for row in result.scalars().all()]


async def review_escalation(
    db: AsyncSession,
    escalation_id: str,
    body: ReviewEscalationSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
    event_depth: int = 1,
) -> None:
    escalation = await _get_escalation_or_404(db, escalation_id)
    if escalation.status != "pending":
        return

    escalation.status = body.decision
    escalation.reviewed_by = current_user.id
    escalation.review_note = body.review_note
    escalation.reviewed_at = _utcnow()
    await db.flush()

    if body.decision == "approved":
        await apply_penalty(
            db,
            escalation.warning_id,
            current_user=current_user,
            arq_pool=arq_pool,
            event_depth=event_depth,
        )
    else:
        warning = await _get_warning_or_404(db, escalation.warning_id)
        before = _warning_state(warning)
        warning.status = "resolved"
        warning.resolved_by = current_user.id
        warning.resolved_at = _utcnow()
        warning.resolution_note = body.review_note or "Escalation rejected"
        await db.flush()
        await _decrement_warning_count(db, warning.student_id)
        await _refresh_student_status(db, warning.student_id)
        await audit_service.log(
            db,
            event_type="warning.resolved",
            action="resolve",
            resource_type="warning",
            resource_id=warning.id,
            summary="Resolved warning via rejected escalation",
            before_state=before,
            after_state=_warning_state(warning),
            **_audit_user(current_user),
        )

    await audit_service.log(
        db,
        event_type="escalation.reviewed",
        action="review",
        resource_type="escalation",
        resource_id=escalation.id,
        summary=f"Escalation {body.decision}",
        metadata={"decision": body.decision},
        **_audit_user(current_user),
    )


async def get_student_warnings(db: AsyncSession, student_id: str) -> StudentWarningsSchema:
    await _get_student_or_404(db, student_id)
    warning_result = await db.execute(
        select(WarningModel).where(WarningModel.student_id == student_id).order_by(WarningModel.created_at.desc())
    )
    penalty_result = await db.execute(
        select(PenaltyModel).where(PenaltyModel.student_id == student_id).order_by(PenaltyModel.created_at.desc())
    )
    return StudentWarningsSchema(
        warnings=[await _warning_schema(db, warning) for warning in warning_result.scalars().all()],
        penalties=[await _penalty_schema(db, penalty) for penalty in penalty_result.scalars().all()],
    )


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


def _xlsx_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    all_rows = [headers, *rows]
    sheet_rows = []
    for row_idx, row in enumerate(all_rows, start=1):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            ref = f"{_xlsx_col_name(col_idx)}{row_idx}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

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
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Warnings" sheetId="1" r:id="rId1"/></sheets>'
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
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f"<sheetData>{''.join(sheet_rows)}</sheetData></worksheet>",
        )
    return output.getvalue()


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
    stmt = _apply_warning_filters(
        select(WarningModel),
        status_filter=status_filter,
        level=level,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
    )
    stmt = stmt.order_by(WarningModel.created_at.desc(), WarningModel.id.asc())
    result = await db.execute(stmt)
    warnings = [await _warning_schema(db, warning) for warning in result.scalars().all()]

    headers = ["warning_id", "student_id", "student_name", "level", "reason", "status", "created_at", "email_sent"]
    rows = [
        [
            item.id,
            item.student_id,
            item.student_name or "",
            item.level,
            item.reason,
            item.status,
            item.created_at.isoformat(sep=" ", timespec="seconds"),
            "yes" if item.email_sent else "no",
        ]
        for item in warnings
    ]
    timestamp = _utcnow().strftime("%Y%m%d_%H%M%S")
    normalized_format = export_format.strip().lower()
    if normalized_format == "csv":
        return _csv_bytes(headers, rows), "text/csv; charset=utf-8", f"warnings_{timestamp}.csv"
    if normalized_format in {"excel", "xlsx"}:
        return (
            _xlsx_bytes(headers, rows),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            f"warnings_{timestamp}.xlsx",
        )
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="format must be 'csv' or 'excel'")
