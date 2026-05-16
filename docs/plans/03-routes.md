# CleanPlates — API Routes

**Base prefix:** `/api/v1`  
**Auth:** JWT Bearer unless marked `[API_KEY]` (ML pipeline) or `[PUBLIC]`  
**Roles:** `SA`=Super Admin, `IA`=Institution Admin, `MA`=Mess Admin, `AV`=Analytics Viewer, `SO`=Staff Operator

---

## 1. Auth Routes
**Router file:** `app/routers/auth.py`  **Prefix:** `/auth`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| POST | `/login` | PUBLIC | `login` | Authenticate, return JWT pair |
| POST | `/logout` | Any | `logout` | Revoke refresh token |
| POST | `/refresh` | PUBLIC | `refresh_token` | Exchange refresh token for new access token |
| GET | `/me` | Any | `get_current_user` | Get current user profile |
| POST | `/forgot-password` | PUBLIC | `forgot_password` | Send password reset email |
| POST | `/reset-password` | PUBLIC | `reset_password` | Set new password via reset token |

---

## 2. Device Routes
**Router file:** `app/routers/devices.py`  **Prefix:** `/devices`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA | `list_devices` | List all devices (filterable by status) |
| POST | `/` | SA, IA | `register_device` | Register a new Raspberry Pi device |
| GET | `/{device_id}` | SA, IA, MA | `get_device` | Get device details |
| PATCH | `/{device_id}` | SA, IA | `update_device` | Update device identity info |
| GET | `/{device_id}/health` | SA, IA, MA | `get_device_health` | Latest health snapshot |
| GET | `/{device_id}/health/history` | SA, IA, MA | `get_health_history` | Health time-series (query: `period`) |
| POST | `/{device_id}/restart` | SA, IA | `restart_service` | Trigger service restart on device |
| POST | `/{device_id}/sync` | SA, IA, MA | `trigger_sync` | Manual data sync trigger |
| POST | `/{device_id}/decommission` | SA, IA | `decommission` | Mark device as decommissioned |

---

## 3. Student Routes
**Router file:** `app/routers/students.py`  **Prefix:** `/students`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA, AV | `list_students` | Paginated student list with filters |
| GET | `/export` | SA, IA, MA | `export_students` | Download student list as CSV/Excel |
| POST | `/import-mapping` | SA, IA, MA | `import_mapping_csv` | Bulk CSV import of device_id→student mappings |
| POST | `/bulk/warn` | SA, IA, MA | `bulk_warn` | Send warnings to multiple students |
| GET | `/{student_id}` | SA, IA, MA, AV | `get_student` | Student profile + mapping info |
| POST | `/{student_id}/map` | SA, IA, MA | `map_student_id` | Map device ID to student identity |
| PATCH | `/{student_id}/map` | SA, IA, MA | `update_mapping` | Update existing student mapping |
| GET | `/{student_id}/stats` | SA, IA, MA, AV | `get_student_stats` | Waste stats for period |
| GET | `/{student_id}/timeline` | SA, IA, MA, AV | `get_student_timeline` | Daily waste timeline |
| GET | `/{student_id}/food-breakdown` | SA, IA, MA, AV | `get_food_breakdown` | Food item waste breakdown |
| GET | `/{student_id}/meal-pattern` | SA, IA, MA, AV | `get_meal_pattern` | Waste by meal type |
| GET | `/{student_id}/improvement` | SA, IA, MA, AV | `get_improvement_trend` | Week-over-week improvement trend |
| GET | `/{student_id}/history` | SA, IA, MA, AV | `get_student_history` | Paginated waste entry history |
| GET | `/{student_id}/warnings` | SA, IA, MA | `get_student_warnings` | All warnings and penalties |
| POST | `/{student_id}/warnings` | SA, IA, MA | `create_warning` | Manually issue a warning |
| POST | `/{student_id}/penalties` | SA, IA, MA | `create_penalty_direct` | Manually apply a penalty directly (no source warning) |
| PATCH | `/{student_id}` | SA, IA, MA | `update_student_profile` | Update student active status (`is_active` only — **[F4-fix]** hostel/room/name/email are on `StudentMappingModel`, use `PATCH /{student_id}/map` instead) |

---

