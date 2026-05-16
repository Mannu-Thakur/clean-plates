# CleanPlates — Phase-Wise Implementation Plan

**Stack:** FastAPI + SQLAlchemy 2.0 (async) + SQLite + Redis + ARQ + SvelteKit  
**Doc refs:** `01-models.md`, `02-controllers.md`, `03-routes.md`, `04-middlewares.md`, `05-schemas.md`

---

## Phase 1 — Project Scaffold & Foundation
**Duration:** Week 1  
**Goal:** Working FastAPI app skeleton with DB, auth, and dev tooling.

### Files to Create

| File | Section | Task |
|------|---------|------|
| `pyproject.toml` | All deps | Add all dependencies from framework doc |
| `.env.example` | — | All settings from `04-middlewares.md § Pydantic Settings` |
| `app/core/config.py` | `Settings` class | Full settings from `04-middlewares.md § Pydantic Settings` |
| `app/core/database.py` | — | Async SQLAlchemy engine + `AsyncSessionLocal` session factory only — **do NOT** define `get_db_session` here; the dependency lives exclusively in `app/middleware/db.py` |
| `app/core/security.py` | — | `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token` |
| `app/main.py` | — | FastAPI app init + all middleware registration from `04-middlewares.md § Middleware Registration Order` |
| `app/middleware/auth.py` | — | `get_current_user`, `get_current_user_optional`, `get_api_key_device` from `04-middlewares.md §1,§11` |
| `app/middleware/rbac.py` | — | `require_roles`, `require_admin`, `require_write_access` from `04-middlewares.md §2` |
| `app/middleware/logging.py` | — | Request/response structured logging from `04-middlewares.md §3` |
| `app/middleware/error_handler.py` | — | All exception handlers from `04-middlewares.md §7` |
| `app/middleware/rate_limit.py` | — | Redis-backed rate limiter from `04-middlewares.md §5` |
| `app/middleware/security_headers.py` | — | Security headers from `04-middlewares.md §10` |
| `app/middleware/ws_auth.py` | — | WebSocket token auth dependency from `04-middlewares.md §11` — extract `?token=` param, decode JWT, close WS with 4001 on failure |
| `app/middleware/audit.py` | — | `capture_before(model)`, `capture_after(model)` helpers from `04-middlewares.md §6` — used by all service layers that audit |
| `app/middleware/db.py` | — | `get_db_session()` async dependency (yields `AsyncSession`, commits on success, rolls back on error) from `04-middlewares.md §12` — distinct from engine setup in `app/core/database.py` |

### Models to Create (SQLAlchemy)

| Model | File | Ref |
|-------|------|-----|
| `Base` + common mixins | `app/models/base.py` | SQLAlchemy declarative base |
| `UserModel` | `app/models/user.py` | `01-models.md §1` |
| `RefreshTokenModel` | `app/models/user.py` | `01-models.md §2` |
| `RoleModel` | `app/models/role.py` | `01-models.md §23` |
| `ConfigModel` | `app/models/config.py` | `01-models.md §19` |

### Alembic

| Task | File |
|------|------|
| Init alembic | `alembic/` directory |
| Customize for async | `alembic/env.py` — use `run_async_migrations()`; import `AsyncEngine`; import all models |
| First migration | `alembic/versions/001_initial_users.py` — creates `users`, `refresh_tokens`, `roles`, `system_config` tables |
| Seed scripts | `scripts/seed_roles.py` — insert default roles, `scripts/seed_config.py` — default config |

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/auth.py` | All 6 auth routes | `03-routes.md §1` |
| `app/controllers/auth_controller.py` | All 6 auth controller functions | `02-controllers.md §1` |
| `app/services/auth_service.py` | `authenticate`, `issue_tokens`, `refresh_tokens`, `revoke_token`, `request_password_reset`, `reset_password` | `02-controllers.md §1` |
| `app/services/config_service.py` | `get_config`, `set_config`, `reset_section` | `02-controllers.md §11` |
| `app/schemas/auth.py` | All auth schemas | `05-schemas.md §1` |

> **Note (Email Stub — Phase 1):** `auth_service.request_password_reset()` sends a password-reset email. Because `EmailService` is not built until Phase 6, stub this call with `# TODO: Wire EmailService in Phase 6` (same pattern as `WarningService` email stub in Phase 2). The reset token must still be generated and stored; only the email dispatch is deferred.

