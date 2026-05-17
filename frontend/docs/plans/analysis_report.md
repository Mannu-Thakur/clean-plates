# Frontend Implementation Plans — Verified Analysis & Fix Report (v2)

This report was produced by cross-referencing every plan file **line-by-line** against the **live FastAPI source code** (`app/routers/`, `app/main.py`). The original v1 report contained significant errors — many "confirmed issues" were already correct in the current plan files. All claims below are verified against actual file contents.

---

## Summary Table

| Plan File | Real Issues Remaining | Original Report False Positives |
|-----------|----------------------|----------------------------------|
| `01-foundation-design-system.md` | 0 | 2 (both already correct in plan) |
| `02-dashboard-and-monitoring.md` | 0 | 0 |
| `03-analytics-and-students.md` | 6 real issues | 3 false positives |
| `04-warnings-and-rules.md` | 3 real issues | 3 false positives |
| `05-notifications-reports-devices.md` | 0 | 0 |
| `06-config-settings-audit.md` | 5 real issues | 5 false positives |

---

## File 1: `01-foundation-design-system.md`

### ✅ NO ISSUES — Plan is Correct

**Original Issue A (FALSE POSITIVE):** The report claimed `min-height: 100vh` needed to be changed to `100dvh`.
**Verified:** Plan line 149 already reads `min-height: 100dvh;` with the correct comment. No fix needed.

**Original Issue B (IMPLEMENTATION NOTE, NOT A BUG):** DataTable generic typing.
**Verified:** The `DataTable.svelte` component has not been implemented yet. The plan description at line 367 (`rows: Array<Record<string, unknown>>`) is a prop-spec placeholder in a prose block. The implementation instruction to use `<script lang="ts" generics="T extends Record<string, unknown>">` is valid engineering guidance for implementation time — it is not a bug in the plan document itself.

---

## File 2: `02-dashboard-and-monitoring.md`

### ✅ NO ISSUES — Plan is Correct

**WebSocket URL:** `app/main.py` line 157 confirms `app.include_router(ws_router)` with **no** `/api/v1` prefix. `ws.py` uses `prefix="/ws"`. Plan correctly specifies `ws://host/ws/dashboard` and `ws://host/ws/monitoring`. ✅

**ChartCard expand:** Valid implementation-time caution, not a plan bug.

---

## File 3: `03-analytics-and-students.md`

### ❌ FALSE POSITIVES FROM ORIGINAL REPORT

The following issues were claimed but are **already correct** in the plan:

- **Heatmap (original Issue A):** Plan line 106–107 already states `GET /api/v1/analytics/trends?type=daily_pattern` and documents client-side 7×24 grid derivation explicitly. ✅
- **`/import-mapping` (original Issue B):** Plan line 204 already reads `POST /api/v1/students/import-mapping`. Plan line 236 also reads `api.upload('/students/import-mapping', 'csv_file', file)`. ✅
- **`/improvement` (original Issue C):** Plan line 340 already reads `GET /api/v1/students/{id}/improvement`. ✅

---

### ✅ CONFIRMED — Issue 1: Analytics filter param names wrong (Line 52)

**Evidence:** `app/routers/analytics.py` `analytics_filters` dependency uses:
```python
date_from: date | None = Query(default=None)
date_to:   date | None = Query(default=None)
```
Plan line 52 shows:
```
GET /api/v1/analytics/overview?period=...&start_date=...&end_date=...&branch=...
```
**`start_date` and `end_date` do not exist.** The correct parameter names are `date_from` and `date_to`.

**Fix:** Replace `start_date=` with `date_from=` and `end_date=` with `date_to=` on line 52 and all similar analytics API call examples.

---

### ✅ CONFIRMED — Issue 2: `/analytics/branch-comparison` does not exist (Lines 77–83)

**Evidence:** `app/routers/analytics.py` has no `/branch-comparison` endpoint. All endpoints: `/overview`, `/trends`, `/peaks`, `/meal-distribution`, `/food-waste-distribution`, `/top-waste-contributors`, `/improvement-tracking`, `/sustainability`.

