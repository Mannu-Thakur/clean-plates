# CleanPlates — Controllers (FastAPI Routers/Services)

**Convention:** Each "controller" = FastAPI router file + its backing service class.  
**Format per function:** `name(inputs) → output | work`

---

## 1. AuthController
**File:** `app/controllers/auth_controller.py`  
**Service:** `app/services/auth_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `login` | `email, password, remember_me` | `TokenPair + UserSchema` | Hash-compare password → create access+refresh tokens → log audit event → return tokens |
| `logout` | `refresh_token, current_user` | `void` | Revoke refresh token in DB → log audit |
| `refresh_token` | `refresh_token` | `TokenPair` | Verify refresh token hash in DB → issue new access token → rotate refresh token |
| `get_current_user` | `access_token (header)` | `UserSchema` | Decode JWT → fetch user from DB → return profile |
| `forgot_password` | `email` | `void` | Find user by email → generate reset token → send email (fire-and-forget) |
| `reset_password` | `token, new_password` | `void` | Verify reset token → hash new password → save → invalidate token |

---

## 2. DeviceController
**File:** `app/controllers/device_controller.py`  
**Service:** `app/services/device_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_devices` | `status_filter, page, size` | `PaginatedDevices` | Query devices table with optional status filter → return paginated list with health summary |
| `register_device` | `DeviceCreateSchema` | `DeviceSchema` | Create device record → generate API key → hash and store → return device with raw API key (once) |
| `get_device` | `device_id` | `DeviceSchema` | Fetch device by ID → 404 if not found |
| `update_device` | `device_id, DeviceUpdateSchema` | `DeviceSchema` | Partial update device identity fields → log audit |
| `get_device_health` | `device_id` | `HealthDataSchema` | Fetch latest health record for device |
| `get_health_history` | `device_id, period` | `HealthHistorySchema` | Query device_health by device_id within period → return time-series list |
| `restart_service` | `device_id` | `void` | Publish restart command to Redis channel `cleanplates:devices:{device_id}:commands` with payload `{"command":"restart"}` → log audit. **Note:** The Pi must periodically poll `GET /devices/{device_id}/commands` or subscribe to this Redis channel via a background loop to receive the command. This route is a best-effort signal only — no delivery guarantee. |
| `trigger_sync` | `device_id` | `SyncResultSchema` | Mark device for sync → return pending entry count. **Note:** Returns `SyncResultSchema` with only `total_received` populated (= number of offline entries pending upload); `inserted`, `skipped`, and `errors` will be `0`/`[]`. |
| `decommission` | `device_id` | `void` | Set device status=decommissioned → log audit |

---

## 3. StudentController
**File:** `app/controllers/student_controller.py`  
**Service:** `app/services/student_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_students` | `status, hostel, branch, year, page, size, sort, order` | `PaginatedStudents` | Join students + student_mappings → apply filters → return with mapping status indicator |
| `get_student` | `student_id` | `StudentDetailSchema` | Fetch student + mapping → 404 if not found |
| `map_student_id` | `student_id, MappingCreateSchema` | `StudentSchema` | Create/upsert student_mapping record → log audit event |
| `update_mapping` | `student_id, MappingUpdateSchema` | `StudentSchema` | PATCH mapping fields (name, roll, branch, year, hostel, room, email) → log audit |
| `update_student_profile` | `student_id, MappingUpdateSchema` | `StudentSchema` | PATCH top-level student profile fields (hostel, room, etc.) — bound to `PATCH /{student_id}` route → log audit |
| `import_mapping_csv` | `csv_file` | `ImportResultSchema` | Parse CSV rows → validate each (device_id, name, roll, year, branch) → bulk upsert mappings → return success/error counts |
| `export_students` | `format: str (query param, one of: csv\|excel), filters (same query params as list_students)` | `FileResponse` | Query students+mappings with filters → generate CSV/Excel → return as file download |
| `bulk_warn` | `student_ids[], reason` | `void` | For each student_id → call WarningService.create_warning() (stub available from Phase 2) → send notifications |
| `get_student_stats` | `student_id, period` | `WasteStatsSchema` | Aggregate waste_entries for student in period → compute avg, total, peak meal, food breakdown |
| `get_student_timeline` | `student_id, period` | `TimelineSchema` | Daily waste entries grouped by date → return chart-ready list |
| `get_food_breakdown` | `student_id, period` | `FoodBreakdownSchema` | Group waste_entries.food_items by food name → return totals per food item |
| `get_meal_pattern` | `student_id, period` | `MealPatternSchema` | Group waste_entries by meal_type → return avg waste per meal |
| `get_improvement_trend` | `student_id` | `ImprovementSchema` | Compare weekly avg waste rolling → compute % improvement week-over-week |
| `get_student_history` | `student_id, page, size` | `PaginatedEntries` | Paginated waste_entries for student ordered by timestamp desc |
| `get_student_warnings` | `student_id` | `StudentWarningsSchema` | All warnings + penalties for student ordered by created_at desc |
| `create_warning` | `student_id, WarningCreateSchema, current_user` | `WarningSchema` | Delegates directly to `WarningService.create_warning()` — no duplicated logic |
| `create_penalty_direct` | `student_id, PenaltyCreateSchema, current_user` | `PenaltySchema` | Create a penalty directly on a student (no source warning) → increment student.penalty_count → send email if flag set → update student status → log audit |

---

## 4. WasteController
**File:** `app/controllers/waste_controller.py`  
**Service:** `app/services/waste_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `create_waste_entry` | `WasteEntryCreateSchema (api_key auth)` | `WasteEntrySchema` | Validate payload → **resolve `device_serial → device_id` UUID via DB lookup** (same as `bulk_sync`) → resolve `student_device_id → student_id` UUID via DB lookup → resolve meal type from config time windows → classify severity → save to DB → publish `waste_entry_created` event to rule engine → push WebSocket event |
| `bulk_sync` | `entries[] (api_key auth)` | `SyncResultSchema` | Batch insert waste entries from offline queue → deduplicate by **(device_serial + timestamp)**: resolve `device_serial → device_id` UUID first, then skip any entry where `(device_id, timestamp)` already exists in DB → trigger rule evaluation for each new entry → return inserted/skipped counts |
| `get_entry` | `entry_id` | `WasteEntryDetailSchema` | Fetch entry with student mapping and device info |
| `list_entries` | `student_id, device_id, meal_type, date_from, date_to, page, size` | `PaginatedEntries` | Filter waste_entries → paginated result |
| `get_current_session` | `device_id` | `SessionSummarySchema` | Resolve active meal from config time windows by current time → count entries in session → return live summary |
| `get_recent_entries` | `device_id, limit` | `WasteEntrySchema[]` | Latest N entries for device ordered by timestamp desc |

