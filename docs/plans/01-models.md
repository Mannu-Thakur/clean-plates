# CleanPlates — Database Models

**Stack:** SQLAlchemy 2.0 (async) + SQLite (edge) | All UUIDs use `uuid4`. All timestamps are UTC. Soft-deletes via `is_deleted: bool`.

---

## 1. UserModel
**Table:** `users`  
**Purpose:** Admin/staff accounts for dashboard access.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `email` | String(255) | UNIQUE, NOT NULL | Login identifier |
| `password_hash` | String(255) | NOT NULL | bcrypt hashed |
| `name` | String(100) | NOT NULL | Display name |
| `role` | String(50) | NOT NULL | `super_admin`, `institution_admin`, `mess_admin`, `analytics_viewer`, `staff_operator` |
| `is_active` | Boolean | DEFAULT true | Deactivated users cannot login |
| `failed_login_attempts` | Integer | DEFAULT 0 | Lockout counter |
| `locked_until` | DateTime | NULLABLE | Lockout expiry |
| `last_login` | DateTime | NULLABLE | |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `email`

---

## 2. RefreshTokenModel
**Table:** `refresh_tokens`  
**Purpose:** Track issued refresh tokens for revocation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `token_hash` | String(255) | UNIQUE, NOT NULL | SHA256 of token |
| `expires_at` | DateTime | NOT NULL | |
| `revoked` | Boolean | DEFAULT false | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `token_hash`, `user_id`

---

## 3. DeviceModel
**Table:** `devices`  
**Purpose:** Raspberry Pi device identity & operational state.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `device_serial` | String(100) | UNIQUE, NOT NULL | Pi serial number |
| `edge_node_name` | String(100) | NOT NULL | Human-readable name |
| `institution_name` | String(200) | NOT NULL | |
| `institution_code` | String(50) | NOT NULL | |
| `campus_name` | String(100) | NOT NULL | |
| `mess_name` | String(100) | NOT NULL | |
| `mess_id` | String(50) | NOT NULL | |
| `hostel_name` | String(100) | NULLABLE | |
| `hostel_block` | String(50) | NULLABLE | |
| `floor_number` | Integer | NULLABLE | |
| `wing_section` | String(50) | NULLABLE | |
| `capacity` | Integer | NULLABLE | Max students |
| `meal_capacity_per_day` | Integer | NULLABLE | |
| `status` | String(20) | DEFAULT `online` | `online`, `offline`, `warning`, `decommissioned` |
| `ip_address` | String(45) | NULLABLE | |
| `mac_address` | String(17) | NULLABLE | |
| `firmware_version` | String(50) | NULLABLE | |
| `os_version` | String(100) | NULLABLE | |
| `last_heartbeat` | DateTime | NULLABLE | |
| `last_sync` | DateTime | NULLABLE | |
| `active_since` | DateTime | NULLABLE | |
| `managed_by` | String(100) | NULLABLE | Admin name |
| `admin_contact` | String(200) | NULLABLE | |
| `api_key_hash` | String(255) | NULLABLE | For ML pipeline auth |
| `is_deleted` | Boolean | DEFAULT false | Soft delete |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `device_serial`, `status`

---

## 4. DeviceHealthModel
**Table:** `device_health`  
**Purpose:** Time-series health snapshots from heartbeats.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `device_id` | UUID | FK → devices.id, NOT NULL | |
| `cpu_percent` | Float | NOT NULL | |
| `ram_percent` | Float | NOT NULL | |
| `temperature` | Float | NULLABLE | Celsius |
| `storage_percent` | Float | NULLABLE | |
| `connectivity` | Boolean | DEFAULT true | Internet reachable |
| `recorded_at` | DateTime | NOT NULL | |

**Indexes:** `device_id`, `recorded_at`

---