### Health & Infra

| File | Task |
|------|------|
| `app/routers/health.py` | `GET /health` → returns `{status: ok, version, uptime}` |
| `docker-compose.dev.yml` | FastAPI + Redis services |
| `Dockerfile` | Multi-stage, ARM64-compatible |
| `nginx.conf` | Reverse proxy to port 8000 |

**Deliverable:** `POST /auth/login` works, returns JWT. All middleware active. DB migrations run clean.

---

## Phase 2 — Device & Student Core
**Duration:** Week 2  
**Goal:** Device registration, student creation, student mapping, ML ingestion endpoint.

### Models to Create

| Model | File | Ref |
|-------|------|-----|
| `DeviceModel` | `app/models/device.py` | `01-models.md §3` |
| `DeviceHealthModel` | `app/models/device.py` | `01-models.md §4` |
| `StudentModel` | `app/models/student.py` | `01-models.md §5` |
| `StudentMappingModel` | `app/models/student.py` | `01-models.md §6` |
| `FoodItemModel` | `app/models/food.py` | `01-models.md §7` |
| `AuditEventModel` | `app/models/audit.py` | `01-models.md §20` |

### Alembic Migration
`alembic/versions/002_devices_students.py` — all above tables

> **Note:** `FoodItemModel` created here is referenced by `WasteEntryModel` in Phase 3.

### Seed Scripts
| Script | Content |
|--------|---------|
| `scripts/seed_food_items.py` | Common food items: rice, dal, sabzi, roti, salad, dessert, beverage |

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/devices.py` | All 8 device routes | `03-routes.md §2` |
| `app/controllers/device_controller.py` | All device controller functions | `02-controllers.md §2` |
| `app/services/device_service.py` | All device service functions | `02-controllers.md §2` |
| `app/schemas/devices.py` | All device schemas | `05-schemas.md §2` |
| `app/routers/students.py` | `list_students`, `get_student`, `map_student_id`, `update_mapping`, `update_student_profile`, `import_mapping_csv`, `export_students` | `03-routes.md §3` |
| `app/controllers/student_controller.py` | Same functions (`update_mapping` = PATCH mapping fields; `update_student_profile` = PATCH top-level student fields, bound to `PATCH /{student_id}`) | `02-controllers.md §3` |
| `app/services/student_service.py` | `list_students`, `get_student`, `map_student_id`, `update_mapping`, `update_student_profile`, `import_mapping_csv`, `export_students` | `02-controllers.md §3` |
| `app/schemas/students.py` | `MappingCreateSchema`, `MappingUpdateSchema`, `StudentSchema`, `ImportResultSchema` | `05-schemas.md §3` |

### Audit Integration
`app/services/audit_service.py` — implement `log()` function. Wire into device registration, student mapping.



**Deliverable:** Register device via API, map students via CSV import.

---

## Phase 3 — Waste Entries & Warning System
**Duration:** Week 3  
**Goal:** Waste entry storage, ML ingestion, warning/penalty CRUD, escalation flow.

### Models to Create

| Model | File | Ref |
|-------|------|-----|
| `WasteEntryModel` | `app/models/waste.py` | `01-models.md §8` |
| `WarningModel` | `app/models/warning.py` | `01-models.md §9` |
| `EscalationModel` | `app/models/warning.py` | `01-models.md §10` |
| `PenaltyModel` | `app/models/warning.py` | `01-models.md §11` |
| `RuleModel` | `app/models/rule.py` | `01-models.md §12` |
| `RuleExecutionModel` | `app/models/rule.py` | `01-models.md §13` |

### Alembic Migration
`alembic/versions/003_waste_warnings_rules.py` — creates `rules`, `rule_executions`, `waste_entries`, `warnings`, `escalations`, `penalties` tables.
> **Note:** Rule models are created in this phase to ensure proper Foreign Key constraint creation for `warnings` and `penalties`, avoiding SQLite `ALTER TABLE` limitations.

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/schemas/waste.py` | All waste schemas | `05-schemas.md §4` |
| `app/routers/ml.py` | `POST /ml/detect`, `POST /ml/sync`, `POST /ml/heartbeat` | `03-routes.md §5` |
| `app/controllers/ml_controller.py` | `ingest_detection`, `bulk_ingest`, `ml_heartbeat` | `02-controllers.md §15` |
| `app/routers/waste.py` | All 4 waste routes | `03-routes.md §4` |
| `app/controllers/waste_controller.py` | `create_waste_entry`, `bulk_sync`, `get_entry`, `list_entries`, `get_current_session`, `get_recent_entries` | `02-controllers.md §4` |
| `app/services/waste_service.py` | Same | `02-controllers.md §4` |
| `app/routers/warnings.py` | All warning, penalty, escalation routes (including `GET /export` → `export_warnings`) | `03-routes.md §6` |
| `app/controllers/warning_controller.py` | All warning controller functions including `export_warnings` | `02-controllers.md §5` |
| `app/services/warning_service.py` | All warning service functions | `02-controllers.md §5` |
| `app/schemas/warnings.py` | All warning/penalty/escalation schemas | `05-schemas.md §5` |

