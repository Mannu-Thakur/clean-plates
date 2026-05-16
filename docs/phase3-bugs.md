# Phase 3 — Bugs & Issues Re-Verification Report

**Re-verified on:** 2026-05-17  
**Audited against:** `01-models.md`, `02-controllers.md`, `03-routes.md`, `05-schemas.md`, `06-phase-wise-plan.md`

---

## Verification Summary

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| BUG-1 | 🔴 Critical | `POST /{device_id}/restart` route missing | ✅ **FIXED** |
| BUG-2 | 🟠 High | `penalty_threshold_grams` bad config key | ✅ **FIXED** |
| BUG-3 | 🟠 High | `MappingCreateSchema.device_id` undocumented + equality check | ✅ **FIXED** |
| BUG-4 | 🟡 Medium | `resolve_warning` orphans pending escalation records | ✅ **FIXED** |
| BUG-5 | 🟡 Medium | `bulk_sync` race condition inflates error count | ✅ **FIXED** |
| BUG-6 | 🟢 Low | `app/schemas/rules.py` not created | ✅ **FIXED** |
| BUG-7 | 🟢 Low | `models/__init__.py` missing Phase 3 model imports | ✅ **FIXED** |

**Result: All 7 bugs are resolved. Phase 3 is clean. ✅**

---

## Detailed Re-Verification

---

### BUG-1 — `POST /{device_id}/restart` ✅ FIXED

**Verified in:** `app/routers/devices.py` (lines 104–111), `app/controllers/device_controller.py` (lines 75–81), `app/services/device_service.py` (lines 292–311)

All three layers are present and correctly wired:

```python
# routers/devices.py — Route registered ✅
@router.post("/{device_id}/restart", response_model=MessageSchema)
async def restart_service(device_id: UUID, current_user=..., db=...):
    await device_controller.restart_service(db, str(device_id), current_user=current_user)
    return MessageSchema(message="Restart command sent")

# controllers/device_controller.py — Dispatch stub ✅
async def restart_service(db, device_id, *, current_user) -> None:
    await device_service.restart_service(db, device_id, current_user=current_user)

# services/device_service.py — Service implementation ✅
async def restart_service(db, device_id, *, current_user=None) -> None:
    device = await _get_device_or_404(db, device_id)
    if device.status == "decommissioned":
        raise HTTPException(409, "Cannot restart a decommissioned device")
    await audit_service.log(db, event_type="device.restart_requested", ...)
    # metadata={"delivery": "stubbed_until_phase_4"} — correctly stubbed for Phase 4 ARQ
```

The old incorrect `# The restart route is intentionally deferred to Phase 4` comment has been removed. ✅

---

### BUG-2 — `penalty_threshold_grams` bad config key ✅ FIXED

**Verified in:** `app/services/waste_service.py` (lines 124–132)

```python
async def _classify_severity(db: AsyncSession, weight_grams: float) -> str:
    thresholds = await config_service.get_config(db, "thresholds")
    warning_threshold = float(thresholds.get("warning_threshold_grams") or 100.0)
    high_threshold    = float(thresholds.get("waste_threshold_grams") or 150.0)  # ✅ correct key
    if weight_grams >= high_threshold:
        return "high"
    if weight_grams >= warning_threshold:
        return "warning"
    return "normal"
```

- `penalty_threshold_grams` → replaced with `waste_threshold_grams` ✅
- Default changed from 200.0 → 150.0 (matches `ThresholdSchema` default) ✅
- Now fully configurable via the config API ✅

---

### BUG-3 — `MappingCreateSchema.device_id` + undocumented equality check ✅ FIXED

**Verified in:** `app/schemas/students.py` (lines 24–43), `app/services/student_service.py` (lines 317–357)

**Schema fix — `device_id` field removed:**
```python
class MappingCreateSchema(BaseModel):
    # device_id: str  ← REMOVED ✅
    name: str = Field(min_length=1, max_length=150)
    roll_number: str = Field(min_length=1, max_length=50)
    branch: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1, le=4)
    hostel: str | None = ...
    room_number: str | None = ...
    email: EmailStr | None = None
```

**Service fix — equality check removed, `device_id` taken from student record:**
```python
async def map_student_id(db, student_id, body, *, current_user):
    student = await _get_student_or_404(db, student_id)
    await _ensure_card_not_mapped_to_other(db, student.device_id, student.id)  # uses student.device_id ✅
    # ...
    if mapping is None:
        mapping = StudentMappingModel(
            student_id=student.id,
            device_id=student.device_id,   # ✅ denormalized from student record, not from body
            mapped_by=current_user.id,
            **body.model_dump(),
        )
    else:
        for field, value in body.model_dump().items():
            setattr(mapping, field, value)
        mapping.device_id = student.device_id   # ✅ always synced from student record
        mapping.mapped_by = current_user.id
```

