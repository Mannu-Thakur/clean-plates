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
| `pyproject.toml` | All deps | Add all dependencies from framework doc (ensure `python-multipart` is included for CSV uploads) |
| `.env.example` | — | All settings from `04-middlewares.md § Pydantic Settings` |
| `app/core/config.py` | `Settings` class | Full settings from `04-middlewares.md § Pydantic Settings` |
| `app/core/redis.py` | Redis Pool | **[NEW — Moved from Phase 4]** Initialize the **`ArqRedis` pool** via `arq.connections.create_pool` inside the FastAPI `@asynccontextmanager` lifespan in `app/main.py`, setting `app.state.arq_pool`. This handles both standard Redis commands (`INCR`/`EXPIRE`) for `RateLimitMiddleware` (since `ArqRedis` subclasses `Redis`) AND future job queueing in Phase 4. |
| `app/core/database.py` | — | Async SQLAlchemy engine + `AsyncSessionLocal` session factory only — **do NOT** define `get_db_session` here; the dependency lives exclusively in `app/middleware/db.py`. **Enable WAL mode, FK constraints, and connection safety immediately:** pass `connect_args={"check_same_thread": False, "timeout": 15}` to the engine. Execute `PRAGMA journal_mode=WAL` and **`PRAGMA foreign_keys=ON`** via an `@event.listens_for(engine.sync_engine, "connect")` hook on startup (SQLite defaults to FKs off, causing silent failures without this). Do NOT defer this to Phase 10 — concurrent ARQ workers in Phase 4+ will cause `OperationalError: database is locked` without it. |
| `app/core/security.py` | — | `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`. **⚠ P1-fix (Event Loop Blocking):** Bcrypt is intentionally slow and CPU-bound (~100-300ms per call). You MUST wrap `hash_password` and `verify_password` in `await asyncio.to_thread(passlib_context.verify, plain, hashed)` (and similarly for hashing) to avoid blocking the ASGI event loop. Without this, concurrent login requests will stall WebSocket heartbeats and all other async I/O. |
| `app/main.py` | — | FastAPI app init + all middleware registration from `04-middlewares.md § Middleware Registration Order`. **⚠ CRITICAL:** Ensure `logging`, `rate_limit`, and `security_headers` middlewares are pure ASGI or explicitly bypass `/ws` paths to prevent `BaseHTTPMiddleware` from sabotaging WebSockets in Phase 7. |
| `app/middleware/auth.py` | — | `get_current_user`, `get_current_user_optional`, `get_api_key_device` from `04-middlewares.md §1,§11` |
| `app/middleware/rbac.py` | — | `require_roles`, `require_admin`, `require_write_access` from `04-middlewares.md §2` |
| `app/middleware/logging.py` | — | Request/response structured logging from `04-middlewares.md §3` |
| `app/middleware/error_handler.py` | — | All exception handlers from `04-middlewares.md §7` |
| `app/middleware/rate_limit.py` | — | Redis-backed rate limiter from `04-middlewares.md §5` |
| `app/middleware/security_headers.py` | — | Security headers from `04-middlewares.md §10` |
| `app/middleware/audit.py` | — | `capture_before(model)`, `capture_after(model)` helpers from `04-middlewares.md §6` — used by all service layers that audit |
| `app/middleware/db.py` | — | `get_db_session()` async dependency (yields `AsyncSession`, commits on success, rolls back on error) from `04-middlewares.md §12` — distinct from engine setup in `app/core/database.py` |
| `app/schemas/common.py` | — | **⚠ Create in Phase 1 (B1-fix):** `PaginatedBase`, `MessageSchema`, `ErrorSchema` — imported by every paginated response schema starting Phase 2. Utility schemas (`SystemInfoSchema`, `LogoUrlSchema`, `CacheResultSchema`, etc.) can be stubbed here and completed in Phase 8. |

### Models to Create (SQLAlchemy)

| Model | File | Ref |
|-------|------|-----|
| `Base` + common mixins | `app/models/base.py` | SQLAlchemy declarative base |
| `UserModel` | `app/models/user.py` | `01-models.md §1` |
| `RefreshTokenModel` | `app/models/user.py` | `01-models.md §2` |
| `RoleModel` | `app/models/role.py` | `01-models.md §23` |
| `ConfigModel` | `app/models/config.py` | `01-models.md §19` |
| `AuditEventModel` | `app/models/audit.py` | **[Moved from Phase 2]** `01-models.md §20` |

### Alembic