### Student Intelligence Routes (analytics part)

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/students.py` | Add: `get_student_stats`, `get_student_timeline`, `get_food_breakdown`, `get_meal_pattern`, `get_improvement_trend`, `get_student_history`, `get_student_warnings`, `bulk_warn`, `create_warning`, `create_penalty_direct` | `03-routes.md §3` |
| `app/controllers/student_controller.py` | Same functions (`create_penalty_direct` ≠ `apply_penalty` — this creates a penalty with no source warning) | `02-controllers.md §3` |

> **Note (Dependencies stubbed):** `WarningService` must stub the email sending logic (e.g., `if send_email: pass # TODO: Wire in Phase 6`) because `EmailService` and ARQ workers are not built until Phases 4 and 6. Similarly, recalculating student status via `aggregation_service` must be stubbed until Phase 5.

**Deliverable:** ML pipeline can push waste entries. Full warning/penalty lifecycle works. Student intelligence page stats computable.

---

## Phase 4 — Rule Engine
**Duration:** Weeks 4–5  
**Goal:** Dynamic rule CRUD, event-based evaluation, action execution.

### Models & DB
*(Rule models `RuleModel` and `RuleExecutionModel` were already created in Phase 3 DB migrations to avoid SQLite FK constraints issues. No new models or migrations required in this phase.)*

### Workers Package Scaffold

> **Note (B4/I1):** Create the `app/workers/` package in this phase — it is the Docker Compose ARQ worker entrypoint. Without `arq_settings.py`, the command `arq app.workers.arq_settings.WorkerSettings` in `docker-compose.yml` will fail immediately.

| File | Task |
|------|------|
| `app/workers/__init__.py` | Empty package init |
| `app/workers/arq_settings.py` | ARQ `WorkerSettings` class — registers all cron jobs; start with `rule_worker` only; expand in Phases 5–6 |
| `app/workers/rule_worker.py` | Subscribe to Redis events via `EventBus` → call `rule_engine_service.evaluate_event` for each event type |

### ARQ Cron Schedule (expand `arq_settings.py` per phase)

| Task Function | Worker File | Frequency | Phase Added |
|--------------|-------------|-----------|-------------|
| `rule_engine_worker` | `rule_worker.py` | Continuous (Redis pub/sub listener) | Phase 4 |
| `run_hourly_aggregation` | `aggregation_worker.py` | Every 60 minutes | Phase 5 |
| `run_daily_aggregation` | `aggregation_worker.py` | Daily at 00:05 UTC | Phase 5 |
| `compute_sustainability_scores` | `aggregation_worker.py` | Daily at 00:15 UTC | Phase 5 |
| `check_device_offline_status` | `aggregation_worker.py` | Every 60 minutes | Phase 5 |
| `execute_scheduled_reports` | `report_worker.py` | Every 5 minutes (checks `next_run`) | Phase 6 |
| `send_scheduled_notifications` | `report_worker.py` | Every 5 minutes (checks `scheduled_at`) | Phase 6 |
| `auto_backup` | `backup_worker.py` | Every 24 hours (per `backup_interval_hours` config) | Phase 8 |
| `purge_old_audit_events` | `backup_worker.py` | Daily at 03:00 UTC (per `audit_retention_days` config) | Phase 8 |