## 4. Waste Entry Routes
**Router file:** `app/routers/waste.py`  **Prefix:** `/waste`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/entries` | SA, IA, MA, AV | `list_entries` | Filtered paginated waste entries |
| GET | `/entries/{entry_id}` | SA, IA, MA, AV | `get_entry` | Single waste entry detail |
| GET | `/current-session` | SA, IA, MA, AV, SO | `get_current_session` | Active meal session summary |
| GET | `/recent` | SA, IA, MA, AV, SO | `get_recent_entries` | Latest N entries for live feed |

---

## 5. ML Ingestion Routes
**Router file:** `app/routers/ml.py`  **Prefix:** `/ml`  *(API Key auth only)*

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| POST | `/detect` | API_KEY | `ingest_detection` | Single plate detection event |
| POST | `/sync` | API_KEY | `bulk_ingest` | Bulk offline sync of entries |
| POST | `/heartbeat` | API_KEY | `ml_heartbeat` | ML pipeline health + metrics push |
| POST | `/upload-image` | API_KEY | `upload_image` | Upload plate image (multipart/form-data), returns filename for use in `/detect` |

---

## 6. Warning & Penalty Routes
**Router file:** `app/routers/warnings.py`  **Prefix:** `/warnings`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA | `list_warnings` | Filtered paginated warnings list — query params: `status`, `level` (`level_1`/`level_2`/`level_3`), `student_id`, `date_from`, `date_to`, `page`, `size` |
| GET | `/stats` | SA, IA, MA | `get_warning_stats` | Summary counts for cards |
| GET | `/export` | SA, IA, MA | `export_warnings` | Download warnings as CSV/Excel — **query params:** `format=csv\|excel` (required), plus same filter params as `list_warnings` (`status`, `student_id`, `date_from`, `date_to`). Do NOT use request body on this GET endpoint. |
| PATCH | `/{warning_id}/resolve` | SA, IA, MA | `resolve_warning` | Resolve a warning |
| POST | `/{warning_id}/escalate` | SA, IA, MA | `escalate_warning` | Escalate warning |
| POST | `/{warning_id}/apply-penalty` | SA, IA | `apply_penalty` | Convert warning to penalty |
| PATCH | `/bulk/resolve` | SA, IA, MA | `bulk_resolve` | Bulk resolve selected warnings |

**Prefix:** `/penalties`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA | `list_penalties` | Filtered penalties list |
| PATCH | `/{penalty_id}/revoke` | SA, IA | `revoke_penalty` | Revoke a penalty |

**Prefix:** `/escalations`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA | `list_escalations` | Pending escalation queue |
| POST | `/{escalation_id}/review` | SA, IA | `review_escalation` | Approve or reject escalation |

---

## 7. Rule Engine Routes
**Router file:** `app/routers/rules.py`  **Prefix:** `/rules`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA | `list_rules` | Filtered paginated rules |
| POST | `/` | SA, IA | `create_rule` | Create new rule |
| GET | `/metadata/fields` | SA, IA | `get_available_fields` | Field options for rule builder |
| GET | `/metadata/operators` | SA, IA | `get_available_operators` | Operator options |
| GET | `/metadata/actions` | SA, IA | `get_available_actions` | Action type options |
| GET | `/chains` | SA, IA | `get_rule_chains` | Rule chain graph data |
| GET | `/{rule_id}` | SA, IA | `get_rule` | Single rule detail |
| PATCH | `/{rule_id}` | SA, IA | `update_rule` | Update rule |
| DELETE | `/{rule_id}` | SA, IA | `delete_rule` | Soft delete rule |
| POST | `/{rule_id}/toggle` | SA, IA | `toggle_rule` | Enable/disable rule |
| POST | `/{rule_id}/duplicate` | SA, IA | `duplicate_rule` | Clone rule |
| POST | `/{rule_id}/test` | SA, IA | `test_rule` | Test rule against sample data |
| POST | `/{rule_id}/simulate` | SA, IA | `simulate_rule` | Simulate against historical data |
| GET | `/{rule_id}/executions` | SA, IA | `get_rule_executions` | Rule execution history |

---

## 8. Analytics Routes
**Router file:** `app/routers/analytics.py`  **Prefix:** `/analytics`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/overview` | SA, IA, MA, AV | `get_overview` | Global KPI cards (query: `period`) |
| GET | `/trends` | SA, IA, MA, AV | `get_trends` | Trend data (query: `type`, `period`) |
| GET | `/peaks` | SA, IA, MA, AV | `get_peak_waste` | Peak waste hours/meals/weekdays |
| GET | `/meal-distribution` | SA, IA, MA, AV | `get_meal_distribution` | Waste by meal type |
| GET | `/food-waste-distribution` | SA, IA, MA, AV | `get_food_waste_distribution` | Top wasted food items |
| GET | `/top-waste-contributors` | SA, IA, MA, AV | `get_top_contributors` | Student waste ranking |
| GET | `/improvement-tracking` | SA, IA, MA, AV | `get_improvement_tracking` | Improvement vs previous period |
| GET | `/sustainability` | SA, IA, MA, AV | `get_sustainability_scores` | Score distribution |

---