The old `if body.device_id != student.device_id: raise HTTPException(400, ...)` guard is gone. ✅

---

### BUG-4 — `resolve_warning` orphans pending escalation records ✅ FIXED

**Verified in:** `app/services/warning_service.py` (lines 339–355)

```python
async def resolve_warning(db, warning_id, body, *, current_user):
    warning = await _get_warning_or_404(db, warning_id)
    if warning.status == "resolved":
        return                               # idempotent ✅
    if warning.status == "converted_to_penalty":
        raise HTTPException(409, "Converted warnings cannot be resolved")  # ✅
    if warning.status == "escalated":
        raise HTTPException(                 # ✅ NEW GUARD — prevents orphaned escalations
            status_code=status.HTTP_409_CONFLICT,
            detail="Escalated warnings must be resolved via the escalation review endpoint",
        )
    # ... proceed to resolve
```

Attempting to resolve an `escalated` warning now returns HTTP 409 with a clear message directing the caller to `POST /escalations/{id}/review`. ✅

---

### BUG-5 — `bulk_sync` concurrent duplicate counted as error ✅ FIXED

**Verified in:** `app/services/waste_service.py` (lines 312–323)

```python
except HTTPException as exc:
    if exc.status_code == status.HTTP_409_CONFLICT:
        skipped += 1   # ✅ concurrent duplicate now counted as skipped, not error
    else:
        errors.append({
            "index": index,
            "device_serial": payload.device_serial,
            "student_device_id": payload.student_device_id,
            "error": exc.detail,
        })
```

Only genuine non-409 HTTP errors (e.g., 404 device-not-found) are appended to `errors[]`. Race-condition duplicates are correctly absorbed into `skipped`. ✅

---

### BUG-6 — `app/schemas/rules.py` not created ✅ FIXED

**Verified:** File `app/schemas/rules.py` exists (5,032 bytes, 201 lines).

Contains all schemas required by `05-schemas.md §6`:

| Schema | Present |
|--------|---------|
| `ConditionSchema` | ✅ |
| `ConditionGroupSchema` | ✅ |
| `TimeConstraintSchema` | ✅ |
| `ScopeSchema` | ✅ |
| `ActionSchema` | ✅ |
| `RuleCreateSchema` | ✅ |
| `RuleUpdateSchema` | ✅ |
| `RuleSchema` (with `from_attributes=True`) | ✅ |
| `TestPayloadSchema` | ✅ |
| `TestResultSchema` | ✅ |
| `SimulationResultSchema` | ✅ |
| `RuleExecutionSchema` (with `from_attributes=True`) | ✅ |
| `FieldOptionSchema` | ✅ |
| `ChainNodeSchema`, `ChainEdgeSchema`, `ChainDataSchema` | ✅ |
| `OperatorOptionSchema`, `ActionOptionSchema` | ✅ |
| `PaginatedRules`, `PaginatedExecutions` | ✅ |

**Bonus — L2-audit-fix implemented:** `RuleCreateSchema` and `RuleUpdateSchema` both include the `@model_validator` that rejects contradictory `classify_student` actions:
```python
def _validate_actions(actions):
    classifications = {
        action.params.get("status")
        for action in actions
        if action.type == "classify_student" and action.params.get("status") is not None
    }
    if len(classifications) > 1:
        raise ValueError("actions cannot contain contradictory classify_student statuses")
```

---

### BUG-7 — `models/__init__.py` missing Phase 3 imports ✅ FIXED

**Verified in:** `app/models/__init__.py` (lines 16–18)

```python
from app.models.rule import RuleExecutionModel, RuleModel       # ✅
from app.models.warning import EscalationModel, PenaltyModel, WarningModel  # ✅
from app.models.waste import WasteEntryModel                    # ✅

__all__ = [
    ...
    "RuleModel", "RuleExecutionModel",        # ✅
    "WasteEntryModel",                        # ✅
    "WarningModel", "EscalationModel", "PenaltyModel",  # ✅
]
```

All Phase 3 models are registered in `__all__` and imported at module level so Alembic's `env.py` discovers every table via `Base.metadata`. ✅

---

## Phase 3 Final Status

> **All 7 reported bugs are confirmed fixed. Phase 3 implementation is fully compliant with documentation.**

The codebase is ready to proceed to **Phase 4** (Rule Engine CRUD + evaluation pipeline).

### Phase 4 Readiness Checklist

| Prerequisite | Status |
|---|---|
| `POST /devices/{id}/restart` route + stub registered | ✅ Ready for ARQ wiring |
| `app/schemas/rules.py` with all rule schemas | ✅ Ready for rule routes |
| `RuleModel` and `RuleExecutionModel` in DB (migration 003) | ✅ Tables exist |
| `models/__init__.py` imports Phase 3 models for Alembic | ✅ |
| `waste_threshold_grams` config key usable from rule conditions | ✅ |
| Escalation lifecycle integrity enforced | ✅ |