## 5. StudentModel
**Table:** `students`  
**Purpose:** System-generated student identity via device/card ID. Status derived from waste data.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `device_id` | String(100) | UNIQUE, NOT NULL | System-assigned card/tag ID |
| `status` | String(20) | DEFAULT `green` | `green`, `yellow`, `orange`, `red` |
| `sustainability_score` | Float | DEFAULT 100.0 | 0–100 |
| `warning_count` | Integer | DEFAULT 0 | Active warnings |
| `penalty_count` | Integer | DEFAULT 0 | Total penalties |
| `total_waste_grams` | Float | DEFAULT 0.0 | Cumulative |
| `avg_waste_grams` | Float | DEFAULT 0.0 | Rolling average per meal |
| `is_active` | Boolean | DEFAULT true | |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `device_id`, `status`

> **⚠ Naming Collision Warning (N3):** `StudentModel.device_id` (String) is the **edge card/tag ID** assigned by the Raspberry Pi — it is NOT a FK and NOT a UUID. `WasteEntryModel.device_id` (UUID, FK → devices.id) is the **Raspberry Pi device UUID**. Both columns are named `device_id` but hold completely different data types and semantics. When writing joins, never equate these two fields. The correct join between students and waste entries is: `students.id = waste_entries.student_id`. The `student_device_id` alias is used in `WasteEntryCreateSchema` (schemas §4) to avoid confusion at the API layer.

---