## 9. Monitoring Routes
**Router file:** `app/routers/monitoring.py`  **Prefix:** `/monitoring`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/current-session` | SA, IA, MA, AV, SO | `get_current_session` | Active meal session |
| GET | `/recent-entries` | SA, IA, MA, AV, SO | `get_recent_entries` | Live feed initial load |
| GET | `/device-statuses` | SA, IA, MA, AV, SO | `get_device_statuses` | All device health status |
| POST | `/alerts/{notif_id}/acknowledge` | SA, IA, MA, SO | `acknowledge_alert` | Mark alert as read |

---

## 10. Notification Routes
**Router file:** `app/routers/notifications.py`  **Prefix:** `/notifications`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA | `list_notifications` | Paginated notifications (query: `tab`, `type`) |
| GET | `/stats` | SA, IA, MA | `get_notification_stats` | Unread/sent/failed counts |
| POST | `/` | SA, IA, MA | `send_notification` | Send custom notification |
| POST | `/broadcast` | SA, IA | `send_broadcast` | Broadcast to group |
| POST | `/schedule` | SA, IA, MA | `schedule_notification` | Schedule future notification |
| GET | `/{notif_id}` | SA, IA, MA | `get_notification` | Detail + delivery status |
| PATCH | `/{notif_id}/read` | SA, IA, MA | `mark_read` | Mark as read |
| POST | `/mark-all-read` | SA, IA, MA | `mark_all_read` | Mark all as read |
| DELETE | `/{notif_id}` | SA, IA, MA | `delete_notification` | Delete notification |
| POST | `/{notif_id}/retry` | SA, IA, MA | `retry_failed` | Retry failed delivery |
| GET | `/{notif_id}/delivery` | SA, IA, MA | `get_delivery_status` | **[M5-audit-fix]** Per-recipient delivery tracking info (timestamps, errors, channel status). Required by frontend spec `09-notifications.md`. |

---

## 11. Report Routes
**Router file:** `app/routers/reports.py`  **Prefix:** `/reports`

> **Route Registration Order:** Register `/schedules` and `/generate` (static paths) **before** `/{report_id}/download` and `/{report_id}` (parameterized paths) in `app/routers/reports.py`. FastAPI resolves static segments first when they are registered first; failing to do so could cause `/schedules` to be misinterpreted as a `report_id`.

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA, AV | `list_reports` | Generated reports list |
| POST | `/generate` | SA, IA, MA | `generate_report` | Generate report (queued) |
| GET | `/schedules` | SA, IA, MA | `list_schedules` | Scheduled report jobs |
| POST | `/schedules` | SA, IA, MA | `create_schedule` | Create report schedule |
| PATCH | `/schedules/{schedule_id}` | SA, IA, MA | `update_schedule` | Edit schedule |
| DELETE | `/schedules/{schedule_id}` | SA, IA, MA | `delete_schedule` | Remove schedule |
| GET | `/{report_id}/download` | SA, IA, MA, AV | `download_report` | Download file |
| DELETE | `/{report_id}` | SA, IA, MA | `delete_report` | Delete report |

---

## 12. Configuration Routes
**Router file:** `app/routers/config.py`  **Prefix:** `/config`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/institution` | SA, IA, MA | `get_config` | Institution config section |
| PATCH | `/institution` | SA, IA | `update_config` | Update institution config |
| GET | `/device` | SA, IA, MA | `get_config` | Device identity config |
| PATCH | `/device` | SA, IA | `update_config` | Update device config |
| GET | `/thresholds` | SA, IA, MA | `get_thresholds` | Threshold values |
| PATCH | `/thresholds` | SA, IA | `update_thresholds` | Update thresholds |
| GET | `/meals` | SA, IA, MA | `get_meal_timings` | Meal session timings |
| PUT | `/meals` | SA, IA | `update_meal_timings` | Replace meal timings |
| GET | `/branches` | SA, IA, MA | `get_branches` | Branch list |
| PUT | `/branches` | SA, IA | `update_branches` | Replace branches |
| GET | `/system` | SA, IA | `get_system_policies` | System policies |
| PATCH | `/system` | SA | `update_system_policies` | Update system policies |
| POST | `/reset/{section}` | SA | `reset_defaults` | Reset section to defaults |

---

## 13. Template Routes
**Router file:** `app/routers/templates.py`  **Prefix:** `/templates`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA, MA | `list_templates` | All email templates |
| POST | `/` | SA, IA | `create_template` | Create new template |
| GET | `/{template_id}` | SA, IA, MA | `get_template` | Template detail |
| PATCH | `/{template_id}` | SA, IA | `update_template` | Update template |
| DELETE | `/{template_id}` | SA, IA | `delete_template` | Delete (non-default only) |
| POST | `/{template_id}/preview` | SA, IA, MA | `preview_template` | Rendered preview |

---