| Task | File |
|------|------|
| Init alembic | `alembic/` directory |
| Customize for async | `alembic/env.py` — use `run_async_migrations()`; import `AsyncEngine`; import all models; **pass `render_as_batch=True` inside `context.configure(...)` to enable SQLite batch migration mode** (required to avoid `ALTER TABLE` crashes on all future migrations). **⚠ CRITICAL (FK Batch Bug):** Inside `run_async_migrations`, you must execute `await connection.execute(text("PRAGMA foreign_keys=OFF"))` before `context.run_migrations()` to prevent batch migration from failing when dropping tables. |
| First migration | `alembic/versions/001_initial_users.py` — creates `users`, `refresh_tokens`, `roles`, `system_config`, `audit_events` tables |
| Seed scripts | `scripts/seed_roles.py` — insert all 5 default roles (`super_admin`, `institution_admin`, `mess_admin`, `analytics_viewer`, `staff_operator`) **with `is_system=True`** so they cannot be inadvertently treated as deletable. Use the permissions matrix from `01-models.md §23`. |
| | `scripts/seed_config.py` — **must populate ALL 8 config sections** or Phase 3+ services will encounter `KeyError` on missing keys: `institution` (name, code, **timezone e.g. "Asia/Kolkata" for accurate aggregations**), `thresholds` (`ThresholdSchema` defaults), `meals` (breakfast 07:00–09:30, lunch 12:00–14:30, dinner 19:00–21:30), `system` (`SystemPolicySchema` defaults), `device` (`DeviceConfigSchema` defaults — `device_offline_threshold_minutes=10`, `heartbeat_interval_seconds=60`), `appearance` (`AppearanceConfigSchema` defaults), `branches` (default entries e.g. `[{"code":"CSE","name":"Computer Science & Engineering"},{"code":"ECE","name":"Electronics & Communication"},{"code":"ME","name":"Mechanical Engineering"},{"code":"CE","name":"Civil Engineering"}]` — **[G4-fix]** used by student filtering, analytics grouping, and `GET /config/branches` route in Phase 6), `security` (`SecurityConfigSchema` defaults — `access_token_expiry_minutes=60`, `max_login_attempts=5`, `lockout_duration_minutes=15` — **[G5-fix]** accessed via `GET/PATCH /settings/security` in Phase 8). |

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/auth.py` | All 6 auth routes | `03-routes.md §1` |
| `app/controllers/auth_controller.py` | All 6 auth controller functions | `02-controllers.md §1` |
| `app/services/auth_service.py` | `authenticate`, `issue_tokens`, `refresh_tokens`, `revoke_token`, `request_password_reset`, `reset_password` | `02-controllers.md §1` |
| `app/services/config_service.py` | `get_config`, `set_config`, `reset_section` | `02-controllers.md §11` |
| `app/services/audit_service.py` | **[Moved from Phase 2]** implement **only `log()` and `purge_old_events()`** in Phase 1. All read endpoints are in Phase 8. Internal callers across Phases 1–7 must only call `audit_service.log()`. | `02-controllers.md §14` |
| `app/schemas/auth.py` | All auth schemas | `05-schemas.md §1` |

> **Note (Email Stub — Phase 1):** `auth_service.request_password_reset()` sends a password-reset email. Because `EmailService` is not built until Phase 6, stub this call with `# TODO: Wire EmailService in Phase 6` (same pattern as `WarningService` email stub in Phase 2). The reset token must still be generated and stored; only the email dispatch is deferred.
>
> **Note (B3 — Config API Availability):** `config_service.py` is created in Phase 1 for **internal use only** by other services (e.g., `waste_service` reads meal timings, `aggregation_service` reads timezone). The config **HTTP routes** (`app/routers/config.py`, `app/controllers/config_controller.py`) are NOT registered until Phase 6. Admins cannot update config via API during Phases 2–5 — all config values come from `seed_config.py` defaults. This is intentional.

### Health & Infra

| File | Task |
|------|------|
| `app/routers/health.py` | `GET /health` → returns `{status: ok, version, uptime}` |
| `docker-compose.dev.yml` | FastAPI + Redis services |
| `Dockerfile` | Multi-stage, ARM64-compatible |
| `nginx.conf` | Reverse proxy to port 8000 |

### Static File Serving (Mount in `app/main.py`)

Mount upload directories so the SvelteKit frontend can render images (plate images from ML, institution logo from Settings):

```python
from fastapi.staticfiles import StaticFiles
import os

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
```

> **Note:** `settings.UPLOAD_DIR` defaults to `./uploads` (from `04-middlewares.md § Pydantic Settings`). Mount this in Phase 1 so that `plate_image_path` (Phase 3 `WasteEntryModel`) and `logo_path` (Phase 8 `upload_logo`) resolve to accessible URLs like `/static/uploads/<filename>` from the frontend. The `nginx.conf` should proxy `/static/` requests to FastAPI (or serve directly from disk in production).

**Deliverable:** `POST /auth/login` works, returns JWT. All middleware active. DB migrations run clean.

> **⚠ M1-fix (Seed Checklist):** Run these commands in order after `alembic upgrade head` — failing to run them before starting Phase 2/3 services will cause `KeyError` on config lookups and missing role data:
> ```bash
> python scripts/seed_roles.py    # 5 default roles with is_system=True
> python scripts/seed_config.py   # ALL 8 config sections (incl. device, branches, security)
> ```
> **Note:** These seed scripts run from the CLI outside of FastAPI's request lifecycle, so they must instantiate their own standalone async SQLAlchemy engine and session. Do NOT defer these to a later phase.

---

## Phase 2 — Device & Student Core
**Duration:** Week 2  
**Goal:** Device registration, student creation, student mapping.

### Models to Create