## 6. StudentMappingModel
**Table:** `student_mappings`  
**Purpose:** Admin-assigned identity for a student device ID.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → students.id, UNIQUE, NOT NULL | One mapping per student |
| `device_id` | String(100) | NOT NULL | Denormalized for fast lookup |
| `name` | String(150) | NOT NULL | Full name |
| `roll_number` | String(50) | NOT NULL | Institutional roll |
| `branch` | String(50) | NOT NULL | CSE, ECE, ME, CE etc. |
| `year` | Integer | NOT NULL | 1–4 |
| `hostel` | String(100) | NULLABLE | |
| `room_number` | String(20) | NULLABLE | |
| `email` | String(255) | NULLABLE | For notifications |
| `mapped_by` | UUID | FK → users.id, NOT NULL | |
| `mapped_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `student_id`, `roll_number`, `branch`, `year`

---

## 7. FoodItemModel
**Table:** `food_items`  
**Purpose:** Food catalog for waste entry tagging.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | String(100) | NOT NULL | rice, dal, sabzi, roti |
| `category` | String(50) | NOT NULL | `main`, `side`, `dessert`, `beverage` |
| `is_active` | Boolean | DEFAULT true | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `name`, `category`

---

## 8. WasteEntryModel
**Table:** `waste_entries`  
**Purpose:** Core data record — one per plate detection event.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → students.id, NOT NULL | |
| `device_id` | UUID | FK → devices.id, NOT NULL | Which Pi captured |
| `weight_grams` | Float | NOT NULL | Measured waste weight |
| `meal_type` | String(20) | NOT NULL | breakfast/lunch/dinner |
| `food_items` | JSON | NULLABLE | `[{"name":"rice","grams":80}]` |
| `confidence_score` | Float | NULLABLE | ML confidence 0–1 |
| `plate_image_path` | String(500) | NULLABLE | Stored image path |
| `session_date` | Date | NOT NULL | Date of meal (for grouping) |
| `timestamp` | DateTime | NOT NULL | Actual detection time |
| `severity` | String(20) | NOT NULL | `normal`, `warning`, `high` |
| `rule_evaluated` | Boolean | DEFAULT false | Has rule engine processed this |
| `source` | String(20) | DEFAULT `ml` | `ml`, `manual`, `sync` |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `student_id`, `device_id`, `timestamp`, `session_date`, `meal_type`, `severity`

---

## 9. WarningModel
**Table:** `warnings`  
**Purpose:** Individual warning records per student.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → students.id, NOT NULL | |
| `level` | String(20) | NOT NULL | `level_1`, `level_2`, `level_3` |
| `reason` | String(500) | NOT NULL | Human-readable reason |
| `rule_id` | UUID | NULLABLE | FK → rules.id |
| `waste_entry_id` | UUID | FK → waste_entries.id, NULLABLE | Triggering entry |
| `issued_by` | UUID | FK → users.id, NULLABLE | Null if auto-generated |
| `status` | String(20) | DEFAULT `active` | `active`, `resolved`, `escalated`, `converted_to_penalty` |
| `resolved_by` | UUID | FK → users.id, NULLABLE | |
| `resolved_at` | DateTime | NULLABLE | |
| `resolution_note` | String(500) | NULLABLE | |
| `email_sent` | Boolean | DEFAULT false | |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `student_id`, `status`, `created_at`

> **Constraint (G2):** `rule_id` FK references `rules.id`. Physical deletion of `RuleModel` rows is **prohibited** — use soft-delete only (`is_deleted=true`). Hard-deleting a rule while warnings reference it would orphan `WarningModel.rule_id`. Enforce this in `rule_service.delete_rule()` (soft delete only) and document in any DB maintenance scripts.

---

## 10. EscalationModel
**Table:** `escalations`  
**Purpose:** Warnings escalated for review.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `warning_id` | UUID | FK → warnings.id, NOT NULL | |
| `student_id` | UUID | FK → students.id, NOT NULL | Denormalized |
| `reason` | String(500) | NOT NULL | |
| `escalated_to_role` | String(50) | NOT NULL | Target role |
| `escalated_by` | UUID | FK → users.id, NOT NULL | |
| `status` | String(20) | DEFAULT `pending` | `pending`, `approved`, `rejected` |
| `reviewed_by` | UUID | FK → users.id, NULLABLE | |
| `review_note` | String(500) | NULLABLE | |
| `reviewed_at` | DateTime | NULLABLE | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `warning_id`, `status`

---

## 11. PenaltyModel
**Table:** `penalties`  
**Purpose:** Formal penalty records per student.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `student_id` | UUID | FK → students.id, NOT NULL | |
| `points` | Integer | NOT NULL | Penalty severity |
| `reason` | String(500) | NOT NULL | |
| `warning_id` | UUID | FK → warnings.id, NULLABLE | Source warning |
| `rule_id` | UUID | NULLABLE | FK → rules.id |
| `issued_by` | UUID | FK → users.id, NULLABLE | |
| `status` | String(20) | DEFAULT `active` | `active`, `revoked` |
| `revoked_by` | UUID | FK → users.id, NULLABLE | |
| `revoke_reason` | String(500) | NULLABLE | |
| `revoked_at` | DateTime | NULLABLE | |
| `email_sent` | Boolean | DEFAULT false | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `student_id`, `status`

---

## 12. RuleModel
**Table:** `rules`  
**Purpose:** Dynamic configurable rules for the rule engine.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | String(200) | NOT NULL | |
| `description` | String(1000) | NULLABLE | |
| `type` | String(30) | NOT NULL | `threshold`, `frequency`, `trend`, `composite`, `device` |
| `priority` | String(20) | NOT NULL | `critical`, `high`, `medium`, `low` |
| `active` | Boolean | DEFAULT true | |
| `conditions` | JSON | NOT NULL | Array of condition groups |
| `time_constraints` | JSON | NULLABLE | `{"window":"per_meal","period":"daily"}` |
| `scope` | JSON | NULLABLE | `{"target":"student","filters":{}}` |
| `actions` | JSON | NOT NULL | Array of action objects |
| `chain_to_rule_id` | UUID | FK → rules.id, NULLABLE | Next rule in chain |
| `execution_count` | Integer | DEFAULT 0 | Stats |
| `last_triggered_at` | DateTime | NULLABLE | |
| `created_by` | UUID | FK → users.id, NOT NULL | |
| `is_deleted` | Boolean | DEFAULT false | Soft delete |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `active`, `type`, `priority`

---

## 13. RuleExecutionModel
**Table:** `rule_executions`  
**Purpose:** Audit log of every rule evaluation that fired.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `rule_id` | UUID | FK → rules.id, NOT NULL | |
| `trigger_event_type` | String(50) | NOT NULL | `waste_entry_created`, etc. |
| `trigger_entity_id` | UUID | NULLABLE | e.g. waste_entry.id |
| `student_id` | UUID | FK → students.id, NULLABLE | |
| `matched_conditions` | JSON | NOT NULL | Which conditions matched |
| `executed_actions` | JSON | NOT NULL | Which actions ran |
| `result_status` | String(20) | NOT NULL | `success`, `partial`, `failed` |
| `error_message` | String(500) | NULLABLE | |
| `executed_at` | DateTime | NOT NULL | |

**Indexes:** `rule_id`, `student_id`, `executed_at`

---

## 14. NotificationModel
**Table:** `notifications`  
**Purpose:** All notifications sent or queued by the system.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `type` | String(30) | NOT NULL | `warning`, `penalty`, `alert`, `system`, `custom`, `appreciation` |
| `channel` | String(20) | NOT NULL | `email`, `dashboard`, `both` |
| `subject` | String(300) | NOT NULL | |
| `body` | Text | NOT NULL | |
| `sender_id` | UUID | FK → users.id, NULLABLE | Null = system |
| `recipient_type` | String(20) | NOT NULL | `individual`, `branch`, `hostel`, `year`, `all` |
| `recipient_ids` | JSON | NOT NULL | Array of student IDs or group identifiers |
| `template_id` | UUID | FK → email_templates.id, NULLABLE | |
| `status` | String(20) | DEFAULT `pending` | `pending`, `sent`, `failed`, `partial` |
| `retry_count` | Integer | DEFAULT 0 | |
| `is_read` | Boolean | DEFAULT false | For dashboard channel |
| `scheduled_at` | DateTime | NULLABLE | If scheduled |
| `sent_at` | DateTime | NULLABLE | |
| `related_entity_type` | String(50) | NULLABLE | `warning`, `penalty`, `rule_execution` |
| `related_entity_id` | UUID | NULLABLE | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `type`, `status`, `recipient_type`, `created_at`

---

## 15. EmailTemplateModel
**Table:** `email_templates`  
**Purpose:** Configurable email templates with Jinja2 variables.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | String(100) | NOT NULL | |
| `type` | String(30) | NOT NULL | `warning`, `penalty`, `appreciation`, `awareness`, `custom`, `device_offline` |
| `subject` | String(300) | NOT NULL | May contain `{{variables}}` |
| `body_html` | Text | NOT NULL | Jinja2 HTML template |
| `variables` | JSON | NOT NULL | `["student_name","waste_grams"]` — declared vars |
| `is_default` | Boolean | DEFAULT false | System templates cannot be deleted |
| `created_by` | UUID | FK → users.id, NOT NULL | |
| `is_deleted` | Boolean | DEFAULT false | |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

**Indexes:** `type`, `is_default`

> **Constraint (G2 — same applies here):** `rule_id` in `PenaltyModel` also FK references `rules.id` (nullable). Same prohibition on hard-deleting rules applies.

---

## 16. ReportModel
**Table:** `reports`  
**Purpose:** Generated report files metadata.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `type` | String(30) | NOT NULL | `daily`, `weekly`, `monthly`, `branch_comparison`, `student_history`, `food_optimization`, `custom` |
| `format` | String(10) | NOT NULL | `pdf`, `csv`, `excel` |
| `file_path` | String(500) | NOT NULL | Local storage path |
| `file_size` | BigInteger | NULLABLE | Bytes |
| `config` | JSON | NULLABLE | Filters and metrics used |
| `generated_by` | UUID | FK → users.id, NOT NULL | |
| `status` | String(20) | DEFAULT `pending` | `pending`, `generating`, `ready`, `failed` |
| `error_message` | String(500) | NULLABLE | |
| `generated_at` | DateTime | NULLABLE | |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `type`, `status`, `created_at`

---

## 17. ReportScheduleModel
**Table:** `report_schedules`  
**Purpose:** Auto-scheduled report jobs.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `report_type` | String(30) | NOT NULL | |
| `format` | String(10) | NOT NULL | |
| `frequency` | String(20) | NOT NULL | `daily`, `weekly`, `monthly` |
| `day_of_week` | String(10) | NULLABLE | `monday`–`sunday` for weekly |
| `time_of_day` | String(5) | NOT NULL | `08:00` |
| `email_recipients` | JSON | NULLABLE | `["admin@college.edu"]` |
| `auto_email` | Boolean | DEFAULT false | |
| `active` | Boolean | DEFAULT true | |
| `created_by` | UUID | FK → users.id, NOT NULL | |
| `last_run` | DateTime | NULLABLE | |
| `next_run` | DateTime | NULLABLE | |
| `created_at` | DateTime | NOT NULL | |

---

## 18. FilterPresetModel
**Table:** `filter_presets`  
**Purpose:** Saved analytics filter combinations per user.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `name` | String(100) | NOT NULL | |
| `filter_state` | JSON | NOT NULL | Complete filter object |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `user_id`

---

## 19. ConfigModel
**Table:** `system_config`  
**Purpose:** Key-value store for all system configuration sections.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `section` | String(50) | NOT NULL | `institution`, `thresholds`, `meals`, `branches`, `system`, `appearance` |
| `key` | String(100) | NOT NULL | Config key |
| `value` | JSON | NOT NULL | Config value (any type) |
| `updated_by` | UUID | FK → users.id, NULLABLE | |
| `updated_at` | DateTime | NOT NULL | |

**Unique:** `(section, key)`  
**Indexes:** `section`

> **Note:** Meal timings, branches, and thresholds stored as structured JSON values within this table. No separate tables needed — reduces migrations for config changes.

---

## 20. AuditEventModel
**Table:** `audit_events`  
**Purpose:** Immutable audit trail of all system actions.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `event_type` | String(50) | NOT NULL | `auth.login`, `config.updated`, `rule.created`, `warning.issued`, etc. |
| `action` | String(50) | NOT NULL | `create`, `update`, `delete`, `login`, `logout`, `execute` |
| `resource_type` | String(50) | NOT NULL | `user`, `rule`, `config`, `student`, `warning`, `device` |
| `resource_id` | String(100) | NULLABLE | ID of affected resource |
| `user_id` | UUID | FK → users.id, NULLABLE | Null for system-generated |
| `user_name` | String(100) | NULLABLE | Denormalized |
| `user_role` | String(50) | NULLABLE | Denormalized |
| `ip_address` | String(45) | NULLABLE | |
| `user_agent` | String(500) | NULLABLE | |
| `summary` | String(500) | NOT NULL | Human-readable description |
| `before_state` | JSON | NULLABLE | State before change |
| `after_state` | JSON | NULLABLE | State after change |
| `metadata` | JSON | NULLABLE | Extra context |
| `created_at` | DateTime | NOT NULL | |

**Indexes:** `event_type`, `resource_type`, `user_id`, `created_at`

---

## 21. BackupModel
**Table:** `backups`  
**Purpose:** Database backup file records.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `filename` | String(300) | NOT NULL | |
| `file_path` | String(500) | NOT NULL | |
| `file_size` | BigInteger | NULLABLE | |
| `backup_type` | String(20) | DEFAULT `manual` | `manual`, `scheduled`, `pre_restore` |
| `status` | String(20) | DEFAULT `creating` | `creating`, `available`, `deleted` |
| `triggered_by` | UUID | FK → users.id, NULLABLE | Null = auto |
| `created_at` | DateTime | NOT NULL | |

---

## 22. AggregatedWasteModel
**Table:** `aggregated_waste`  
**Purpose:** Pre-computed aggregates for fast analytics queries.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `period_type` | String(20) | NOT NULL | `hourly`, `daily`, `weekly`, `monthly` |
| `period_start` | DateTime | NOT NULL | |
| `period_end` | DateTime | NOT NULL | |
| `scope_type` | String(20) | NOT NULL | `global`, `device`, `student`, `branch`, `hostel`, `meal`, `food_item` |
| `scope_id` | String(100) | NULLABLE | Scope entity identifier |
| `total_waste_grams` | Float | NOT NULL | |
| `avg_waste_grams` | Float | NOT NULL | |
| `entry_count` | Integer | NOT NULL | |
| `student_count` | Integer | NULLABLE | |
| `peak_hour` | Integer | NULLABLE | 0–23 |
| `computed_at` | DateTime | NOT NULL | |

**Unique:** `(period_type, period_start, scope_type, scope_id)`  
**Indexes:** `period_type`, `period_start`, `scope_type`, `scope_id`

---

## 23. RoleModel  
**Table:** `roles`  
**Purpose:** Role definitions with permission sets.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `name` | String(50) | UNIQUE, NOT NULL | `super_admin`, etc. |
| `description` | String(300) | NULLABLE | |
| `permissions` | JSON | NOT NULL | `{"students":["read","write"],"rules":["read"]}` |
| `is_system` | Boolean | DEFAULT false | System roles cannot be deleted |
| `created_at` | DateTime | NOT NULL | |
| `updated_at` | DateTime | NOT NULL | |

### Default Role Permissions Matrix (I3)

Seed via `scripts/seed_roles.py`. Use this as the source of truth:

| Resource | `super_admin` | `institution_admin` | `mess_admin` | `analytics_viewer` | `staff_operator` |
|----------|--------------|--------------------|--------------|--------------------|------------------|
| `students` | read, write | read, write | read, write | read | read |
| `waste` | read, write | read, write | read, write | read | read, write |
| `warnings` | read, write | read, write | read, write | — | read |
| `penalties` | read, write | read, write | read | — | — |
| `escalations` | read, write | read, write | read | — | — |
| `rules` | read, write | read, write | — | — | — |
| `analytics` | read | read | read | read | — |
| `devices` | read, write | read, write | read | — | read |
| `config` | read, write | read, write | read | — | — |
| `notifications` | read, write | read, write | read, write | — | — |
| `reports` | read, write | read, write | read, write | read | — |
| `audit` | read | read | — | — | — |
| `settings` | read, write | read | — | — | — |
| `roles` | read, write | read | — | — | — |

---

## Model Relationships Summary

```
users ─────────────────────────────────────────────────────────────────────────
  │ (issued_by)        warnings, penalties, rules, notifications, audit_events
  │ (mapped_by)        student_mappings
  │ (created_by)       reports, report_schedules, email_templates, filter_presets
  └── refresh_tokens

devices ────────────────────────────────────────────────────────────────────────
  └── device_health
  └── waste_entries (device_id)

students ───────────────────────────────────────────────────────────────────────
  └── student_mappings (1:1)
  └── waste_entries (1:N)
  └── warnings (1:N)
  └── penalties (1:N)
  └── rule_executions (1:N)

waste_entries ──────────────────────────────────────────────────────────────────
  ├── student_id → students
  ├── device_id → devices

warnings ───────────────────────────────────────────────────────────────────────
  ├── student_id → students
  ├── rule_id → rules (nullable)
  ├── waste_entry_id → waste_entries (nullable)
  └── escalations (1:1)
      └── → penalty (via apply-penalty flow)

rules ──────────────────────────────────────────────────────────────────────────
  └── rule_executions (1:N)
  └── chain_to_rule_id → rules (self-referential)

notifications ──────────────────────────────────────────────────────────────────
  └── template_id → email_templates (nullable)

system_config ──────────────────────────────────────────────────────────────────
  (flat key-value; no foreign relationships)
```