**Fix:** Remove Tab 3 "Branch Comparison" API call `GET /api/v1/analytics/branch-comparison`. Replace with: derive branch breakdown client-side from `GET /api/v1/analytics/overview` filtered per branch, or note this tab is not supported by the current backend.

---

### ✅ CONFIRMED — Issue 3: `/analytics/sustainability-scores` wrong name (Line 89)

**Evidence:** Backend endpoint is `@router.get("/sustainability", ...)` — no hyphen, no `-scores` suffix.

**Fix:** Plan line 89: Change `GET /api/v1/analytics/sustainability-scores` → `GET /api/v1/analytics/sustainability`.

---

### ✅ CONFIRMED — Issue 4: Manual warn endpoint wrong (Lines 247, 342)

**Evidence:** `app/routers/students.py` line 225:
```python
@router.post("/{student_id}/warnings", ...)
```
Plan line 247 (Quick Warn Modal): `POST /api/v1/students/{id}/warn`
Plan line 342 (Profile API table): `POST /api/v1/students/{id}/warn`

**`/warn` does not exist.** The correct endpoint is `/warnings`.

**Fix:** Change both occurrences of `/students/{id}/warn` → `/students/{id}/warnings`.

---

### ✅ CONFIRMED — Issue 5: Bulk warn endpoint wrong (Line 343)

**Evidence:** `app/routers/students.py` line 116:
```python
@router.post("/bulk/warn", ...)
```
Plan line 343: `POST /api/v1/students/{id}/bulk-warn`

**`/{id}/bulk-warn` does not exist.** Bulk warn is a collection endpoint (no student ID in path).

**Fix:** Plan line 343: Change `POST /api/v1/students/{id}/bulk-warn` → `POST /api/v1/students/bulk/warn` with `BulkWarnSchema` body (list of student IDs + level + message).

---

### ✅ CONFIRMED — Issue 6: `StudentFilters` interface has non-existent fields (Lines 296–304)

**Evidence:** `app/routers/students.py` `list_students` query params are: `status_filter` (alias `status`), `hostel`, `branch`, `year`, `page`, `size`, `sort`, `order`. There is **no `search` param and no `warning_status` param**.

Plan lines 296–304:
```typescript
export interface StudentFilters {
  search?: string;           // ← does not exist in backend
  status?: string;
  branch?: string;
  warning_status?: 'active' | 'resolved';  // ← does not exist in backend
  page?: number;
  size?: number;
  sort?: string;
}
```
Also, the FilterBar description at line 188 shows `[Warning▼]` filter — this maps to no backend param.

**Fix:** Remove `search` and `warning_status` from `StudentFilters`. Add `hostel?: string` and `year?: number`. Update FilterBar to remove the warning status filter (replace with `hostel` filter). The `[Search]` input can remain as a **client-side** filter only, or be removed.

---

## File 4: `04-warnings-and-rules.md`

### ❌ FALSE POSITIVES FROM ORIGINAL REPORT

The following issues were claimed but are **already correct** in the plan:

- **Resolve endpoint (original Issue A):** Plan line 39 already reads `PATCH /api/v1/warnings/{id}/resolve with ResolveWarningSchema body`. ✅
- **Rule toggle (original Issue C):** Plan line 233 already reads `POST /api/v1/rules/{id}/toggle with body {"active": true/false}`. ✅
- **Simulate query params (original Issue D):** Plan line 432 already reads `POST /api/v1/rules/{id}/simulate?date_from={start_date}&date_to={end_date}` (dates as query params, not body). ✅

---

### ✅ CONFIRMED — Issue 1: `GET /api/v1/warnings/{id}` does not exist (Line 36)

**Evidence:** `app/routers/warnings.py` has no `GET /{warning_id}` single-item endpoint. The router has list, stats, export, bulk-resolve, resolve, escalate, and apply-penalty — but no individual warning GET by ID.

**Fix:** Remove `GET /api/v1/warnings/{id}` from the API calls table (line 36). The warning detail modal should use data already present in the list row (passed as a prop), or fetch via `GET /api/v1/students/{student_id}/warnings` and filter client-side.

---

### ✅ CONFIRMED — Issue 2: Create Manual Warning wrong endpoint (Line 110)