| Model | File | Ref |
|-------|------|-----|
| `DeviceModel` | `app/models/device.py` | `01-models.md §3` |
| `DeviceHealthModel` | `app/models/device.py` | `01-models.md §4` |
| `StudentModel` | `app/models/student.py` | `01-models.md §5` |
| `StudentMappingModel` | `app/models/student.py` | `01-models.md §6` |
| `FoodItemModel` | `app/models/food.py` | `01-models.md §7` |

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
| `app/routers/devices.py` | **8 of 9 device routes** (`restart_service` is the 9th — added in Phase 4) | `03-routes.md §2` |
| `app/controllers/device_controller.py` | All device controller functions | `02-controllers.md §2` |
| `app/services/device_service.py` | All device service functions | `02-controllers.md §2` |
| `app/schemas/devices.py` | All device schemas | `05-schemas.md §2` |
| `app/routers/students.py` | `list_students`, `get_student`, `map_student_id`, `update_mapping`, `update_student_profile`, `import_mapping_csv`, `export_students` | `03-routes.md §3` |
| `app/controllers/student_controller.py` | Same functions (`update_mapping` = PATCH mapping fields; `update_student_profile` = PATCH top-level student fields, bound to `PATCH /{student_id}`) | `02-controllers.md §3` |
| `app/services/student_service.py` | `list_students`, `get_student`, `map_student_id`, `update_mapping`, `update_student_profile`, `import_mapping_csv`, `export_students` | `02-controllers.md §3` |
| `app/schemas/students.py` | `MappingCreateSchema`, `MappingUpdateSchema`, `StudentProfileUpdateSchema`, `StudentSchema`, `ImportResultSchema` | `05-schemas.md §3` |

### Audit Integration

Wire `audit_service.log()` into device registration and student mapping functions.



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
| `app/routers/ml.py` | `POST /ml/detect`, `POST /ml/sync`, `POST /ml/heartbeat`, `POST /ml/upload-image` | `03-routes.md §5` |
| `app/controllers/ml_controller.py` | `ingest_detection`, `bulk_ingest`, `ml_heartbeat`, `upload_image` | `02-controllers.md §15` |
| `app/routers/waste.py` | All 4 waste routes | `03-routes.md §4` |
| `app/controllers/waste_controller.py` | `create_waste_entry`, `bulk_sync`, `get_entry`, `list_entries`, `get_current_session`, `get_recent_entries` | `02-controllers.md §4` |
| `app/services/waste_service.py` | Same | `02-controllers.md §4` |
| `app/routers/warnings.py` | All warning, penalty, escalation routes (including `GET /export` → `export_warnings` and `create_penalty_direct`) | `03-routes.md §6` |
| `app/controllers/warning_controller.py` | All warning controller functions including `export_warnings` and `create_penalty_direct` | `02-controllers.md §5` |
| `app/services/warning_service.py` | All warning service functions | `02-controllers.md §5` |
| `app/schemas/warnings.py` | All warning/penalty/escalation schemas | `05-schemas.md §5` |

### Student Intelligence Routes (analytics part)

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/students.py` | Add: `get_student_stats`, `get_student_timeline`, `get_food_breakdown`, `get_meal_pattern`, `get_improvement_trend`, `get_student_history`, `get_student_warnings`, `bulk_warn`, `create_warning` | `03-routes.md §3` |
| `app/controllers/student_controller.py` | Same functions | `02-controllers.md §3` |

> **Note (Dependencies stubbed):** `WarningService` must stub the email sending logic (e.g., `if send_email: pass # TODO: Wire in Phase 6`) because `EmailService` and ARQ workers are not built until Phases 4 and 6. Similarly, recalculating student status via `aggregation_service` must be stubbed until Phase 5.

**Deliverable:** ML pipeline can push waste entries. Full warning/penalty lifecycle works. Student intelligence page stats computable.

---

## Phase 4 — Rule Engine
**Duration:** Weeks 4–5  
**Goal:** Dynamic rule CRUD, event-based evaluation, action execution.

### Models & DB
*(Rule models `RuleModel` and `RuleExecutionModel` were already created in Phase 3 DB migrations to avoid SQLite FK constraints issues. No new models or migrations required in this phase.)*

### ARQ Redis Pool Setup (C1-fix)

> **⚠ C1-fix:** `waste_service` and `warning_service` call `await arq_redis.enqueue_job(...)` to dispatch rule evaluation jobs. `arq_redis` is an ARQ `ArqRedis` connection pool. As noted in Phase 1, this pool is already initialized in `app.main.py`'s lifespan. You just need to ensure the dependency injection `get_arq_pool()` is properly passing it to your services.

| File | Task |
|------|------|
| `app/core/redis.py` | **[NEW — C1-fix]** Ensure the dependency `def get_arq_pool(request: Request) -> ArqRedis:` returns `request.app.state.arq_pool` (which was initialized in Phase 1). |

**Lifespan hook to add to `app/main.py`** (created in Phase 1):
```python
from contextlib import asynccontextmanager
from arq.connections import create_pool, RedisSettings
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    yield
    await app.state.arq_pool.aclose()

app = FastAPI(..., lifespan=lifespan)
```

