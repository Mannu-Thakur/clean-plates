# CleanPlates Final Technical Audit Report

This report presents the findings of a rigorous line-by-line technical audit of the CleanPlates implementation plans, including a cross-reference verification between the backend architectures and frontend UI specifications (`docs/praposed-imp/pages/`). The objective was to verify the robustness of the architecture, identify unpatched logical or structural vulnerabilities, and ensure that previously reported issues were successfully resolved.

## 🔴 High Severity Issues (Architectural Breaking Points & Data Corruption)

### 1. Implicit Student Creation Missing in ML Ingestion
* **Location:** `02-controllers.md` (§4 WasteController & §15 MLIngestionController)
* **Description:** The `create_waste_entry` and `bulk_sync` functions resolve `student_device_id` to `student_id` via a database lookup. However, if a new Raspberry Pi edge device scans a new or unregistered RFID card, no `StudentModel` record exists. The system will fail the lookup and reject the entry, completely breaking the "ID-first mapping" architectural workflow where cards should be mapped by admins later.
* **Remediation:** Modify `WasteController` to automatically insert a new `StudentModel` record with the unknown `device_id` and a default `status='green'` if the database lookup fails. This allows the waste entry to be successfully saved, and the admin can map the identity via `map_student_id` later.

### 2. Staged Restore SQLite WAL Corruption
* **Location:** `06-phase-wise-plan.md` (Phase 8, M3-fix) & `07-project-structure.md`
* **Description:** The backup restore process securely extracts backups to `staging_restore.db` and relies on `entrypoint.sh` to overwrite `database.db` on restart. Because SQLite operates in Write-Ahead Log (WAL) mode, replacing the main `.db` file while leaving the old `.db-wal` and `.db-shm` files on disk will cause SQLite to attempt replaying old transactions against the new database file. This results in catastrophic database corruption.
* **Remediation:** Update `entrypoint.sh` to explicitly execute `rm -f database.db-wal database.db-shm` simultaneously with the replacement of `database.db`.

### 3. Concurrency Bug on Denormalized Counters
* **Location:** `02-controllers.md` (§5 WarningController) & `app/engine/action_executor.py`
* **Description:** Both `warning_service.create_warning` and `action_executor.increase_penalty` increment `student.warning_count` and `penalty_count`. Under high concurrency (e.g., bulk ML sync triggering multiple rules for the same student simultaneously), standard ORM increments (`student.count += 1; commit()`) will result in lost updates due to Python-level race conditions.
* **Remediation:** All counter increments must utilize SQL-level atomic updates instead of ORM memory updates: 
  `await db.execute(update(StudentModel).where(id=student_id).values(warning_count=StudentModel.warning_count + 1))`

### 4. Conflict Between Rule Engine `classify_student` and Aggregation Service
* **Location:** `08-rule-engine.md` (ActionExecutor) & `02-controllers.md` (§16 AggregationService)
* **Description:** The rule engine can explicitly set a student's status via the `classify_student` action (e.g., escalating them to `red`). However, the scheduled `run_hourly_aggregation` computes status purely from `avg_waste_grams` and will overwrite the rule engine's manual classification back to `green` if their average is numerically low.
* **Remediation:** Introduce an `is_status_manual` boolean flag on the `StudentModel`. The `update_student_status` aggregation job must skip students where this flag is `True`, ensuring that manual or rule-based classifications persist.

### 5. Rate Limiting on ML Image Uploads Blocks Offline Recovery
* **Location:** `04-middlewares.md` (§5 RateLimitMiddleware)
* **Description:** The `/ml/*` endpoint group is rate-limited to 1,000 requests per minute per `device_id`. If an edge device has been offline for several days, it may queue thousands of plate images locally. Uploading these sequentially via `POST /ml/upload-image` when connection is restored will quickly trigger a `429 Too Many Requests` limit, halting the offline data recovery completely.
* **Remediation:** Exempt `/ml/upload-image` from the standard ML rate limit, significantly increase the limit, or provide a bulk-image-upload route (ZIP extraction) to process recovery queues efficiently.

### 6. Student Creation Omission during CSV Import
* **Location:** `02-controllers.md` (§3 StudentController) & `05-students-list.md`
* **Description:** The `import_mapping_csv` function is designed to bulk map `device_id` to student details. However, if an admin uploads a CSV containing `device_id`s that the edge devices haven't scanned yet, the system will fail to insert the mapping due to Foreign Key constraints (since the parent `StudentModel` record doesn't exist).
* **Remediation:** `import_mapping_csv` must automatically create `StudentModel` stubs for any `device_id` found in the CSV that doesn't already exist in the database before inserting the mappings.

---

## 🟡 Moderate Severity Issues (Logical Gaps & Performance Risks)

### 1. Timezone Handling in Scheduled Reports
* **Location:** `06-phase-wise-plan.md` (Phase 6, ReportWorker)
* **Description:** `ReportScheduleModel` stores `time_of_day` (e.g., "08:00"). If the ARQ worker computes the `next_run` datetime using UTC, a report scheduled by an admin in India for 08:00 IST will incorrectly execute at 08:00 UTC (13:30 IST).
* **Remediation:** The `next_run` calculation within `report_service.py` must lookup the institution's timezone (`config_service.get_config("institution")["timezone"]`), construct a localized datetime object, and then convert it to UTC for the ARQ scheduler.