---

## 5. WarningController
**File:** `app/controllers/warning_controller.py`  
**Service:** `app/services/warning_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_warnings` | `status, priority, student_id, date_from, date_to, page, size` | `PaginatedWarnings` | Query warnings with filters → join student_mappings for name display |
| `get_warning_stats` | `void` | `WarningSummarySchema` | Count active, escalated, total penalties → return summary cards data |
| `create_warning` | `student_id, level, reason, rule_id, waste_entry_id, send_email` | `WarningSchema` | Insert warning record → increment student.warning_count → if send_email: queue email notification → log audit |
| `resolve_warning` | `warning_id, resolution_note, current_user` | `void` | Set warning.status=resolved → decrement student.warning_count → log audit |
| `escalate_warning` | `warning_id, EscalateSchema, current_user` | `EscalationSchema` | Insert escalation record → set warning.status=escalated → send notification to target role → log audit |
| `apply_penalty` | `warning_id, current_user` | `PenaltySchema` | Create penalty from warning → set warning.status=converted_to_penalty → update student status to red → send email → log audit |
| `bulk_resolve` | `warning_ids[], resolution_note, current_user` | `void` | Batch resolve warnings → update student.warning_count for each |
| `export_warnings` | `format, filters` | `FileResponse` | Apply same filters as list_warnings → generate CSV/Excel → return as file download |
| `list_penalties` | `status, student_id, page, size` | `PaginatedPenalties` | Query penalties with filters |
| `revoke_penalty` | `penalty_id, reason, current_user` | `void` | Set penalty.status=revoked → recalculate student status → log audit |
| `list_escalations` | `status` | `EscalationSchema[]` | Query escalations with status filter |
| `review_escalation` | `escalation_id, decision, review_note, current_user` | `void` | Set escalation.status → if approved: apply_penalty() → if rejected: resolve_warning() → log audit |

---