### Core Engine Files

| File | Class/Functions | Ref |
|------|-----------------|-----|
| `app/services/rule_engine_service.py` | `evaluate_event`, `match_conditions`, `execute_actions` | `02-controllers.md §16 Internal` |
| `app/engine/condition_matcher.py` | `match`, `match_numeric`, `match_string`, `match_time_window`, `match_frequency`, `match_trend`, `match_aggregate` | `08-rule-engine.md` |
| `app/engine/action_executor.py` | `execute`, `generate_warning`, `send_email`, `increase_penalty`, `trigger_escalation`, `classify_student`, `create_audit_log` | `08-rule-engine.md` |
| `app/engine/event_bus.py` | `publish(event_type, event_data)`, `subscribe(event_type, handler)` — Redis pub/sub backed | `08-rule-engine.md` |

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/rules.py` | All 15 rule routes | `03-routes.md §7` |
| `app/controllers/rule_controller.py` | All rule controller functions | `02-controllers.md §6` |
| `app/schemas/rules.py` | All rule schemas | `05-schemas.md §6` |
| `app/routers/devices.py` | Add: `restart_service` | `03-routes.md §2` |
| `app/controllers/device_controller.py` | Add: `restart_service` | `02-controllers.md §2` |

### Wire Events
- In `waste_service.create_waste_entry()`: after saving, call `event_bus.publish("waste_entry_created", entry_data)`
- In `warning_service.create_warning()`: publish `"warning_issued"` event
- ARQ worker: `app/workers/rule_worker.py` — subscribes to events, runs `evaluate_event`

**Deliverable:** Create rule via API → waste entry saved → rule fires → warning auto-created.

---

## Phase 5 — Analytics Engine
**Duration:** Weeks 6–7  
**Goal:** All analytics endpoints, aggregation pipeline, sustainability scoring.

### Models to Create

| Model | File | Ref |
|-------|------|-----|
| `AggregatedWasteModel` | `app/models/aggregated_waste.py` | `01-models.md §22` |
| `FilterPresetModel` | `app/models/filter_preset.py` | `01-models.md §18` |

### Alembic Migration
`alembic/versions/004_analytics.py`
> **Note:** Migration `004` directly follows `003`. There is no `004` gap — Phase 4 (Rule Engine) added no new models (rules were created in `003`), so numbering continues here.

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/analytics.py` | All 8 analytics routes | `03-routes.md §8` |
| `app/controllers/analytics_controller.py` | All analytics controller functions | `02-controllers.md §7` |
| `app/services/analytics_service.py` | All analytics service functions including `get_monthly_comparison` (exposed via `GET /analytics/trends?type=monthly_comparison`, dispatched inside `get_trends`) | `02-controllers.md §7` |
| `app/schemas/analytics.py` | All analytics schemas | `05-schemas.md §7` |
| `app/schemas/filter_presets.py` | All preset schemas | `05-schemas.md §12` |
| `app/routers/filter_presets.py` | 5 preset routes | `03-routes.md §17` |
| `app/controllers/filter_preset_controller.py` | `list_presets`, `save_preset`, `get_preset`, `update_preset`, `delete_preset` | `02-controllers.md §17` |
| `app/services/filter_preset_service.py` | Same functions | `02-controllers.md §17` |

### Background Aggregation

| File | Functions |
|------|-----------|
| `app/services/aggregation_service.py` | `run_hourly_aggregation`, `run_daily_aggregation`, `compute_sustainability_scores`, `update_student_status`, `check_device_offline_status` |
| `app/workers/aggregation_worker.py` | ARQ scheduled tasks: hourly aggregation, daily scoring, hourly device offline check |

> **Note:** `check_device_offline_status()` runs on the same hourly schedule as `run_hourly_aggregation`. It reads `device_offline_threshold_minutes` from `config_service.get_config("device")` (default: 10 minutes), finds devices where `last_heartbeat < now − threshold` and status ≠ `decommissioned`, then publishes a `device_offline` event to the event bus for each. Register in `arq_settings.py` alongside the other aggregation tasks.