**Evidence:** There is **no `POST /api/v1/warnings`** endpoint in `warnings.py`. Warnings are created via:
```python
# students.py line 225
@router.post("/{student_id}/warnings", ...)
```

Plan line 110 (Create Manual Warning Modal submit): `Submit → POST /api/v1/warnings`

**Fix:** Change line 110 to: `Submit → POST /api/v1/students/{student_id}/warnings` — the student must be selected first via the autocomplete, then their ID is used in the path.

---

### ✅ CONFIRMED — Issue 3: Create Direct Penalty wrong endpoint (Line 138)

**Evidence:** `app/routers/warnings.py` has no `POST /warnings/penalties`. Direct penalty creation is:
```python
# students.py line 242
@router.post("/{student_id}/penalties", ...)
```

Plan line 138 (Create Direct Penalty Modal submit): `Submit → POST /api/v1/warnings/penalties`

**Fix:** Change line 138 to: `Submit → POST /api/v1/students/{student_id}/penalties` (student must be selected via autocomplete, their ID used in path).

---

## File 5: `05-notifications-reports-devices.md`

### ✅ NO ISSUES — Plan is Correct

All API endpoints cross-reference correctly against the live backend routers.

---

## File 6: `06-config-settings-audit.md`

### ❌ FALSE POSITIVES FROM ORIGINAL REPORT

The following issues were claimed but are **already correct** in the plan:

- **`/config/all` (original Issue A):** Plan lines 48–58 already include a `> **Note:**` block documenting `Promise.all()` approach explicitly. ✅
- **Maintenance table paths (original Issue B):** Plan API calls table lines 233–235 already shows `clear-cache`, `optimize-db`, `system-info` all with the correct `/maintenance/` prefix. ✅
- **Backup restore (original Issue C):** Plan line 223 already reads `POST /api/v1/settings/backups/restore (file upload, field: backup_file)`. Plan line 320 already reads `api.upload('/settings/backups/restore', 'backup_file', file)`. ✅
- **User deactivate (original Issue D):** Plan line 215 already reads `POST /api/v1/settings/users/{id}/deactivate`. Plan line 251 already documents deactivate logic correctly. ✅
- **Logo upload path (original Issue E):** Plan line 70 and line 227 already read `POST /api/v1/settings/appearance/logo`. ✅

---

### ✅ CONFIRMED — Issue 1: Config reset path has wrong segment order (Line 142)

**Evidence:** `app/routers/config.py` line 129:
```python
@router.post("/reset/{section}", ...)
```
Full path: `POST /api/v1/config/reset/{section}`

Plan line 142: `POST /api/v1/config/{section}/reset` — **segment order is reversed**.

**Fix:** Change line 142 to `POST /api/v1/config/reset/{section}`.

---

### ✅ CONFIRMED — Issue 2: System info endpoint missing `/maintenance/` prefix in prose (Line 378)

**Evidence:** `app/routers/settings.py` line 184:
```python
@router.get("/maintenance/system-info", ...)
```
Plan line 378 (Maintenance tab prose, outside the API table): `Fetch from GET /api/v1/settings/system-info on tab open.`

**Fix:** Change line 378 to `Fetch from GET /api/v1/settings/maintenance/system-info on tab open.`

---

### ✅ CONFIRMED — Issue 3: Optimize DB endpoint wrong in prose (Line 392)

**Evidence:** `app/routers/settings.py` line 176:
```python
@router.post("/maintenance/optimize-db", ...)
```
Plan line 392 (Database Optimization section): `"Optimize Database" button → POST /api/v1/settings/optimize`

**Fix:** Change line 392 to `POST /api/v1/settings/maintenance/optimize-db`.

---

### ✅ CONFIRMED — Issue 4: Settings store uses `deleteUser` (Lines 560–564)

**Evidence:** Backend has no DELETE endpoint for users. Only `POST /settings/users/{id}/deactivate` exists.

Plan lines 560–564 (settings store definition):
```typescript
// Actions: fetchUsers(), createUser(data), updateUser(id, data), deleteUser(id), ...
```
`deleteUser` does not correspond to any backend endpoint.