## 6. RuleController
**File:** `app/controllers/rule_controller.py`  
**Service:** `app/services/rule_engine_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_rules` | `type, priority, status, sort, page, size` | `PaginatedRules` | Query rules where is_deleted=false → apply filters |
| `get_rule` | `rule_id` | `RuleSchema` | Fetch rule by ID → 404 if deleted |
| `create_rule` | `RuleCreateSchema, current_user` | `RuleSchema` | Validate rule JSON structure → insert rule → log audit → register with engine |
| `update_rule` | `rule_id, RuleUpdateSchema, current_user` | `RuleSchema` | Validate updated rule → partial update → log audit with before/after state |
| `delete_rule` | `rule_id, current_user` | `void` | Soft delete (is_deleted=true, active=false) → log audit |
| `toggle_rule` | `rule_id, active: bool, current_user` | `void` | Set rule.active → log audit |
| `duplicate_rule` | `rule_id, current_user` | `RuleSchema` | Clone rule record with name "(Copy of X)" → set active=false → insert |
| `test_rule` | `rule_id, TestPayloadSchema` | `TestResultSchema` | Run condition matcher against provided sample data → return which conditions match + what actions would fire (no side effects) |
| `simulate_rule` | `rule_id, date_from, date_to` | `SimulationResultSchema` | Fetch historical waste_entries in period → run condition matcher for each → count matches + projected action outcomes (no side effects) |
| `get_rule_executions` | `rule_id, page, size` | `PaginatedExecutions` | Query rule_executions by rule_id → paginated |
| `get_available_fields` | `void` | `FieldOptionSchema[]` | Return static metadata: available condition fields (waste_grams, meal_type, frequency, branch, etc.) |
| `get_available_operators` | `void` | `OperatorOptionSchema[]` | Return static metadata: operators per field type (gt, lt, eq, contains, etc.) |
| `get_available_actions` | `void` | `ActionOptionSchema[]` | Return static metadata: available action types and their param schemas |
| `get_rule_chains` | `void` | `ChainDataSchema` | Query rules where chain_to_rule_id is not null → build graph nodes+edges |

---