**Deliverable:** All analytics dashboard endpoints return correct data with filters.

---

## Phase 6 — Notifications, Config & Reports
**Duration:** Week 8  
**Goal:** Email engine, notification CRUD, config system, report generation.

### Models to Create

| Model | File | Ref |
|-------|------|-----|
| `NotificationModel` | `app/models/notification.py` | `01-models.md §14` |
| `EmailTemplateModel` | `app/models/notification.py` | `01-models.md §15` |
| `ReportModel` | `app/models/report.py` | `01-models.md §16` |
| `ReportScheduleModel` | `app/models/report.py` | `01-models.md §17` |
| `BackupModel` | `app/models/backup.py` | `01-models.md §21` |

### Alembic Migration
`alembic/versions/005_notif_config_reports.py`
> **Note (B2):** Numbering continues from `004_analytics.py`. Phase 4 (Rule Engine) added no new models, so `005` follows `004` directly.

### Seed Scripts
`scripts/seed_templates.py` — 6 default email templates

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/notifications.py` | All 10 notification routes | `03-routes.md §10` |
| `app/controllers/notification_controller.py` | All notification functions | `02-controllers.md §9` |
| `app/services/notification_service.py` | All notification service functions | `02-controllers.md §9` |
| `app/services/email_service.py` | `send_email`, `send_bulk`, `render_template` | `02-controllers.md §16 Internal` |
| `app/schemas/notifications.py` | All notification schemas | `05-schemas.md §8` |
| `app/routers/templates.py` | All 6 template routes | `03-routes.md §13` |
| `app/controllers/template_controller.py` | All template functions | `02-controllers.md §12` |
| `app/services/template_service.py` | All template service functions | `02-controllers.md §12` |
| `app/schemas/templates.py` | `TemplateCreateSchema`, `TemplateUpdateSchema`, `EmailTemplateSchema`, `SampleDataSchema`, `RenderedHtmlSchema` | `05-schemas.md §14` |
| `app/routers/config.py` | All 13 config routes | `03-routes.md §12` |
| `app/controllers/config_controller.py` | All config functions | `02-controllers.md §11` |
| `app/schemas/config.py` | All config schemas | `05-schemas.md §10` |
| `app/routers/reports.py` | All 8 report routes | `03-routes.md §11` |
| `app/controllers/report_controller.py` | All report functions | `02-controllers.md §10` |
| `app/services/report_service.py` | `generate_report`, `generate_daily_report`, `generate_weekly_report`, `generate_custom_report`, `get_report_file`, `schedule_report`, `execute_scheduled_reports` | `02-controllers.md §10` |
| `app/schemas/reports.py` | All report schemas including `ScheduleUpdateSchema`, `PaginatedReports` | `05-schemas.md §9` |

### Report Generators

| File | Purpose |
|------|---------|
| `app/generators/pdf_generator.py` | WeasyPrint-based PDF from HTML templates |
| `app/generators/csv_generator.py` | CSV export using Python `csv` module |
| `app/generators/excel_generator.py` | OpenPyXL Excel generation |

### Workers
`app/workers/report_worker.py` — ARQ tasks: generate report, execute scheduled reports, send scheduled notifications

**Deliverable:** Send email, generate PDF report, update config — all working.

---

## Phase 7 — Real-Time & WebSocket
**Duration:** Week 9  
**Goal:** WebSocket server, live monitoring, real-time KPI updates.

### Files to Create

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/ws.py` | `ws_dashboard`, `ws_monitoring` WS endpoints | `03-routes.md §18` |
| `app/controllers/ws_controller.py` | `ws_dashboard`, `ws_monitoring` | `02-controllers.md §16` |
| `app/services/ws_service.py` | `ConnectionManager` class: `connect`, `disconnect`, `broadcast_to_room`, `send_to_user` |
| `app/routers/monitoring.py` | All 4 monitoring routes | `03-routes.md §9` |
| `app/controllers/monitoring_controller.py` | All monitoring functions | `02-controllers.md §8` |
| `app/services/monitoring_service.py` | All monitoring service functions | `02-controllers.md §8` |

