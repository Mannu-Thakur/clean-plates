# CleanPlates — Project Directory Structure

**Backend:** FastAPI | **Frontend:** SvelteKit | **DB:** SQLite + Redis

---

## Backend Directory Tree

```
backend/
├── pyproject.toml                     # All Python dependencies
├── .env                               # Environment variables (gitignored)
├── .env.example                       # Template for .env
├── alembic.ini                        # Alembic config
├── Dockerfile                         # ARM64-compatible multi-stage. **[M4-audit-fix]** Must include `apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info` for WeasyPrint PDF generation.
├── entrypoint.sh                      # Docker entrypoint script (handles staged DB restore). **[H2-audit-fix]** Must execute `rm -f database.db-wal database.db-shm` alongside `mv staging_restore.db database.db` to prevent WAL corruption.
│
├── alembic/
│   ├── env.py                         # Async alembic env
│   └── versions/
│       ├── 001_initial_users.py       # Phase 1: users, refresh_tokens, roles, system_config, audit_events — **[F1-fix]** audit_events moved here from 002 (audit_service.log() is used from Phase 1)
│       ├── 002_devices_students.py    # Phase 2: devices, device_health, students, student_mappings, food_items
│       ├── 003_waste_warnings_rules.py # Phase 3: waste_entries, warnings, escalations, penalties, rules, rule_executions
│       ├── 004_analytics.py           # Phase 5: aggregated_waste, filter_presets (Phase 4 adds no new models)
│       └── 005_notif_config_reports.py # Phase 6: notifications, email_templates, reports, report_schedules, backups
│
├── scripts/
│   ├── seed_roles.py                  # Insert 5 default roles with permissions
│   ├── seed_food_items.py             # Default food catalog
│   ├── seed_config.py                 # Default system config values
│   └── seed_templates.py             # Default email templates
│
├── app/
│   ├── main.py                        # FastAPI app init + middleware registration
│   │
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings class
│   │   ├── database.py                # Async SQLAlchemy engine + AsyncSessionLocal (get_db_session lives in app/middleware/db.py)
│   │   ├── redis.py                   # ARQ pool init + get_arq_pool() dependency (C1-fix: required by waste_service and warning_service for enqueue_job calls)
│   │   └── security.py                # hash_password, verify_password, create/decode tokens
│   │
│   ├── middleware/
│   │   ├── auth.py                    # get_current_user, get_current_user_optional, get_api_key_device
│   │   ├── rbac.py                    # require_roles, require_admin, require_write_access
│   │   ├── logging.py                 # RequestLoggingMiddleware
│   │   ├── rate_limit.py              # Redis-backed RateLimitMiddleware
│   │   ├── error_handler.py           # All exception handlers
│   │   ├── security_headers.py        # SecurityHeadersMiddleware
│   │   ├── ws_auth.py                 # WebSocket auth dependency
│   │   ├── audit.py                   # capture_before(), capture_after() helpers
│   │   └── db.py                      # get_db_session() async dependency
│   │
│   ├── models/
│   │   ├── __init__.py                # Re-export all models for alembic env.py
│   │   ├── base.py                    # SQLAlchemy Base, common mixins (id, created_at, updated_at)
│   │   ├── user.py                    # UserModel, RefreshTokenModel
│   │   ├── role.py                    # RoleModel
│   │   ├── device.py                  # DeviceModel, DeviceHealthModel
│   │   ├── student.py                 # StudentModel, StudentMappingModel
│   │   ├── food.py                    # FoodItemModel
│   │   ├── waste.py                   # WasteEntryModel
│   │   ├── warning.py                 # WarningModel, EscalationModel, PenaltyModel
│   │   ├── rule.py                    # RuleModel, RuleExecutionModel
│   │   ├── notification.py            # NotificationModel, EmailTemplateModel
│   │   ├── report.py                  # ReportModel, ReportScheduleModel
│   │   ├── config.py                  # ConfigModel
│   │   ├── audit.py                   # AuditEventModel
│   │   ├── backup.py                  # BackupModel
│   │   ├── aggregated_waste.py        # AggregatedWasteModel
│   │   └── filter_preset.py           # FilterPresetModel
│   │
│   ├── schemas/
│   │   ├── auth.py                    # LoginSchema, TokenPairSchema, UserSchema, etc.
│   │   ├── devices.py                 # DeviceCreateSchema, DeviceSchema, HeartbeatSchema, etc.
│   │   ├── students.py                # MappingCreateSchema, StudentSchema, StudentWarningsSchema, WasteStatsSchema, etc.
│   │   ├── waste.py                   # WasteEntryCreateSchema, WasteEntrySchema, SyncResultSchema, etc.
│   │   ├── warnings.py                # WarningSchema, PenaltySchema, EscalationSchema, PaginatedWarnings, PaginatedPenalties, etc.
│   │   ├── rules.py                   # RuleCreateSchema, RuleSchema, TestResultSchema, OperatorOptionSchema, ActionOptionSchema, PaginatedRules, etc.
│   │   ├── analytics.py               # OverviewKpisSchema, TrendDataSchema, ImprovementDataSchema, etc.
│   │   ├── notifications.py           # NotificationCreateSchema, NotificationDetailSchema, PaginatedNotifications, etc.
│   │   ├── reports.py                 # ReportConfigSchema, ReportSchema, ScheduleCreateSchema, ScheduleUpdateSchema, PaginatedReports, etc.
│   │   ├── config.py                  # ThresholdSchema, MealTimingSchema, SystemPolicySchema, etc.
│   │   ├── audit.py                   # AuditEventSchema, AuditStatsSchema, etc.
│   │   ├── filter_presets.py          # FilterPresetCreateSchema, FilterPresetSchema, etc.
│   │   ├── templates.py               # TemplateCreateSchema, EmailTemplateSchema, SampleDataSchema, RenderedHtmlSchema, etc.
│   │   ├── settings.py                # UserCreateSchema, UserUpdateSchema, BackupSchema
│   │   ├── roles.py                   # RoleSchema, RoleUpdateSchema
│   │   └── common.py                  # PaginatedBase, MessageSchema, SystemInfoSchema, etc.
│   │
│   ├── routers/
│   │   ├── auth.py                    # /auth/* routes
│   │   ├── devices.py                 # /devices/* routes
│   │   ├── students.py                # /students/* routes
│   │   ├── waste.py                   # /waste/* routes
│   │   ├── ml.py                      # /ml/* routes (API key auth)
│   │   ├── warnings.py                # /warnings, /penalties, /escalations routes
│   │   ├── rules.py                   # /rules/* routes
│   │   ├── analytics.py               # /analytics/* routes
│   │   ├── monitoring.py              # /monitoring/* routes
│   │   ├── notifications.py           # /notifications/* routes
│   │   ├── reports.py                 # /reports/* routes
│   │   ├── config.py                  # /config/* routes
│   │   ├── templates.py               # /templates/* routes
│   │   ├── settings.py                # /settings/* routes
│   │   ├── audit.py                   # /audit/* routes
│   │   ├── roles.py                   # /roles/* routes
│   │   ├── filter_presets.py          # /filters/* routes
│   │   ├── ws.py                      # WebSocket routes (/ws/*)
│   │   └── health.py                  # /health route
│   │
│   ├── controllers/
│   │   ├── auth_controller.py
│   │   ├── device_controller.py
│   │   ├── student_controller.py
│   │   ├── waste_controller.py
│   │   ├── ml_controller.py           # MLIngestionController (02-controllers.md §15)
│   │   ├── warning_controller.py
│   │   ├── rule_controller.py
│   │   ├── analytics_controller.py
│   │   ├── monitoring_controller.py
│   │   ├── notification_controller.py
│   │   ├── report_controller.py
│   │   ├── config_controller.py
│   │   ├── template_controller.py
│   │   ├── settings_controller.py
│   │   ├── audit_controller.py
│   │   ├── filter_preset_controller.py # FilterPresetController (02-controllers.md §17)
│   │   ├── roles_controller.py         # RolesController (02-controllers.md §18)
│   │   └── ws_controller.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   ├── student_service.py
│   │   ├── waste_service.py
│   │   ├── warning_service.py
│   │   ├── rule_engine_service.py
│   │   ├── analytics_service.py
│   │   ├── aggregation_service.py
│   │   ├── monitoring_service.py
│   │   ├── notification_service.py
│   │   ├── email_service.py
│   │   ├── report_service.py
│   │   ├── config_service.py
│   │   ├── template_service.py
│   │   ├── settings_service.py
│   │   ├── audit_service.py
│   │   ├── backup_service.py
│   │   ├── filter_preset_service.py   # FilterPresetController backing service (02-controllers.md §17)
│   │   ├── roles_service.py           # RolesController backing service (02-controllers.md §18)
│   │   └── ws_service.py
│   │
│   ├── engine/
│   │   ├── condition_matcher.py       # match(), matchNumeric(), matchFrequency(), etc.
│   │   ├── action_executor.py         # execute(), generateWarning(), sendEmail(), etc.
│   │   └── event_bus.py               # publish(), subscribe() — Redis pub/sub
│   │
│   ├── generators/
│   │   ├── pdf_generator.py           # WeasyPrint PDF generation
│   │   ├── csv_generator.py           # CSV export
│   │   └── excel_generator.py         # OpenPyXL Excel generation
│   │
│   └── workers/
│       ├── arq_settings.py            # ARQ WorkerSettings, cron schedule
│       ├── rule_worker.py             # Subscribe to events → evaluate rules
│       ├── aggregation_worker.py      # Hourly aggregation, daily scoring
│       ├── report_worker.py           # Generate reports, run schedules, send scheduled notifs
│       └── backup_worker.py           # Scheduled backups, purge old audit events
│
├── uploads/                           # Logo, CSV imports (gitignored)
├── reports/                           # Generated report files (gitignored)
├── backups/                           # DB backup ZIPs (gitignored)
└── logs/                              # App logs (gitignored)
```