**Fix:** Change `deleteUser(id)` to `deactivateUser(id)` in the store actions comment.

---

### ✅ CONFIRMED — Issue 5: Verification checklist uses "Delete user" (Line 612)

**Evidence:** No DELETE endpoint for users exists.

Plan line 612: `- [ ] Delete user: confirm dialog, cannot delete self`

**Fix:** Change to `- [ ] Deactivate user: confirm dialog with warning, cannot deactivate own account or last super_admin`

---

## Corrected Fixes Table

The following are the **actual corrections required** in plan files as of this verification:

| # | File | Line(s) | Change Required |
|---|------|---------|-----------------|
| 1 | `03-analytics-and-students.md` | 52 | `start_date=` → `date_from=`, `end_date=` → `date_to=` |
| 2 | `03-analytics-and-students.md` | 77–83 | Remove `GET /analytics/branch-comparison` — endpoint does not exist; note tab is unsupported |
| 3 | `03-analytics-and-students.md` | 89 | `GET /analytics/sustainability-scores` → `GET /analytics/sustainability` |
| 4 | `03-analytics-and-students.md` | 247, 342 | `/students/{id}/warn` → `/students/{id}/warnings` |
| 5 | `03-analytics-and-students.md` | 343 | `/students/{id}/bulk-warn` → `/students/bulk/warn` (no student ID in path) |
| 6 | `03-analytics-and-students.md` | 296–304 | Remove `search` and `warning_status` from `StudentFilters`; add `hostel?: string`, `year?: number` |
| 7 | `04-warnings-and-rules.md` | 36 | Remove `GET /api/v1/warnings/{id}` — endpoint does not exist |
| 8 | `04-warnings-and-rules.md` | 110 | `POST /api/v1/warnings` → `POST /api/v1/students/{student_id}/warnings` |
| 9 | `04-warnings-and-rules.md` | 138 | `POST /api/v1/warnings/penalties` → `POST /api/v1/students/{student_id}/penalties` |
| 10 | `06-config-settings-audit.md` | 142 | `POST /config/{section}/reset` → `POST /config/reset/{section}` |
| 11 | `06-config-settings-audit.md` | 378 | `GET /settings/system-info` → `GET /settings/maintenance/system-info` |
| 12 | `06-config-settings-audit.md` | 392 | `POST /settings/optimize` → `POST /settings/maintenance/optimize-db` |
| 13 | `06-config-settings-audit.md` | 560–564 | `deleteUser(id)` → `deactivateUser(id)` in store actions comment |
| 14 | `06-config-settings-audit.md` | 612 | `Delete user` → `Deactivate user` in verification checklist |

---

## Verified Correct Items (No Changes Needed)

1. **WebSocket URLs** — `ws://host/ws/dashboard` and `ws://host/ws/monitoring` are correct (WS router mounted without `/api/v1` prefix in `main.py` line 157).
2. **`min-height: 100dvh`** — already correct in `01` plan line 149.
3. **Heatmap tab** — already uses `trends?type=daily_pattern` with client-side grid derivation in `03` plan lines 106–131.
4. **`/students/import-mapping`** — already correct in `03` plan lines 204, 236.
5. **`/students/{id}/improvement`** — already correct in `03` plan line 340.
6. **`PATCH /warnings/{id}/resolve`** — already correct in `04` plan line 39.
7. **`POST /rules/{id}/toggle`** — already correct in `04` plan line 233.
8. **Simulate via query params** — already correct in `04` plan line 432.
9. **`Promise.all()` for config load** — already documented in `06` plan lines 48–58.
10. **Maintenance endpoint paths (API table)** — already correct in `06` plan lines 233–235.
11. **Backup restore as file upload** — already correct in `06` plan lines 223, 320.
12. **User deactivate (not delete)** — already correct in `06` plan lines 215, 251.
13. **Logo upload at `/settings/appearance/logo`** — already correct in `06` plan lines 70, 227.
14. **`api.ts` FormData handling** — `client.ts` already omits `Content-Type` for FormData uploads.
15. **Static uploads** — `http://host/static/uploads/{filename}` served without auth via `StaticFiles` mount at `main.py` line 115.