### WebSocket Event Types
Wire these publish calls:
- `waste_service.create_waste_entry()` → `ws_service.broadcast_to_room("monitoring", {type:"waste_entry", ...})`
- `warning_service.create_warning()` → `ws_service.broadcast_to_room("dashboard", {type:"warning_issued", ...})`
- `waste_service.ml_heartbeat()` → `ws_service.broadcast_to_room("monitoring", {type:"device_status", ...})`
- `aggregation_worker` (hourly) → `ws_service.broadcast_to_room("dashboard", {type:"kpi_update", ...})`

> **Retroactive Imports Required (N4):** Adding broadcast calls to services built in earlier phases requires these file edits:
> - `app/services/waste_service.py` (Phase 3) → add `from app.services.ws_service import ws_service`
> - `app/services/warning_service.py` (Phase 3) → add `from app.services.ws_service import ws_service`
>
> These imports are safe to add in Phase 7 (after `ws_service.py` is created) because the broadcast calls inside each service are guarded by lazy import at module level — no circular dependency is introduced.

> **Dependency note:** `waste_service` and `warning_service` import `ws_service` for broadcast calls. `monitoring_service` also delegates to `waste_service` internally. **`waste_service` must never import from `monitoring_service`** — that direction creates a circular import. All WS broadcasts from `waste_service` go directly through `ws_service`, never through `monitoring_service`.

**Deliverable:** Live monitoring page streams waste entries in real-time via WebSocket.

---