## 14. Settings Routes
**Router file:** `app/routers/settings.py`  **Prefix:** `/settings`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/users` | SA, IA | `list_users` | Admin/staff user list |
| POST | `/users` | SA | `create_user` | Create new user |
| PATCH | `/users/{user_id}` | SA, IA | `update_user` | Update user info/role |
| POST | `/users/{user_id}/deactivate` | SA | `deactivate_user` | Disable user account |
| POST | `/users/{user_id}/reset-password` | SA | `reset_user_password` | Force password reset |
| GET | `/security` | SA | `get_security_config` | JWT/password/lockout config |
| PATCH | `/security` | SA | `update_security_config` | Update security config |
| GET | `/backups` | SA, IA | `list_backups` | Backup list |
| POST | `/backups` | SA, IA | `trigger_backup` | Manual backup |
| GET | `/backups/{backup_id}/download` | SA, IA | `download_backup` | Download backup ZIP |
| POST | `/backups/restore` | SA | `restore_backup` | Restore from backup |
| GET | `/appearance` | SA, IA | `get_appearance` | Appearance config |
| PATCH | `/appearance` | SA, IA | `update_appearance` | Update appearance |
| POST | `/appearance/logo` | SA, IA | `upload_logo` | Upload institution logo |
| POST | `/maintenance/clear-cache` | SA | `clear_cache` | Flush Redis cache |
| POST | `/maintenance/optimize-db` | SA | `optimize_db` | SQLite VACUUM |
| GET | `/maintenance/system-info` | SA, IA | `get_system_info` | System metrics |
| GET | `/maintenance/export-all` | SA | `export_all_data` | Full data export ZIP |

---

## 15. Audit Routes
**Router file:** `app/routers/audit.py`  **Prefix:** `/audit`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA | `list_events` | Filtered paginated audit log — **[M6-audit-fix]** query params include: `user_id`, `event_type` (e.g., `config.updated`, `rule.created`), `resource_type` (e.g., `config`, `rules`, `students`), `date_from`, `date_to`, `q` (full-text search), `sort`, `page`, `size` |
| GET | `/stats` | SA, IA | `get_stats` | Stats bar counts |
| GET | `/timeline` | SA, IA | `get_timeline` | Timeline grouped by user |
| GET | `/export` | SA, IA | `export_log` | CSV export |
| GET | `/{event_id}` | SA, IA | `get_event` | Full event detail |

---

## 16. Roles Routes
**Router file:** `app/routers/roles.py`  **Prefix:** `/roles`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/` | SA, IA | `list_roles` | All role definitions |
| PATCH | `/{role_id}` | SA | `update_role` | Update role permissions |

---

## 17. Filter Preset Routes
**Router file:** `app/routers/filter_presets.py`  **Prefix:** `/filters`

| Method | Path | Roles | Controller Function | Description |
|--------|------|-------|---------------------|-------------|
| GET | `/presets` | SA, IA, MA, AV | `list_presets` | Current user's saved presets |
| POST | `/presets` | SA, IA, MA, AV | `save_preset` | Save filter preset |
| GET | `/presets/{preset_id}` | SA, IA, MA, AV | `get_preset` | Load preset |
| PATCH | `/presets/{preset_id}` | SA, IA, MA, AV | `update_preset` | Update preset name or filter_state |
| DELETE | `/presets/{preset_id}` | SA, IA, MA, AV | `delete_preset` | Delete preset |

---

## 18. WebSocket Routes
**Router file:** `app/routers/ws.py`  **Prefix:** `/ws`

| Protocol | Path | Roles | Controller Function | Events Pushed |
|----------|------|-------|---------------------|---------------|
| WS | `/dashboard` | SA, IA, MA, AV | `ws_dashboard` | `kpi_update`, `rule_executed`, `warning_issued`, `alert` |
| WS | `/monitoring` | SA, IA, MA, AV, SO | `ws_monitoring` | `waste_entry`, `alert`, `device_status`, `session_update` |

---

## Query Parameter Conventions

| Parameter | Type | Used In | Description |
|-----------|------|---------|-------------|
| `page` | int (default 1) | All list endpoints | Page number |
| `size` | int (default 25, max 100) | All list endpoints | Items per page |
| `sort` | string | List endpoints | Column name to sort by |
| `order` | `asc`/`desc` | List endpoints | Sort direction |
| `period` | `today`/`yesterday`/`7d`/`30d`/`semester`/`all` | Analytics | Time filter |
| `date_from` | ISO date | Analytics, Audit | Start date |
| `date_to` | ISO date | Analytics, Audit | End date |
| `status` | string | Students, Warnings | Status filter |
| `format` | `csv`/`excel`/`pdf` | Export endpoints | Export format |
| `q` | string | Audit | Full-text search |