**Usage in services** (`waste_service.py`, `warning_service.py`):
> **⚠ CRITICAL (ARQ Pool Injection):** Services that enqueue jobs (like `warning_service.create_warning()`) are called by both FastAPI routers AND the ARQ worker (via `action_executor`). Since workers lack a FastAPI `Request` object, relying on `request.app.state.arq_pool` inside the service will cause fatal crashes.
> **Fix:** Services must explicitly accept `arq_pool: ArqRedis` as an argument (just like `db: AsyncSession`). FastAPI injects it via `Depends(get_arq_pool)`; ARQ workers inject it via `ctx['redis']`.

```python
# Inside service function signature:
async def create_warning(db: AsyncSession, arq_pool: ArqRedis, ...):
    # Enqueue with depth tracking to prevent infinite loops (Phase 4)
    payload = {"event": event_type, "data": event_data, "depth": 1}
    await arq_pool.enqueue_job("evaluate_event", event_type, payload)
```

### Workers Package Scaffold

> **Note (B4/I1):** Create the `app/workers/` package in this phase — it is the Docker Compose ARQ worker entrypoint. Without `arq_settings.py`, the command `arq app.workers.arq_settings.WorkerSettings` in `docker-compose.yml` will fail immediately.

| File | Task |
|------|------|
| `app/workers/__init__.py` | Empty package init |
| `app/workers/arq_settings.py` | ARQ `WorkerSettings` class — registers all cron jobs; start with `rule_worker` only; expand in Phases 5–6. **⚠ CRITICAL:** Must define an `on_startup` hook to initialize the `AsyncEngine` and attach an `async_sessionmaker` to `ctx['db_session_factory']`. ARQ workers do NOT have access to FastAPI's `Depends(get_db_session)`. Worker functions must create their own DB session from `ctx` and pass it to services. **⚠ M3-audit-fix (Stuck Background Jobs Recovery):** The `on_startup` hook must ALSO query for any `ReportModel` stuck in `generating` status or `BackupModel` stuck in `creating` status and reset them to `failed`. If the ARQ worker crashes or restarts mid-job, these records remain stuck indefinitely, cluttering the UI and blocking future runs. |
| `app/workers/rule_worker.py` | **N2-fix:** Receives ARQ jobs enqueued by `waste_service` and `warning_service` → calls `rule_engine_service.evaluate_event` for each job. Does NOT use Redis Pub/Sub as primary delivery (see B4 note above). `event_bus.py` Redis Pub/Sub is reserved for WebSocket fan-out in Phase 7 only. |

### ARQ Cron Schedule (expand `arq_settings.py` per phase)

| Task Function | Worker File | Frequency | Phase Added |
|--------------|-------------|-----------|-------------|
| `rule_engine_worker` | `rule_worker.py` | **On-demand via ARQ job queue** (enqueued by `waste_service` and `warning_service` — see B4 note above; Redis Pub/Sub is NOT used for rule evaluation) | Phase 4 |
| `run_hourly_aggregation` | `aggregation_worker.py` | Every 30 minutes (checks if hour rolled over) | Phase 5 |
| `run_daily_aggregation` | `aggregation_worker.py` | Every 30 minutes — **[M10-fix: Fractional Timezones]** Must run every 30 mins (not 60) to support fractional timezones like IST (UTC+5:30) where midnight is 18:30 UTC. Internal logic checks `local_time.hour == 0 and local_time.minute == 0`. | Phase 5 |
| `compute_sustainability_scores` | `aggregation_worker.py` | **[P4-fix]** Every 15 minutes (`minute={0, 15, 30, 45}`) — internal logic checks if `local_time.hour == 0 and local_time.minute == 15` before executing. Running only at a fixed UTC time misses the 00:15 local mark for fractional timezones (e.g., IST 00:15 = UTC 18:45, which a 30-min cron at :00/:30 would skip entirely). | Phase 5 |
| `check_device_offline_status` | `aggregation_worker.py` | Every 5 minutes | Phase 5 |
| `execute_scheduled_reports` | `report_worker.py` | Every 5 minutes (checks `next_run`) | Phase 6 |
| `send_scheduled_notifications` | `report_worker.py` | Every 5 minutes (checks `scheduled_at`) | Phase 6 |
| `send_email_task` | `report_worker.py` | **[NEW] On-demand via ARQ job queue** (immediate email dispatch) | Phase 6 |
| `auto_backup` | `backup_worker.py` | **[P3-fix]** Every 1 hour (static ARQ cron). Internal logic fetches `backup_interval_hours` from `config_service.get_config("system")`, checks timestamp of last backup in `BackupModel`, and only executes if `now − last_backup >= interval`. ARQ cron schedules are evaluated at worker startup — a static 24h interval ignores dynamic config changes until the container restarts. | Phase 8 |
| `purge_old_audit_events` | `backup_worker.py` | Daily at 03:00 UTC (per `audit_retention_days` config) | Phase 8 |
| `restore_backup_task` | `backup_worker.py` | **On-demand via ARQ job queue** (enqueued by `settings_service.restore_backup()`) | Phase 8 |

### Core Engine Files