## Phase 8 — Settings & Audit
**Duration:** Week 10  
**Goal:** Settings page (user mgmt, security, backup, maintenance), audit log.

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/settings.py` | All 19 settings routes | `03-routes.md §14` |
| `app/controllers/settings_controller.py` | All settings functions | `02-controllers.md §13` |
| `app/services/settings_service.py` | All settings service functions | `02-controllers.md §13` |
| `app/schemas/settings.py` | `UserCreateSchema`, `UserUpdateSchema`, `BackupSchema` | `05-schemas.md §15` |
| `app/routers/audit.py` | All 5 audit routes | `03-routes.md §15` |
| `app/controllers/audit_controller.py` | All audit functions | `02-controllers.md §14` |
| `app/services/audit_service.py` | Complete implementation | `02-controllers.md §14` |
| `app/schemas/audit.py` | All audit schemas | `05-schemas.md §11` |
| `app/schemas/common.py` | Common utility schemas | `05-schemas.md §13` |
| `app/routers/roles.py` | 2 role routes | `03-routes.md §16` |
| `app/controllers/roles_controller.py` | `list_roles`, `update_role` | `02-controllers.md §18` |
| `app/services/roles_service.py` | `list_roles`, `update_role` | `02-controllers.md §18` |
| `app/schemas/roles.py` | `RoleSchema`, `RoleUpdateSchema` | `05-schemas.md §16` |

### Backup System

| File | Purpose |
|------|---------|
| `app/services/backup_service.py` | `create_backup` (copy SQLite + compress), `restore_backup` |
| `app/workers/backup_worker.py` | ARQ scheduled backup task, auto-purge old audit events |

**Deliverable:** All 14 pages of the dashboard have working backend APIs.

---

## Phase 9 — SvelteKit Frontend
**Duration:** Weeks 11–14  
**Goal:** Complete dashboard UI wired to all backend APIs.

### Week 11 — Setup & Auth & Layout

| File | Task |
|------|------|
| `frontend/` SvelteKit init | TypeScript, Tailwind, shadcn-svelte |
| `src/lib/api/client.ts` | Fetch wrapper with JWT attach + refresh logic |
| `src/lib/api/ws.ts` | WebSocket client with reconnect |
| `src/lib/stores/auth.ts` | `AuthStore` with login/logout/session |
| `src/routes/login/+page.svelte` | Login page — `01-login.md` |
| `src/lib/components/layout/` | Sidebar nav, header, content wrapper |

### Week 12 — Dashboard, Monitoring, Analytics

| File | Page | Ref |
|------|------|-----|
| `src/routes/dashboard/+page.svelte` | Overview dashboard | `02-overview-dashboard.md` |
| `src/routes/dashboard/monitoring/+page.svelte` | Live monitoring | `03-live-monitoring.md` |
| `src/routes/dashboard/analytics/+page.svelte` | Analytics + sub-tabs | `04-analytics.md` |
| `src/lib/components/charts/` | Line, bar, donut, gauge chart wrappers (Chart.js) |

### Week 13 — Students, Warnings, Rules

| File | Page | Ref |
|------|------|-----|
| `src/routes/dashboard/students/+page.svelte` | Students list | `05-students-list.md` |
| `src/routes/dashboard/students/[id]/+page.svelte` | Student intelligence | `06-student-intelligence.md` |
| `src/routes/dashboard/warnings/+page.svelte` | Warnings & penalties | `07-warnings-penalties.md` |
| `src/routes/dashboard/rules/+page.svelte` | Rule engine | `08-rule-engine.md` (UI spec in `docs/praposed-imp/pages/08-rule-engine.md` — **not** `docs/plans/08-rule-engine.md` which is the backend internals doc) |

### Week 14 — Notifications, Reports, Devices, Config, Settings, Audit

| File | Page | Ref |
|------|------|-----|
| `src/routes/dashboard/notifications/+page.svelte` | Notification center | `09-notifications.md` |
| `src/routes/dashboard/reports/+page.svelte` | Reports | `10-reports.md` |
| `src/routes/dashboard/devices/+page.svelte` | Devices | `11-devices.md` |
| `src/routes/dashboard/config/+page.svelte` | Configuration | `12-configuration.md` |
| `src/routes/dashboard/settings/+page.svelte` | Settings | `13-settings.md` |
| `src/routes/dashboard/audit/+page.svelte` | Audit log | `14-audit-log.md` |

---

## Phase 10 — Deployment & Hardening
**Duration:** Week 15  
**Goal:** Production Docker, Nginx, Cloudflare Tunnel, security audit.

| Task | File/Tool |
|------|-----------|
| Production Docker Compose | `docker-compose.prod.yml` — fastapi, celery/arq, redis, nginx, cloudflared |
| ARM64 Dockerfile | `Dockerfile.prod` — multi-stage, slim base |
| Nginx prod config | `nginx/nginx.conf` — gzip, rate limit, SSL, proxy to :8000 |
| Cloudflare Tunnel | `cloudflare/config.yml` |
| systemd services | `deploy/systemd/cleanplates.service` |
| DB WAL mode | Enable in `app/core/database.py` on startup |
| Indexes review | Verify all indexes in `01-models.md` exist in migrations |
| RBAC full audit | Test each endpoint with each role |
| Load test | `scripts/load_test.py` — verify <100ms CRUD, <500ms analytics |

---

## File Count Summary

| Layer | Files |
|-------|-------|
| Models | 16 model files (base.py + 15 model files = 24 models total) |
| Schemas | 16 schema files |
| Controllers | 18 controller files |
| Services | 20 service files |
| Routers | 19 router files (18 feature routers + health.py) |
| Middlewares | 9 middleware files |
| Engine | 3 engine files (condition, action, event bus) |
| Workers | 4 ARQ worker files |
| Generators | 3 generator files (pdf, csv, excel) |
| Frontend pages | 14 route pages + components |
| **Total backend** | **~112 Python files** |
| **Total frontend** | **~60 Svelte/TS files** |

---

## Cross-Cutting Rules for Coding Agent

1. **Every write endpoint** must call `audit_service.log()` with before+after state
2. **Every warning/penalty creation** must check `send_email` flag → queue email via ARQ
3. **Every waste entry** saved must publish `waste_entry_created` to event bus
4. **Rule engine** must be stateless — reload active rules from DB on each evaluation
5. **Config values** are always read from DB via `config_service.get_config()`, never hardcoded
6. **Student status** (`green/yellow/orange/red`) is always recomputed via `aggregation_service.update_student_status()` after any warning/penalty change
7. **Sustainability score** is recomputed in daily ARQ task, not on every entry
8. **All paginated endpoints** must use `page`+`size` query params and return `PaginatedBase` shape
9. **File uploads** (logo, backup restore, CSV import) use `UploadFile` FastAPI type, validate type+size before processing
10. **WebSocket connections** authenticate via `?token=` query parameter, validated same as HTTP auth