---

## Frontend Directory Tree

```
frontend/
├── package.json
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
│
├── src/
│   ├── app.html
│   ├── app.css                        # Global styles + Tailwind
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts              # Fetch wrapper: auth header, refresh logic, error handling
│   │   │   ├── ws.ts                  # WebSocket client: connect, reconnect, room subscriptions
│   │   │   ├── auth.api.ts
│   │   │   ├── students.api.ts
│   │   │   ├── waste.api.ts
│   │   │   ├── warnings.api.ts
│   │   │   ├── rules.api.ts
│   │   │   ├── analytics.api.ts
│   │   │   ├── monitoring.api.ts
│   │   │   ├── notifications.api.ts
│   │   │   ├── reports.api.ts
│   │   │   ├── config.api.ts
│   │   │   ├── devices.api.ts
│   │   │   ├── settings.api.ts
│   │   │   └── audit.api.ts
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.store.ts          # currentUser, isAuthenticated, login(), logout()
│   │   │   ├── overview.store.ts
│   │   │   ├── monitoring.store.ts    # liveEntries, liveAlerts, devices
│   │   │   ├── analytics.store.ts
│   │   │   ├── students.store.ts
│   │   │   ├── warnings.store.ts
│   │   │   ├── rules.store.ts
│   │   │   ├── notifications.store.ts
│   │   │   ├── reports.store.ts
│   │   │   ├── config.store.ts
│   │   │   ├── devices.store.ts
│   │   │   └── audit.store.ts
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   ├── Header.svelte
│   │   │   │   └── PageWrapper.svelte
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.svelte
│   │   │   │   ├── BarChart.svelte
│   │   │   │   ├── DonutChart.svelte
│   │   │   │   ├── GaugeChart.svelte
│   │   │   │   └── HeatmapChart.svelte
│   │   │   ├── shared/
│   │   │   │   ├── KpiCard.svelte
│   │   │   │   ├── DataTable.svelte
│   │   │   │   ├── Pagination.svelte
│   │   │   │   ├── FilterBar.svelte
│   │   │   │   ├── StatusBadge.svelte
│   │   │   │   ├── Modal.svelte
│   │   │   │   └── Toast.svelte
│   │   │   └── features/
│   │   │       ├── MapStudentModal.svelte
│   │   │       ├── IssueWarningModal.svelte
│   │   │       ├── RuleBuilder.svelte
│   │   │       ├── ConditionBuilder.svelte
│   │   │       ├── ActionBuilder.svelte
│   │   │       ├── ComposeNotification.svelte
│   │   │       ├── ReportBuilder.svelte
│   │   │       └── TemplateEditor.svelte
│   │   │
│   │   └── types/
│   │       └── index.ts               # TypeScript interfaces matching backend schemas
│   │
│   └── routes/
│       ├── +layout.svelte             # Root layout (auth guard)
│       ├── login/
│       │   └── +page.svelte           # Page 01
│       └── dashboard/
│           ├── +layout.svelte         # Sidebar + header layout
│           ├── +page.svelte           # Page 02 - Overview
│           ├── monitoring/
│           │   └── +page.svelte       # Page 03 - Live Monitoring
│           ├── analytics/
│           │   └── +page.svelte       # Page 04 - Analytics
│           ├── students/
│           │   ├── +page.svelte       # Page 05 - Students List
│           │   └── [id]/
│           │       └── +page.svelte   # Page 06 - Student Intelligence
│           ├── warnings/
│           │   └── +page.svelte       # Page 07 - Warnings & Penalties
│           ├── rules/
│           │   └── +page.svelte       # Page 08 - Rule Engine
│           ├── notifications/
│           │   └── +page.svelte       # Page 09 - Notification Center
│           ├── reports/
│           │   └── +page.svelte       # Page 10 - Reports
│           ├── devices/
│           │   └── +page.svelte       # Page 11 - Devices
│           ├── config/
│           │   └── +page.svelte       # Page 12 - Configuration
│           ├── settings/
│           │   └── +page.svelte       # Page 13 - Settings
│           └── audit/
│               └── +page.svelte       # Page 14 - Audit Log
│
└── static/
    └── favicon.svg
```

---

## Docker Compose Structure

```
docker-compose.yml
├── fastapi          → Dockerfile, port 8000, mounts: ./uploads, ./reports, ./backups, ./data, ./logs
├── arq-worker       → Same image as fastapi, command: arq app.workers.arq_settings.WorkerSettings
├── redis            → redis:7-alpine, port 6379, volume: redis-data
└── nginx            → nginx:alpine, ports 80/443, mounts: ./nginx.conf, frontend/build

volumes:
  sqlite-data        → /data/ (SQLite db file)
  redis-data         → Redis persistence
  uploads            → /uploads/
  reports            → /reports/
  backups            → /backups/
  logs               → /logs/ — **[F9-fix]** Required for file-based log retention (LOG_RETENTION_DAYS setting)
```