| File | Class/Functions | Ref |
|------|-----------------|-----|
| `app/services/rule_engine_service.py` | `evaluate_event`, `match_conditions`, `execute_actions` | `02-controllers.md §16 Internal` |
| `app/engine/condition_matcher.py` | `match`, `match_numeric`, `match_string`, `match_time_window`, `match_frequency`, `match_trend`, `match_aggregate` | `08-rule-engine.md` |
| `app/engine/action_executor.py` | `execute`, `generate_warning`, `send_email`, `increase_penalty`, `trigger_escalation`, `classify_student`, `create_audit_log` — **⚠ B2-fix: all methods accept `arq_pool: ArqRedis` as a parameter** (needed for downstream job enqueuing per Cross-Cutting Rule #11) | `08-rule-engine.md` |
| `app/engine/event_bus.py` | `publish(event_type, event_data)`, `subscribe(event_type, handler)` — Redis pub/sub backed | `08-rule-engine.md` |

> **Note (Event Bus Reliability & Scope — B4):** Redis Pub/Sub is fire-and-forget. If the rule worker is restarting or blocked at the exact moment a `waste_entry_created` event fires, that event is **silently lost** and no rules will evaluate for that entry. **Preferred fix:** Use ARQ's job queue as the primary delivery mechanism. In `waste_service.create_waste_entry()` and `warning_service.create_warning()`, call `await arq_redis.enqueue_job("evaluate_event", event_type, event_data)`. This provides at-least-once delivery with automatic retry. **Reserve `event_bus.py` strictly for UI WebSocket fan-out in Phase 7.** The rule engine internal logic operates solely on ARQ.

> **Note (Email Action Stub — Phase 4):** `action_executor.py` includes a `send_email` action type. Because `EmailService` is not built until Phase 6, stub this action in Phase 4: `if action["type"] == "send_email": pass  # TODO: Wire EmailService in Phase 6`. Log the intended email action to `audit_service` so it is traceable. Un-stub in Phase 6 by enqueuing an email job via `await ctx['redis'].enqueue_job('send_email_task', ...)` instead of synchronous calling to avoid blocking the rule worker.
>
> **Note (System User & Audits):** When rules fire via the background worker, there is no `current_user`. The `warning_service.create_warning` and `audit_service.log` functions must be explicitly designed to accept `current_user=None` (handling it as a "System" action).
>
> **⚠ M4-fix (Infinite Loop Protection):** A rule triggered by `warning_issued` could execute `generate_warning`, which triggers `warning_issued` again, creating an infinite loop. `rule_engine_service.evaluate_event` MUST track an execution `depth` (passed in the ARQ payload) and abort if `depth > 3`, or strictly prevent self-triggering recursive rules.
>
> **Note (Enqueueing Jobs):** Inside FastAPI routes/services, use `request.app.state.arq_pool.enqueue_job`. Inside ARQ workers, use `ctx['redis'].enqueue_job`.

### Routes & Controllers

| File | Functions | Ref |
|------|-----------|-----|
| `app/routers/rules.py` | All 15 rule routes | `03-routes.md §7` |
| `app/controllers/rule_controller.py` | All rule controller functions | `02-controllers.md §6` |
| `app/schemas/rules.py` | All rule schemas | `05-schemas.md §6` |
| `app/routers/devices.py` | Add: `restart_service` | `03-routes.md §2` |
| `app/controllers/device_controller.py` | Add: `restart_service` | `02-controllers.md §2` |

### Wire Events (N3-fix: use ARQ job queue, NOT event_bus.publish as primary)
- In `waste_service.create_waste_entry()`: after saving, call **`await arq_redis.enqueue_job("evaluate_event", "waste_entry_created", entry_data)`** (ARQ job queue — at-least-once delivery). Additionally call `event_bus.publish("waste_entry_created", entry_data)` for WebSocket fan-out only (Phase 7).
- In `warning_service.create_warning()`: enqueue ARQ job for `"warning_issued"` event; also publish to event bus for WS fan-out.
- ARQ worker: `app/workers/rule_worker.py` — receives enqueued jobs, runs `evaluate_event`.

> **⚠ P2-fix (Commit-Before-Enqueue Race Condition):** When a service function saves a DB record and then enqueues an ARQ job referencing that record, the service MUST call `await db.commit()` **before** `await arq_pool.enqueue_job(...)`. If the job is enqueued first, the ARQ worker may pick it up instantly and query the DB before the HTTP request's middleware commits the transaction — causing the worker to find nothing and fail silently. This applies to `waste_service.create_waste_entry()`, `warning_service.create_warning()`, and any future service that enqueues jobs after writes. The `get_db_session()` middleware will then commit a no-op (already committed), which is harmless.

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
| `app/workers/aggregation_worker.py` | ARQ scheduled tasks: hourly aggregation, daily scoring, 5-minute device offline check |

> **Note:** `check_device_offline_status()` runs on a **5-minute schedule** (must be more frequent than the default 10-min threshold). It reads `device_offline_threshold_minutes` from `config_service.get_config("device")` (default: 10 minutes), finds devices where `last_heartbeat < now − threshold` and status ≠ `decommissioned`, then publishes a `device_offline` event to the event bus for each. Register in `arq_settings.py` alongside the other aggregation tasks. **⚠ L1-fix (Duplicate Event Guard):** Only publish `device_offline` for devices where `status != 'offline'`. After publishing the event, immediately update `device.status = 'offline'` in the same transaction. This ensures the event fires **exactly once** per offline transition — without this guard, a device that goes offline will trigger a `device_offline` event (and potentially duplicate warnings/notifications) every 5 minutes indefinitely.
>
> **⚠ M5-fix (Timezone Alignment):** `run_hourly_aggregation` and `run_daily_aggregation` must query `config_service.get_config("institution")` for the institution's timezone (e.g., "Asia/Kolkata") to accurately resolve date boundaries (midnight) and meal time slots (e.g., 07:00-09:30). Do NOT rely solely on UTC. Because ARQ's cron is strictly UTC, `run_daily_aggregation` must run *every 30 minutes* (to accommodate fractional timezones like IST at UTC+5:30), and its internal logic should check if `local_time.hour == 0 and local_time.minute == 0` before processing the daily rollup.

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

> **⚠ M8-fix (Un-stubbing Emails):** Go back to `auth_service.request_password_reset` (Phase 1), `warning_service` (Phase 3), and `action_executor` (Phase 4) and replace the `# TODO: Wire EmailService in Phase 6` stubs with actual calls to `email_service` or ARQ enqueues.

### Report Generators

| File | Purpose |
|------|---------|
| `app/generators/pdf_generator.py` | WeasyPrint-based PDF from HTML templates. **⚠ CRITICAL (Blocking I/O):** WeasyPrint is CPU-bound and synchronous. You MUST wrap generation in `await asyncio.to_thread(weasyprint_func, ...)` to avoid blocking the Uvicorn/ARQ async event loop. **⚠ M4-audit-fix (System Dependencies):** WeasyPrint requires OS-level C-libraries. Add to Dockerfile: `apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`. Without these, WeasyPrint will fail with missing library errors at runtime. |
| `app/generators/csv_generator.py` | CSV export using Python `csv` module |
| `app/generators/excel_generator.py` | OpenPyXL Excel generation |

### Workers
`app/workers/report_worker.py` — ARQ tasks: generate report, execute scheduled reports, send scheduled notifications, and **`send_email_task` (for immediate email dispatch from services)**.

> **⚠ F2-fix (Scheduled Report `generated_by`):** `execute_scheduled_reports` runs in the ARQ worker with no `current_user`. `ReportModel.generated_by` is `NOT NULL`. The worker MUST set `generated_by = schedule.created_by` (the user who created the `ReportScheduleModel`). This is semantically correct — the schedule owner is responsible for auto-generated reports.
>
> **⚠ M1-audit-fix (Timezone Handling in Scheduled Reports):** `ReportScheduleModel` stores `time_of_day` (e.g., "08:00") which represents the admin's local time. The `next_run` calculation within `report_service.py` and `execute_scheduled_reports` MUST: (1) lookup the institution's timezone via `config_service.get_config("institution")["timezone"]` (e.g., "Asia/Kolkata"), (2) construct a localized datetime object using that timezone, (3) convert it to UTC for the ARQ scheduler comparison. Without this, a report scheduled for 08:00 IST will incorrectly execute at 08:00 UTC (13:30 IST).

> **⚠ F6-fix (Security Config Source of Truth):** `Settings` in `.env` provides **startup/seed defaults** for `ACCESS_TOKEN_EXPIRE_MINUTES`, `MAX_LOGIN_ATTEMPTS`, `LOCKOUT_DURATION_MINUTES`. The `security` section in `system_config` DB (seeded from these defaults) is the **runtime source of truth**. `auth_service.authenticate()` must read lockout settings via `config_service.get_config("security")`, NOT `settings.MAX_LOGIN_ATTEMPTS`. Admin changes via `PATCH /settings/security` take effect immediately. The `.env` values only matter for initial seeding.

**Deliverable:** Send email, generate PDF report, update config — all working.

---

## Phase 7 — Real-Time & WebSocket
**Duration:** Week 9  
**Goal:** WebSocket server, live monitoring, real-time KPI updates.

### Files to Create

| File | Functions | Ref |
|------|-----------|-----|
| `app/middleware/ws_auth.py` | **[Moved from Phase 1]** WebSocket token auth dependency from `04-middlewares.md §11` | `04-middlewares.md` |
| `app/routers/ws.py` | `ws_dashboard`, `ws_monitoring` WS endpoints | `03-routes.md §18` |
| `app/controllers/ws_controller.py` | `ws_dashboard`, `ws_monitoring` | `02-controllers.md §16` |
| `app/services/ws_service.py` | `ConnectionManager` class: `connect`, `disconnect`, `broadcast_to_room`, `send_to_user` — **see multi-worker note below** |
| `app/routers/monitoring.py` | All 4 monitoring routes | `03-routes.md §9` |
| `app/controllers/monitoring_controller.py` | All monitoring functions | `02-controllers.md §8` |
| `app/services/monitoring_service.py` | All monitoring service functions | `02-controllers.md §8` |

> **Note (WebSocket Multi-Worker Scaling — N5):** An in-memory `ConnectionManager` only holds connections for the single Uvicorn worker process that accepted them. When `docker-compose.prod.yml` (Phase 10) runs multiple Uvicorn workers, a broadcast triggered by an ARQ worker or a *different* Uvicorn process will **not** reach clients connected to the other workers. **Required design:** `ws_service.py` must use Redis Pub/Sub as a fan-out bus. Each Uvicorn worker runs a background task that subscribes to a Redis channel (e.g., `cleanplates:ws:dashboard`, `cleanplates:ws:monitoring`). When any service calls `broadcast_to_room(room, payload)`, it publishes to the Redis channel; each worker's subscriber loop then delivers the message to its in-memory connected clients. This is safe and straightforward to implement using `aioredis` subscribe. Implement this pattern from the start in Phase 7 — retrofitting it later breaks all WS clients.
>
> **⚠ M6-fix (Subscriber Lifecycle):** Start the Redis subscriber loop as an `asyncio.create_task(ws_service.subscriber_loop())` explicitly inside the FastAPI `@asynccontextmanager lifespan` in `app/main.py`. This ensures it starts exactly once per worker process and gracefully shuts down. **CRITICAL:** The `subscriber_loop()` method MUST be wrapped in a `while True:` loop with a `try...except ConnectionError` and `await asyncio.sleep(2)` backoff to automatically reconnect if the Redis connection drops, preventing silent permanent WS failures.

### WebSocket Event Types
Wire these publish calls:
- `waste_service.create_waste_entry()` → `ws_service.broadcast_to_room("monitoring", {type:"waste_entry", ...})`
- `warning_service.create_warning()` → `ws_service.broadcast_to_room("dashboard", {type:"warning_issued", ...})`
- `waste_service.ml_heartbeat()` → `ws_service.broadcast_to_room("monitoring", {type:"device_status", ...})`
- `aggregation_worker` (hourly) → `ws_service.broadcast_to_room("dashboard", {type:"kpi_update", ...})`

> **WebSocket Fan-out Architecture (N4-fix):** Do **NOT** use lazy imports to call `ws_service` from `waste_service` or `warning_service`. Instead, `waste_service` and `warning_service` already use `event_bus.publish` (from Phase 4) to emit events to Redis Pub/Sub. In Phase 7, simply have `ws_service` run a background task that **subscribes** to `event_bus.py` channels and pushes received messages to connected WebSocket clients. This completely decouples HTTP services from WebSocket fan-out logic.

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
| `app/schemas/common.py` | Expand with remaining utility schemas (`SystemInfoSchema`, `LogoUrlSchema`, `CacheResultSchema`, `OptimizeResultSchema`, `RestoreResultSchema`, `TempPasswordSchema`) | `05-schemas.md §13` — **N1-fix: base schemas (`PaginatedBase`, `MessageSchema`, `ErrorSchema`) were already created in Phase 1; only add the utility schemas here** |
| `app/routers/roles.py` | 2 role routes | `03-routes.md §16` |
| `app/controllers/roles_controller.py` | `list_roles`, `update_role` | `02-controllers.md §18` |
| `app/services/roles_service.py` | `list_roles`, `update_role` | `02-controllers.md §18` |
| `app/schemas/roles.py` | `RoleSchema`, `RoleUpdateSchema` | `05-schemas.md §16` |

> **Note (M7 — EmailService available here):** `settings_service.py` functions `create_user` and `reset_user_password` send emails. `EmailService` was built in Phase 6, so **no stub is needed in Phase 8** — import `email_service` directly. Do not copy the `# TODO: Wire EmailService` stub pattern from earlier phases.

### Backup System

| File | Purpose |
|------|---------|
| `app/services/backup_service.py` | `create_backup` (use `VACUUM INTO` + compress), `restore_backup` |
| `app/workers/backup_worker.py` | ARQ scheduled backup (`auto_backup`), auto-purge old audit events (`purge_old_audit_events`), **and `restore_backup_task` (M3-fix — on-demand ARQ job enqueued by `settings_service.restore_backup()`)** |

> **⚠ M3-fix (Staged DB Restore):** `settings_service.restore_backup()` enqueues an ARQ job named `"restore_backup_task"`. This function **must** be registered in `backup_worker.py` and included in `arq_settings.WorkerSettings.functions` list. 
> **⚠ CRITICAL (Docker Split-Brain Prevention):** The ARQ task must NOT overwrite `database.db` directly. Overwriting the active DB while Uvicorn workers are connected will corrupt the SQLite database. Instead, the task must extract the backup to a staging file (e.g. `./data/staging_restore.db`) and then write an empty `./data/restart.lock` file. **Both** the FastAPI and ARQ containers must have a background healthcheck or loop monitoring this `.lock` file. When detected, BOTH containers must gracefully exit (`os._exit(0)`). Docker Compose will automatically restart them. The `entrypoint.sh` script detects `staging_restore.db`, replaces the main DB files safely before Uvicorn/ARQ boots, deletes the lock, and starts the app. **⚠ H2-audit-fix (WAL Corruption Prevention):** `entrypoint.sh` must execute `rm -f database.db-wal database.db-shm` **simultaneously** with the `mv staging_restore.db database.db` replacement. If old WAL/SHM files from the previous database are left on disk, SQLite will attempt to replay those old transactions against the new (restored) database file, causing catastrophic data corruption.
>
> **⚠ M9-fix (Backup Integrity):** Because SQLite WAL mode is enabled, standard file copying (`shutil.copy`) of the `.db` file will result in a corrupted backup (pending transactions reside in `.db-wal`). `create_backup` must use `await db.execute(text("VACUUM INTO 'backup.db'"))` to safely snapshot the database.

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

> **Pre-Week-13 Check (L2-fix):** Verify that `docs/praposed-imp/pages/` directory exists and contains UI specs for all 14 dashboard pages before starting Week 13. The Rule Engine UI spec (`docs/praposed-imp/pages/08-rule-engine.md`) is referenced below — it must not be confused with the backend internals doc at `docs/plans/08-rule-engine.md`.

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
| Production Docker Compose | `docker-compose.prod.yml` — fastapi, **arq**, redis, nginx, cloudflared. **⚠ CRITICAL:** Both `fastapi` and `arq` containers must mount the *exact same host volume* (e.g. `./data:/app/data`) for the SQLite DB files to prevent split-brain. **⚠ P5-fix (Uploads Volume):** Both containers must ALSO mount a shared uploads volume (e.g. `./uploads:/app/uploads`) so plate images saved by FastAPI during ML ingestion are accessible to the ARQ worker when generating PDF reports. Without this, container restarts lose all uploaded images permanently. **Both containers must monitor for a `restart.lock` file created by the DB restore task and self-exit when found.** Use a custom `entrypoint.sh` to safely `mv staging_restore.db database.db` on boot before the app starts. |
| ARM64 Dockerfile | `Dockerfile.prod` — multi-stage, slim base. **⚠ M4-audit-fix (WeasyPrint Dependencies):** Must include `RUN apt-get update && apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info` in the Dockerfile to provide the C-libraries required by WeasyPrint for PDF generation. |
| Nginx prod config | `nginx/nginx.conf` — gzip, rate limit, SSL, proxy to :8000 |
| Cloudflare Tunnel | `cloudflare/config.yml` |
| systemd services | `deploy/systemd/cleanplates.service` |
| Indexes review | Verify all indexes in `01-models.md` exist in migrations |(WAL mode enabled in Phase 1 `app/core/database.py` — no action needed here) |
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
11. **DB Session & ARQ Pool Injection Rule:** All service layer functions must explicitly accept `db: AsyncSession` as an argument. Furthermore, any service function that enqueues background jobs must explicitly accept `arq_pool: ArqRedis` as an argument. They must **never** use `Depends(get_db_session)` or `request.app.state.arq_pool` internally. FastAPI Routers resolve these via `Depends` and pass them into the service. ARQ workers pass them via `ctx['db_session_factory']()` and `ctx['redis']`. This completely decouples services from the HTTP lifecycle.
12. **Commit-Before-Enqueue (P2-fix):** Any service function that saves a DB record and then enqueues an ARQ job referencing that record MUST call `await db.commit()` before `await arq_pool.enqueue_job(...)`. The ARQ worker may execute instantly and query for data that the HTTP middleware has not yet committed, causing silent failures.
13. **ARQ Retry on SQLite Locks (P6-fix):** All ARQ worker functions that perform database writes must use ARQ's built-in retry mechanisms (e.g., `max_tries=3` in the job definition or `raise Retry(defer=2)` on `sqlite3.OperationalError`) to gracefully absorb transient SQLite write locks caused by high-concurrency scenarios like bulk ML sync triggering dozens of simultaneous rule evaluations.
14. **CPU-Bound Operations (P1-fix):** All CPU-bound or blocking I/O operations within `async def` functions must be wrapped in `await asyncio.to_thread(...)`. This includes: bcrypt password hashing/verification (`security.py`), WeasyPrint PDF generation (`pdf_generator.py`), and any future synchronous library calls. Failure to do so blocks the ASGI event loop and stalls all concurrent requests and WebSocket connections.
15. **Counter Reconciliation (L3-fix):** `student.warning_count` and `student.penalty_count` are denormalized counters that can drift if a service fails mid-operation (e.g., warning inserted but counter not incremented). `aggregation_service.update_student_status()` (Phase 5) must also reconcile these counters by recomputing them from actual DB data: `warning_count = SELECT COUNT(*) FROM warnings WHERE student_id=X AND status='active'` and `penalty_count = SELECT COUNT(*) FROM penalties WHERE student_id=X AND status='active'`. This self-healing runs on every status update and prevents permanent drift.
16. **Response Schema ORM Config (B4-fix):** Per `05-schemas.md` GLOBAL RULE M7, **every** Pydantic response schema that is populated from SQLAlchemy ORM objects MUST include `model_config = ConfigDict(from_attributes=True)`. This is stated once in the schemas doc but not repeated in each code block. The implementer must apply it to ALL response schemas (`DeviceSchema`, `StudentSchema`, `WasteEntrySchema`, `WarningSchema`, `PenaltySchema`, `EscalationSchema`, `RuleSchema`, `RuleExecutionSchema`, `NotificationSchema`, `ReportSchema`, `ReportScheduleSchema`, `AuditEventSchema`, `FilterPresetSchema`, `BackupSchema`, `RoleSchema`, etc.) — omitting it causes `PydanticUserError` on every ORM read.