## 7. AnalyticsController
**File:** `app/controllers/analytics_controller.py`  
**Service:** `app/services/analytics_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `get_overview` | `period` | `OverviewKpisSchema` | Query aggregated_waste for global scope → compute KPI cards (total waste, avg, reduction %) → count students by status → count active devices → count alerts today |
| `get_weekly_trend` | `device_id?` | `TrendDataSchema` | Daily totals for last 7 days → return `[{date, total_grams}]` |
| `get_monthly_comparison` | `void` | `ComparisonDataSchema` | Compare current month daily avg vs previous month daily avg |
| `get_meal_distribution` | `period, device_id?` | `DistributionDataSchema` | Group waste_entries by meal_type in period → return `[{meal, total, pct}]` |
| `get_food_waste_distribution` | `period, limit` | `FoodRankingSchema` | Unnest food_items JSON → group by food name → sort by total desc → return top N |
| `get_top_contributors` | `FilterParams, limit` | `StudentRankingSchema[]` | Aggregate waste per student in filter period → sort desc → join mappings for names |
| `get_improvement_tracking` | `FilterParams` | `ImprovementDataSchema[]` | Compare student avg waste: current period vs previous same-length period → rank by improvement |
| `get_peak_waste` | `FilterParams` | `PeakDataSchema` | Group waste_entries by hour, weekday, meal → find max values → return peak hour, meal, weekday |
| `get_sustainability_scores` | `branch?, year?` | `ScoreDistributionSchema` | Query students.sustainability_score → group by score band → optional branch/year filter |
| `get_trends` | `type, FilterParams` | `TrendDataSchema` | `weekly`, `monthly_comparison`, or `semester` trend data |

---

## 8. MonitoringController
**File:** `app/controllers/monitoring_controller.py`  
**Service:** `app/services/monitoring_service.py`

> **Dependency Constraint (one-way):** `monitoring_service` imports `waste_service` to delegate `get_current_session()`. **`waste_service` must never import from `monitoring_service`** — doing so creates a circular import. All WebSocket broadcasts originating in `waste_service` must call `ws_service.broadcast_to_room()` directly, not route through `monitoring_service`.

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `get_current_session` | `device_id?` | `SessionSummarySchema` | Resolve active meal from config time windows by current time → count today's entries in that session → return live summary. **Note:** Delegates to `waste_service.get_current_session()` internally — do not duplicate the DB query logic here. |
| `get_recent_entries` | `device_id?, limit` | `WasteEntrySchema[]` | Latest N waste entries → join student_mapping for name display |
| `get_device_statuses` | `void` | `DeviceStatusSchema[]` | All devices → latest health record each → classify status |
| `acknowledge_alert` | `notification_id, current_user` | `void` | Set notification is_read=true → log audit |

---

## 9. NotificationController
**File:** `app/controllers/notification_controller.py`  
**Service:** `app/services/notification_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_notifications` | `tab, type, channel, page, size` | `PaginatedNotifications` | Query notifications by tab (inbox=unread, sent, scheduled) → apply type/channel filters |
| `get_notification` | `notif_id` | `NotificationDetailSchema` | Fetch notification + delivery status |
| `mark_read` | `notif_id, current_user` | `void` | Set notification.is_read=true |
| `mark_all_read` | `current_user` | `void` | Bulk update is_read=true for current user's unread notifications |
| `delete_notification` | `notif_id, current_user` | `void` | Soft delete notification record |
| `send_notification` | `NotificationCreateSchema, current_user` | `NotificationSchema` | Resolve recipients → insert notification record → dispatch via email/dashboard per channel → update status |
| `send_broadcast` | `BroadcastSchema, current_user` | `BroadcastResultSchema` | Resolve group recipients (branch/hostel/year/all) → bulk insert notification records → queue email batch |
| `schedule_notification` | `ScheduleNotifSchema, current_user` | `NotificationSchema` | Insert notification with scheduled_at set → ARQ worker will pick up at scheduled time |
| `retry_failed` | `notif_id` | `void` | Reset status=pending, retry_count=0 → re-queue for dispatch |
| `get_notification_stats` | `void` | `NotifStatsSchema` | Count unread, sent_today, failed, pending |

---

## 10. ReportController
**File:** `app/controllers/report_controller.py`  
**Service:** `app/services/report_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_reports` | `type, date_from, date_to, page, size` | `PaginatedReports` | Query reports table with filters → return list with download availability |
| `generate_report` | `ReportConfigSchema, current_user` | `ReportSchema` | Insert report record (status=pending) → enqueue ARQ task → return report ID for polling |
| `download_report` | `report_id` | `FileResponse` | Fetch report.file_path → validate exists → stream file |
| `delete_report` | `report_id, current_user` | `void` | Delete file from disk → remove DB record → log audit |
| `list_schedules` | `void` | `ReportScheduleSchema[]` | Query report_schedules |
| `create_schedule` | `ScheduleCreateSchema, current_user` | `ReportScheduleSchema` | Insert schedule → compute next_run → log audit |
| `update_schedule` | `schedule_id, ScheduleUpdateSchema` | `ReportScheduleSchema` | Update schedule fields → recompute next_run |
| `delete_schedule` | `schedule_id` | `void` | Delete schedule record → log audit |

---

## 11. ConfigController
**File:** `app/controllers/config_controller.py`  
**Service:** `app/services/config_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `get_config` | `section` | `ConfigDataSchema` | Query system_config by section → return all key-value pairs as structured object. **⚠ Default fallback (N1):** If no rows exist for the requested section (e.g., during Phase 1 before `seed_config.py` runs), return the section's Pydantic schema defaults (`ThresholdSchema`, `SystemPolicySchema`, etc.) as a dict. Never raise 404 or return empty — `waste_service` and `aggregation_service` call this from Phase 3 onwards and expect usable values. |
| `update_config` | `section, ConfigUpdateSchema, current_user` | `void` | Validate `data` against the section-specific schema (e.g., `ThresholdSchema` for `thresholds`) → upsert config keys → log audit with before/after |
| `reset_defaults` | `section, current_user` | `ConfigDataSchema` | Replace section config with hardcoded defaults → log audit |
| `get_meal_timings` | `void` | `MealTimingSchema[]` | Fetch meals config from system_config → return list |
| `update_meal_timings` | `MealTimingSchema[], current_user` | `void` | Replace meals config value → log audit |
| `get_branches` | `void` | `BranchSchema[]` | Fetch branches from system_config |
| `update_branches` | `BranchSchema[], current_user` | `void` | Replace branches config → log audit |
| `get_thresholds` | `void` | `ThresholdSchema` | Fetch thresholds section |
| `update_thresholds` | `ThresholdSchema, current_user` | `void` | Update threshold values in system_config via `config_service`. **Note:** The rule engine reads thresholds directly from DB on each evaluation (stateless) — no cache invalidation or engine notification needed. |
| `get_system_policies` | `void` | `SystemPolicySchema` | Fetch system section |
| `update_system_policies` | `SystemPolicySchema, current_user` | `void` | Update system config → apply changes (e.g., log retention) → log audit |