### 2. Rule Engine Chaining to Deleted Rules
* **Location:** `02-controllers.md` (§6 RuleController) & `08-rule-engine.md`
* **Description:** `RuleModel.chain_to_rule_id` links rules together for sequential evaluation. If the target rule is soft-deleted (`is_deleted=true`) or deactivated (`active=false`), the engine might encounter a `NoneType` exception or fail the entire execution chain.
* **Remediation:** `RuleEngineService` must gracefully halt rule chains if a targeted rule is deleted or inactive. Furthermore, `RuleController.delete_rule` should warn admins if the rule they are deleting is the target of an active chain.

### 3. Stuck Background Jobs Recovery
* **Location:** `01-models.md` (§16 ReportModel & §21 BackupModel)
* **Description:** If the ARQ worker container crashes or restarts while a report or backup is in the `generating` or `creating` status, that status will remain stuck in the database indefinitely, cluttering the UI.
* **Remediation:** Implement an `on_startup` hook in the ARQ worker settings that queries for any `ReportModel` or `BackupModel` stuck in intermediate states and resets them to `failed`.

### 4. Missing System Dependencies for PDF Generation
* **Location:** `07-project-structure.md` & `06-phase-wise-plan.md`
* **Description:** The plan utilizes `WeasyPrint` for converting HTML templates to PDFs. However, WeasyPrint requires specific OS-level C-libraries that are not mentioned in the `Dockerfile`.
* **Remediation:** Explicitly add the necessary dependencies to the Dockerfile installation steps: 
  `apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`.

### 5. Notification Delivery Status Endpoint Mismatch
* **Location:** `09-notifications.md` (UI Spec) vs `03-routes.md` (Backend)
* **Description:** The UI specification expects to call `GET /api/v1/notifications/{id}/delivery` to fetch tracking info. However, the backend bundles this data into the `GET /{notif_id}` detail endpoint and does not define a separate `/delivery` route.
* **Remediation:** Add the `/delivery` route to `03-routes.md` and the controller, or update the frontend spec to read the delivery array directly from the `get_notification` detail response.

### 6. Audit Log Filtering Query Parameters Missing
* **Location:** `14-audit-log.md` (UI Spec) vs `03-routes.md` (Backend)
* **Description:** The UI heavily relies on filtering audit logs via `?resource=config` or `?event_type=rule.created`. The backend route definitions do not explicitly list `resource` or `event_type` as supported query parameters for `/audit`.
* **Remediation:** Ensure `list_events` in `AuditController` accepts and processes `resource_type` and `event_type` query parameters.

### 7. Student Mapping Route Parameter Mismatch
* **Location:** `05-students-list.md` (UI Spec) vs `03-routes.md` (Backend)
* **Description:** The UI specification mistakenly expects to use `POST /api/v1/students/{deviceId}/map`. The backend correctly enforces `POST /api/v1/students/{student_id}/map` requiring the UUID.
* **Remediation:** Update the frontend documentation and API client to pass `student.id` instead of `student.device_id` in the URL path.

---

## 🔵 Medium/Low Severity Issues (Best Practices)

### 1. File Upload Size Restrictions
* **Location:** `02-controllers.md` (§13 SettingsController & §15 MLIngestionController)
* **Description:** FastAPI `UploadFile` spools files larger than 1MB to disk. Without proper size checks, malicious users could upload massive files (e.g., 5GB dummy images) to `/ml/upload-image` or `/settings/appearance/logo`, causing an application-level Denial of Service (DoS) in environments lacking reverse-proxy limits.
* **Remediation:** Explicitly implement a `Content-Length` header check and byte-read bounds limit inside the upload controllers prior to processing or saving the file.

### 2. Action Executor Priority Clarification
* **Location:** `08-rule-engine.md`
* **Description:** While `ActionExecutor` executes actions in a sorted priority order, it does not stop contradictory actions from occurring if an admin misconfigures a rule (e.g., attempting to set a student to both `green` and `red` simultaneously).
* **Remediation:** Add validation to `RuleCreateSchema` or `RuleController` that rejects rule definitions containing mutually exclusive actions of the exact same type.

---

## ✅ Reverified Patches (Confirmed Resolved)

During the audit, the following previously implemented "fixes" (designated by `-fix` suffixes in the documentation) were reviewed and confirmed to be correctly integrated:

* **P1-fix:** `asyncio.to_thread` added for bcrypt hashing to prevent blocking the ASGI event loop.
* **P2-fix:** `await db.commit()` applied before `arq_pool.enqueue_job` to prevent race conditions where ARQ queries uncommitted data.
* **M3-fix / M9-fix:** Staged DB restores via `restart.lock` to prevent split-brain container writes, and `VACUUM INTO` for safe SQLite WAL backups.
* **F8-fix:** `db_session_factory()` explicitly initiated inside ARQ workers instead of `Depends`.
* **L3-fix:** `student.warning_count` and `penalty_count` drift reconciliation explicitly verified in `aggregation_service.update_student_status`.
* **M4-fix:** Infinite loop protection (recursive rule chaining `depth > 3` rejection) confirmed in `RuleEngineService`.
* **B4-fix / M7-Global:** `ConfigDict(from_attributes=True)` is enforced on all response schemas ensuring safe SQLAlchemy ORM parsing.