---

## 12. TemplateController
**File:** `app/controllers/template_controller.py`  
**Service:** `app/services/template_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_templates` | `type?` | `EmailTemplateSchema[]` | Query email_templates where is_deleted=false |
| `create_template` | `TemplateCreateSchema, current_user` | `EmailTemplateSchema` | Insert template → extract variables from Jinja2 body → store in variables field → log audit |
| `get_template` | `template_id` | `EmailTemplateSchema` | Fetch template |
| `update_template` | `template_id, TemplateUpdateSchema, current_user` | `EmailTemplateSchema` | Update fields → re-extract variables → log audit |
| `delete_template` | `template_id, current_user` | `void` | Check is_default=false → soft delete → log audit |
| `preview_template` | `template_id, SampleDataSchema` | `RenderedHtmlSchema` | Render Jinja2 template with sample data → return HTML string |

---

## 13. SettingsController
**File:** `app/controllers/settings_controller.py`  
**Service:** `app/services/settings_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_users` | `void` | `UserSchema[]` | Query users table → return list |
| `create_user` | `UserCreateSchema, current_user` | `UserSchema` | Hash temp password → insert user → send welcome email → log audit |
| `update_user` | `user_id, UserUpdateSchema, current_user` | `UserSchema` | Update user fields → log audit |
| `deactivate_user` | `user_id, current_user` | `void` | Set is_active=false → revoke all refresh tokens → log audit |
| `reset_user_password` | `user_id, current_user` | `TempPasswordSchema` | Generate temp password → hash → update → email user → log audit |
| `get_security_config` | `void` | `SecurityConfigSchema` | Fetch security section from system_config |
| `update_security_config` | `SecurityConfigSchema, current_user` | `void` | Validate values → update config → log audit |
| `list_backups` | `void` | `BackupSchema[]` | Query backups table ordered by created_at desc |
| `trigger_backup` | `current_user` | `BackupSchema` | Insert backup record → enqueue ARQ backup task → return record |
| `download_backup` | `backup_id` | `FileResponse` | Fetch backup.file_path → stream ZIP file |
| `restore_backup` | `backup_file, current_user` | `RestoreResultSchema` | Validate file → enqueue restore task → log audit (CAUTION: destructive) |
| `get_appearance` | `void` | `AppearanceConfigSchema` | Fetch appearance config section |
| `update_appearance` | `AppearanceConfigSchema, current_user` | `void` | Update appearance config → log audit |
| `upload_logo` | `image_file, current_user` | `LogoUrlSchema` | Validate file type/size → save to uploads → update config logo_path → return URL |
| `clear_cache` | `current_user` | `CacheResultSchema` | Flush Redis cache → log audit → return success |
| `optimize_db` | `current_user` | `OptimizeResultSchema` | Run SQLite VACUUM + ANALYZE → return freed space |
| `get_system_info` | `void` | `SystemInfoSchema` | Collect OS version, Python version, DB file size, uptime, disk usage → return |
| `export_all_data` | `current_user` | `FileResponse` | Dump SQLite + config + uploads → package ZIP → stream as download → log audit |

---

## 14. AuditController
**File:** `app/controllers/audit_controller.py`  
**Service:** `app/services/audit_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_events` | `user_id, event_type, resource_type, date_from, date_to, q, sort, page, size` | `PaginatedAuditEvents` | Query audit_events with all filters → full-text search on summary if q provided |
| `get_event` | `event_id` | `AuditEventDetailSchema` | Fetch full event including before_state, after_state, metadata |
| `get_stats` | `period` | `AuditStatsSchema` | Count events by type today → return stats bar data |
| `get_timeline` | `FilterParams` | `TimelineDataSchema` | Group events by user+day → return structured timeline |
| `export_log` | `FilterParams, format` | `FileResponse` | Apply filters → generate CSV → stream download |
| `log` | `AuditEventPayload` | `void` | **Internal only** — insert audit_event record (called by other services) |
| `purge_old_events` | `retention_days` | `int` | Delete events older than retention_days → return deleted count (called by ARQ scheduler) |

---

## 15. MLIngestionController
**File:** `app/controllers/ml_controller.py`  
**Service:** `app/services/waste_service.py` (shared)

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `ingest_detection` | `DetectionPayload (api_key auth)` | `WasteEntrySchema` | Validate payload → lookup student by device_id → create waste entry → trigger rule engine → push WS event |
| `bulk_ingest` | `DetectionPayload[] (api_key auth)` | `SyncResultSchema` | Deduplicate by (device_id+timestamp) → batch insert → trigger rules → return counts |
| `ml_heartbeat` | `HeartbeatPayload (api_key auth)` | `void` | Update device.last_heartbeat → insert health snapshot |

---

## 16. WebSocketController
**File:** `app/controllers/ws_controller.py`  
**Service:** `app/services/ws_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `ws_dashboard` | `WebSocket, current_user` | `void` | Accept → join `dashboard` room → push KPI updates, rule events → handle ping/disconnect |
| `ws_monitoring` | `WebSocket, current_user` | `void` | Accept → join `monitoring` room → push waste entries, alerts, device status → handle pause/filter messages from client |

---

## Internal Services (No Direct Routes)

### RuleEngineService
**File:** `app/services/rule_engine_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `evaluate_event` | `event_type, event_data` | `EvaluationResult[]` | Load active rules → for each: run ConditionMatcher → if matched: run ActionExecutor → log RuleExecution |
| `match_conditions` | `rule.conditions, event_data` | `bool` | Evaluate AND/OR condition groups with field+operator+value |
| `execute_actions` | `rule.actions, context` | `ActionResult[]` | Dispatch each action: generate_warning, send_email, increase_penalty, classify_student, etc. |

### AggregationService
**File:** `app/services/aggregation_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `run_hourly_aggregation` | `void` | `void` | Group last hour's waste_entries by scope types → upsert aggregated_waste |
| `run_daily_aggregation` | `date` | `void` | Aggregate yesterday's data for all scopes → upsert |
| `compute_sustainability_scores` | `void` | `void` | For each student: compute score from 5 factors → update student.sustainability_score |
| `update_student_status` | `student_id` | `void` | Compute status (green/yellow/orange/red) from avg_waste_grams → update student.status |
| `check_device_offline_status` | `void` | `void` | **(G3)** Read threshold from `config_service.get_config("device")["device_offline_threshold_minutes"]` (default 10) → query devices where `last_heartbeat < now − threshold` AND status != `decommissioned` → publish `device_offline` event to event bus for each; also called by `aggregation_worker` hourly |

### EmailService
**File:** `app/services/email_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `send_email` | `to, subject, body_html` | `SendResultSchema` | aiosmtplib send → update notification status |
| `send_bulk` | `recipients[], template_id, context_data` | `BulkResultSchema` | Render template per recipient → batch send → return success/fail counts |
| `render_template` | `template_id, context_data` | `str` | Fetch template → Jinja2 render with context |

---

## 17. FilterPresetController
**File:** `app/controllers/filter_preset_controller.py`  
**Service:** `app/services/filter_preset_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_presets` | `current_user` | `FilterPresetSchema[]` | Query filter_presets where user_id=current_user.id → return list |
| `save_preset` | `PresetCreateSchema, current_user` | `FilterPresetSchema` | Insert filter_preset record for current user → return created |
| `get_preset` | `preset_id, current_user` | `FilterPresetSchema` | Fetch preset → 404 if not found → 403 if not owned by user |
| `update_preset` | `preset_id, FilterPresetUpdateSchema, current_user` | `FilterPresetSchema` | Verify ownership → partial update name/filter_state → return updated |
| `delete_preset` | `preset_id, current_user` | `void` | Verify ownership → delete record |

---

## 18. RolesController
**File:** `app/controllers/roles_controller.py`  
**Service:** `app/services/roles_service.py`

| Function | Input | Output | Work |
|----------|-------|--------|------|
| `list_roles` | `void` | `RoleSchema[]` | Query all roles → return list with permissions |
| `update_role` | `role_id, RoleUpdateSchema, current_user` | `RoleSchema` | Validate role exists → update permissions JSON → log audit with before/after state |
