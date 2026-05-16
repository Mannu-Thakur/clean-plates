# CleanPlates — Schemas (Pydantic Request/Response)

**Convention:** All schemas use Pydantic v2. `Base` = shared fields. `Create` = POST input. `Update` = PATCH input (all optional). `Schema` = response output.

> **GLOBAL RULE (M7):** Every response schema used as a route return type **must** include:
> ```python
> model_config = ConfigDict(from_attributes=True)
> ```
> Required for SQLAlchemy ORM → Pydantic v2 serialization (`model_validate(orm_obj)`). Without it, all ORM reads will raise `PydanticUserError`. Import via `from pydantic import ConfigDict`.

> **⚠ [F5-fix] IMPLEMENTATION NOTE:** The code blocks below show `model_config` explicitly only on `UserSchema` (§1) as a reference example. **ALL response schemas** (`DeviceSchema`, `StudentSchema`, `WasteEntrySchema`, `WarningSchema`, `EscalationSchema`, `PenaltySchema`, `RuleSchema`, `RuleExecutionSchema`, `NotificationSchema`, `ReportSchema`, `ReportScheduleSchema`, `AuditEventSchema`, `FilterPresetSchema`, `EmailTemplateSchema`, `BackupSchema`, `RoleSchema`, `DeviceStatusSchema`, `HealthDataSchema`, `StudentMappingSchema`, etc.) must include it in the actual implementation. See also `06-phase-wise-plan.md` Cross-Cutting Rule #16.

---

## 1. Auth Schemas
**File:** `app/schemas/auth.py`

```python
class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds

class RefreshTokenSchema(BaseModel):
    refresh_token: str

class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str        # min 8 chars validated

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # M5-fix: required for ORM → Pydantic v2 serialization
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    last_login: datetime | None

class LoginResponseSchema(BaseModel):
    tokens: TokenPairSchema
    user: UserSchema
```

---

## 2. Device Schemas
**File:** `app/schemas/devices.py`

```python
class DeviceCreateSchema(BaseModel):
    device_serial: str
    edge_node_name: str
    institution_name: str
    institution_code: str
    campus_name: str
    mess_name: str
    mess_id: str
    hostel_name: str | None = None
    hostel_block: str | None = None
    floor_number: int | None = None
    wing_section: str | None = None
    capacity: int | None = None
    meal_capacity_per_day: int | None = None
    managed_by: str | None = None
    admin_contact: str | None = None

class DeviceUpdateSchema(BaseModel):         # All optional
    edge_node_name: str | None = None
    mess_name: str | None = None
    hostel_name: str | None = None
    hostel_block: str | None = None
    floor_number: int | None = None
    capacity: int | None = None
    # L4-fix: `status` removed — device status is system-managed (heartbeat → online/offline;
    # use POST /devices/{id}/decommission for decommissioned status).
    # Allowing free-form PATCH of status causes data inconsistency.

class DeviceSchema(BaseModel):               # Response
    id: UUID
    device_serial: str
    edge_node_name: str
    institution_name: str
    mess_name: str
    hostel_name: str | None
    status: str
    ip_address: str | None
    firmware_version: str | None
    last_heartbeat: datetime | None
    last_sync: datetime | None
    active_since: datetime | None

class DeviceWithApiKeySchema(DeviceSchema):  # Only on create
    api_key: str                             # Raw key, shown once

class HeartbeatSchema(BaseModel):
    cpu_percent: float
    ram_percent: float
    temperature: float | None = None
    storage_percent: float | None = None
    connectivity: bool = True

class HealthDataSchema(BaseModel):
    device_id: UUID
    cpu_percent: float
    ram_percent: float
    temperature: float | None
    storage_percent: float | None
    connectivity: bool
    recorded_at: datetime

class HealthHistorySchema(BaseModel):
    device_id: UUID
    period: str
    data: list[HealthDataSchema]

class QueuedSyncSchema(BaseModel):           # H4-fix: return type for POST /devices/{id}/sync
    message: str                             # "Device queued for sync"
    pending_count: int                       # Offline entries awaiting upload
    device_id: UUID

class DeviceStatusSchema(BaseModel):
    id: UUID
    edge_node_name: str
    mess_name: str
    status: str
    cpu_percent: float | None
    ram_percent: float | None
    temperature: float | None
    last_heartbeat: datetime | None
```

---

## 3. Student Schemas
**File:** `app/schemas/students.py`

```python
class MappingCreateSchema(BaseModel):
    name: str
    roll_number: str
    branch: str
    year: int                    # 1–4
    hostel: str | None = None
    room_number: str | None = None
    email: EmailStr | None = None

class MappingUpdateSchema(BaseModel):        # All optional
    name: str | None = None
    roll_number: str | None = None
    branch: str | None = None
    year: int | None = None
    hostel: str | None = None
    room_number: str | None = None
    email: EmailStr | None = None

class StudentMappingSchema(BaseModel):
    student_id: UUID
    device_id: str
    name: str
    roll_number: str
    branch: str
    year: int
    hostel: str | None
    room_number: str | None
    email: str | None
    mapped_by: UUID
    mapped_at: datetime

class StudentSchema(BaseModel):
    id: UUID
    device_id: str
    status: str
    is_status_manual: bool           # [H4-audit-fix] True if status was set by rule engine classify_student or admin
    sustainability_score: float
    warning_count: int
    penalty_count: int
    avg_waste_grams: float
    is_active: bool
    mapping: StudentMappingSchema | None     # None if unmapped
    created_at: datetime

class StudentDetailSchema(StudentSchema):
    total_waste_grams: float

class StudentProfileUpdateSchema(BaseModel):  # M6-fix: for PATCH /students/{student_id}
    is_active: bool | None = None             # Only mutable StudentModel field
    # NOTE: hostel, room_number, name, email, etc. are on StudentMappingModel.
    #       Use PATCH /students/{student_id}/map (MappingUpdateSchema) for those.

class PaginatedStudents(PaginatedBase):
    items: list[StudentSchema]

class ImportResultSchema(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: list[dict]           # [{row, device_id, error}]

class WasteStatsSchema(BaseModel):
    student_id: UUID
    period: str
    total_waste_grams: float
    avg_waste_grams: float
    entry_count: int
    most_wasted_food: str | None
    peak_meal: str | None
    sustainability_score: float
    improvement_pct: float | None

class TimelinePointSchema(BaseModel):
    date: date
    total_grams: float
    entry_count: int

class TimelineSchema(BaseModel):
    student_id: UUID
    period: str
    threshold_grams: float
    data: list[TimelinePointSchema]

class FoodBreakdownItemSchema(BaseModel):
    food_name: str
    total_grams: float
    percentage: float

class FoodBreakdownSchema(BaseModel):
    student_id: UUID
    data: list[FoodBreakdownItemSchema]

class MealPatternItemSchema(BaseModel):
    meal_type: str
    avg_grams: float
    entry_count: int

class MealPatternSchema(BaseModel):
    student_id: UUID
    data: list[MealPatternItemSchema]

class ImprovementPointSchema(BaseModel):
    week_label: str
    avg_grams: float
    improvement_pct: float

class ImprovementSchema(BaseModel):
    student_id: UUID
    current_improvement_pct: float
    direction: str               # "improving", "stable", "worsening"
    data: list[ImprovementPointSchema]
```

---

## 4. Waste Entry Schemas
**File:** `app/schemas/waste.py`

```python
class FoodItemEntrySchema(BaseModel):
    name: str
    grams: float | None = None

class WasteEntryCreateSchema(BaseModel):     # From ML pipeline
    student_device_id: str
    device_serial: str
    weight_grams: float
    meal_type: str | None = None             # If provided, used as-is. If absent/None, resolved from timestamp and config time windows.
    food_items: list[FoodItemEntrySchema] = []
    confidence_score: float | None = None
    plate_image_path: str | None = None
    timestamp: datetime

class WasteEntrySchema(BaseModel):
    id: UUID
    student_id: UUID
    device_id: UUID
    weight_grams: float
    meal_type: str
    food_items: list[FoodItemEntrySchema]
    severity: str
    session_date: date
    timestamp: datetime
    student_name: str | None          # From mapping join
    student_device_id: str

class WasteEntryDetailSchema(WasteEntrySchema):
    confidence_score: float | None
    plate_image_path: str | None
    rule_evaluated: bool

class PaginatedEntries(PaginatedBase):
    items: list[WasteEntrySchema]

class SessionSummarySchema(BaseModel):
    session_name: str
    meal_type: str
    start_time: str
    end_time: str
    entry_count_today: int
    total_waste_today_grams: float
    is_active: bool

class SyncResultSchema(BaseModel):
    total_received: int
    inserted: int
    skipped: int
    errors: list[dict]

class BulkWasteIngestSchema(BaseModel):
    entries: list[WasteEntryCreateSchema]
```

---

## 5. Warning & Penalty Schemas
**File:** `app/schemas/warnings.py`

```python
class WarningCreateSchema(BaseModel):
    level: str               # level_1, level_2, level_3
    reason: str
    send_email: bool = False
    rule_id: UUID | None = None
    waste_entry_id: UUID | None = None

class WarningSchema(BaseModel):
    id: UUID
    student_id: UUID
    level: str
    reason: str
    status: str
    rule_id: UUID | None
    issued_by: UUID | None
    email_sent: bool
    created_at: datetime
    student_name: str | None

class WarningSummarySchema(BaseModel):
    total_warnings: int
    active_warnings: int
    pending_escalations: int
    total_penalties: int

class ResolveWarningSchema(BaseModel):
    resolution_note: str

class EscalateWarningSchema(BaseModel):
    escalated_to_role: str
    reason: str

class EscalationSchema(BaseModel):
    id: UUID
    warning_id: UUID
    student_id: UUID
    reason: str
    escalated_to_role: str
    escalated_by: UUID | None    # [F3-fix] NULLABLE — matches G6-fix in 01-models.md (None when auto-escalated by rule engine)
    status: str
    reviewed_by: UUID | None
    review_note: str | None
    reviewed_at: datetime | None
    created_at: datetime

class ReviewEscalationSchema(BaseModel):
    decision: str            # approved, rejected
    review_note: str | None = None

class PenaltyCreateSchema(BaseModel):
    points: int
    reason: str
    send_email: bool = False

class PenaltySchema(BaseModel):
    id: UUID
    student_id: UUID
    points: int
    reason: str
    status: str
    warning_id: UUID | None
    issued_by: UUID | None
    email_sent: bool
    created_at: datetime
    student_name: str | None

class RevokePenaltySchema(BaseModel):
    reason: str

class BulkResolveSchema(BaseModel):
    warning_ids: list[UUID]
    resolution_note: str

class StudentWarningsSchema(BaseModel):   # Used by GET /{student_id}/warnings
    warnings: list[WarningSchema]
    penalties: list[PenaltySchema]

class PaginatedWarnings(PaginatedBase):
    items: list[WarningSchema]

class PaginatedPenalties(PaginatedBase):
    items: list[PenaltySchema]
```

---

## 6. Rule Engine Schemas
**File:** `app/schemas/rules.py`

```python
class ConditionSchema(BaseModel):
    field: str               # waste_grams, meal_type, frequency_count, etc.
    operator: str            # gt, lt, eq, gte, lte, in, contains
    value: Any

class ConditionGroupSchema(BaseModel):
    logic: str = "AND"       # AND or OR
    conditions: list[ConditionSchema]

class TimeConstraintSchema(BaseModel):
    window: str | None = None      # per_meal, per_day, per_week, per_month
    lookback_days: int | None = None

class ScopeSchema(BaseModel):
    target: str = "student"        # student, branch, hostel, institution
    filters: dict = {}

class ActionSchema(BaseModel):
    type: str                      # generate_warning, send_email, increase_penalty, etc.
    params: dict = {}

class RuleCreateSchema(BaseModel):
    name: str
    description: str | None = None
    type: str                      # threshold, frequency, trend, composite, device
    priority: str                  # critical, high, medium, low
    active: bool = True
    conditions: list[ConditionGroupSchema]
    time_constraints: TimeConstraintSchema | None = None
    scope: ScopeSchema = ScopeSchema()
    actions: list[ActionSchema]
    chain_to_rule_id: UUID | None = None
    # ⚠ L2-audit-fix: Requires @model_validator to reject contradictory actions (e.g., two `classify_student` with different statuses)

class RuleUpdateSchema(BaseModel):         # All optional
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    active: bool | None = None
    conditions: list[ConditionGroupSchema] | None = None
    time_constraints: TimeConstraintSchema | None = None
    scope: ScopeSchema | None = None
    actions: list[ActionSchema] | None = None
    chain_to_rule_id: UUID | None = None
    # ⚠ L2-audit-fix: Requires @model_validator to reject contradictory actions if actions are updated

class RuleSchema(BaseModel):
    id: UUID
    name: str
    description: str | None
    type: str
    priority: str
    active: bool
    conditions: list[ConditionGroupSchema]
    time_constraints: TimeConstraintSchema | None
    scope: ScopeSchema
    actions: list[ActionSchema]
    chain_to_rule_id: UUID | None
    execution_count: int
    last_triggered_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

class TestPayloadSchema(BaseModel):
    waste_grams: float | None = None
    meal_type: str | None = None
    student_branch: str | None = None
    student_year: int | None = None
    frequency_count: int | None = None

class TestResultSchema(BaseModel):
    rule_id: UUID
    matched: bool
    matched_conditions: list[dict]
    would_execute_actions: list[dict]
    reason: str

class SimulationResultSchema(BaseModel):
    rule_id: UUID
    period_from: date
    period_to: date
    total_events_evaluated: int
    matched_count: int
    projected_warnings: int
    projected_penalties: int
    projected_emails: int
    sample_matches: list[dict]

class RuleExecutionSchema(BaseModel):
    id: UUID
    rule_id: UUID
    trigger_event_type: str
    student_id: UUID | None
    matched_conditions: dict
    executed_actions: dict
    result_status: str
    executed_at: datetime

class FieldOptionSchema(BaseModel):
    field: str
    label: str
    type: str                # numeric, string, enum, count
    operators: list[str]
    enum_values: list[str] | None = None

class ChainNodeSchema(BaseModel):
    id: UUID
    name: str
    type: str

class ChainEdgeSchema(BaseModel):
    from_rule_id: UUID
    to_rule_id: UUID

class ChainDataSchema(BaseModel):
    nodes: list[ChainNodeSchema]
    edges: list[ChainEdgeSchema]

class OperatorOptionSchema(BaseModel):
    operator: str
    label: str
    applies_to: list[str]    # numeric, string, enum

class ActionOptionSchema(BaseModel):
    type: str
    label: str
    required_params: list[str]
    optional_params: list[str]

class PaginatedRules(PaginatedBase):
    items: list[RuleSchema]

class PaginatedExecutions(PaginatedBase):
    items: list[RuleExecutionSchema]
```

---

## 7. Analytics Schemas
**File:** `app/schemas/analytics.py`

```python
class KpiCardSchema(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    trend: float | None = None      # % change vs previous period
    trend_direction: str | None = None   # up, down, stable

class OverviewKpisSchema(BaseModel):
    total_waste_today_grams: float
    total_waste_week_grams: float
    total_waste_month_grams: float
    avg_daily_waste_grams: float
    waste_reduction_pct: float | None
    peak_waste_time: str | None
    total_active_students: int
    students_under_warning: int
    students_under_penalty: int
    active_devices: int
    offline_devices: int
    alerts_today: int
    rule_violations_today: int

class TrendPointSchema(BaseModel):
    label: str                 # date or week label
    value: float

class TrendDataSchema(BaseModel):
    type: str
    data: list[TrendPointSchema]

class ComparisonDataSchema(BaseModel):
    current_label: str
    previous_label: str
    current_data: list[TrendPointSchema]
    previous_data: list[TrendPointSchema]

class MealDistributionItemSchema(BaseModel):
    meal_type: str
    total_grams: float
    percentage: float

class DistributionDataSchema(BaseModel):
    period: str
    data: list[MealDistributionItemSchema]

class FoodRankingItemSchema(BaseModel):
    food_name: str
    total_grams: float
    entry_count: int
    percentage: float

class FoodRankingSchema(BaseModel):
    period: str
    data: list[FoodRankingItemSchema]

class StudentRankingItemSchema(BaseModel):
    rank: int
    student_id: UUID
    device_id: str
    name: str | None              # From mapping
    avg_waste_grams: float
    total_waste_grams: float
    violation_count: int
    status: str

class StudentRankingSchema(BaseModel):
    period: str
    data: list[StudentRankingItemSchema]

class PeakDataSchema(BaseModel):
    peak_hour: int | None         # 0–23
    peak_meal: str | None
    peak_weekday: str | None
    peak_hour_grams: float | None
    heatmap_data: list[dict]      # [{hour, weekday, avg_grams}]

class ScoreDistributionSchema(BaseModel):
    excellent_count: int          # 90–100
    good_count: int               # 75–89
    average_count: int            # 50–74
    poor_count: int               # <50
    overall_avg: float

class ImprovementDataSchema(BaseModel):   # Used by GET /analytics/improvement-tracking
    student_id: UUID
    device_id: str
    name: str | None
    current_avg_grams: float
    previous_avg_grams: float
    improvement_pct: float
    direction: str               # "improving", "stable", "worsening"
```

---

## 8. Notification Schemas
**File:** `app/schemas/notifications.py`

```python
class NotificationCreateSchema(BaseModel):
    type: str
    channel: str               # email, dashboard, both
    subject: str
    body: str
    recipient_type: str        # individual, branch, hostel, year, all
    recipient_ids: list[str]   # student IDs or group identifiers
    template_id: UUID | None = None

class BroadcastSchema(BaseModel):
    subject: str
    body: str
    channel: str
    recipient_type: str        # branch, hostel, year, all
    recipient_filter: dict = {}   # {branch: "CSE"} or {year: 2}
    template_id: UUID | None = None

class ScheduleNotifSchema(NotificationCreateSchema):
    scheduled_at: datetime

class NotificationSchema(BaseModel):
    id: UUID
    type: str
    channel: str
    subject: str
    status: str
    recipient_type: str
    is_read: bool
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

class NotifStatsSchema(BaseModel):
    unread: int
    sent_today: int
    failed: int
    pending: int

class BroadcastResultSchema(BaseModel):
    total_recipients: int
    queued: int
    failed: int

class NotificationDetailSchema(NotificationSchema):
    body: str
    sender_id: UUID | None
    recipient_ids: list[str]
    template_id: UUID | None
    retry_count: int
    related_entity_type: str | None
    related_entity_id: UUID | None

class PaginatedNotifications(PaginatedBase):
    items: list[NotificationSchema]

class DeliveryStatusItemSchema(BaseModel):   # [M5-audit-fix] Per-recipient delivery tracking
    recipient_id: str
    recipient_email: str | None
    channel: str                             # email, dashboard
    status: str                              # delivered, failed, pending
    delivered_at: datetime | None
    error: str | None

class DeliveryStatusSchema(BaseModel):       # [M5-audit-fix] Response for GET /notifications/{id}/delivery
    notification_id: UUID
    total_recipients: int
    delivered: int
    failed: int
    pending: int
    deliveries: list[DeliveryStatusItemSchema]
```

---

## 9. Report Schemas
**File:** `app/schemas/reports.py`

```python
class ReportConfigSchema(BaseModel):
    type: str                  # daily, weekly, monthly, custom, student_history, etc.
    format: str                # pdf, csv, excel
    date_from: date | None = None
    date_to: date | None = None
    student_id: UUID | None = None   # For student_history type
    filters: dict = {}

class ReportSchema(BaseModel):
    id: UUID
    type: str
    format: str
    status: str
    file_size: int | None
    generated_by: UUID
    generated_at: datetime | None
    created_at: datetime

class ScheduleCreateSchema(BaseModel):
    report_type: str
    format: str
    frequency: str             # daily, weekly, monthly
    day_of_week: str | None = None
    time_of_day: str           # "08:00"
    email_recipients: list[str] = []
    auto_email: bool = False
    active: bool = True

class ReportScheduleSchema(BaseModel):
    id: UUID
    report_type: str
    format: str
    frequency: str
    day_of_week: str | None
    time_of_day: str
    email_recipients: list[str]
    auto_email: bool
    active: bool
    last_run: datetime | None
    next_run: datetime | None

class ScheduleUpdateSchema(BaseModel):    # All optional for PATCH
    report_type: str | None = None
    format: str | None = None
    frequency: str | None = None
    day_of_week: str | None = None
    time_of_day: str | None = None
    email_recipients: list[str] | None = None
    auto_email: bool | None = None
    active: bool | None = None

class PaginatedReports(PaginatedBase):
    items: list[ReportSchema]
```

---

## 10. Config Schemas
**File:** `app/schemas/config.py`

```python
class ThresholdSchema(BaseModel):
    waste_threshold_grams: float = 150.0
    warning_threshold_grams: float = 100.0
    penalty_threshold_grams: float = 200.0
    improvement_target_pct: float = 25.0
    reset_duration_days: int = 30
    warning_count_for_penalty: int = 5

class MealTimingSchema(BaseModel):
    name: str
    display_name: str
    start_time: str            # "07:00"
    end_time: str              # "09:30"
    is_active: bool = True
    order_index: int

class BranchSchema(BaseModel):
    code: str                  # CSE, ECE, ME
    name: str                  # Computer Science & Engineering

class SystemPolicySchema(BaseModel):
    sync_frequency_minutes: int = 5
    offline_handling: str = "queue"
    backup_interval_hours: int = 24
    data_retention_days: int = 365
    log_retention_days: int = 30
    audit_retention_days: int = 90

class AppearanceConfigSchema(BaseModel):
    theme: str = "dark"
    logo_path: str | None = None
    primary_color: str = "#6366f1"
    institution_display_name: str | None = None

class SecurityConfigSchema(BaseModel):
    access_token_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7
    min_password_length: int = 8
    require_uppercase: bool = True
    require_numbers: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 120

class ConfigDataSchema(BaseModel):
    """(G6) Generic response for get_config() and reset_defaults()."""
    section: str
    data: dict  # Section-specific key-value pairs from system_config
    # NOTE: `data` is typed as `dict` intentionally — it holds different
    # shapes per section (ThresholdSchema, MealTimingSchema, etc.).
    # Frontend TypeScript types must be narrowed manually based on `section`.

class ConfigUpdateSchema(BaseModel):
    """(G4) Generic input for update_config(). The service validates `data` against
    the section-specific schema (ThresholdSchema, MealTimingSchema, etc.) internally."""
    data: dict

class DeviceConfigSchema(BaseModel):
    """(M6) Config section for /config/device route."""
    device_offline_threshold_minutes: int = 10   # Used by aggregation_worker
    heartbeat_interval_seconds: int = 60
    sync_batch_size: int = 100
```

---

## 11. Audit Schemas
**File:** `app/schemas/audit.py`

```python
class AuditEventSchema(BaseModel):
    id: UUID
    event_type: str
    action: str
    resource_type: str
    resource_id: str | None
    user_id: UUID | None
    user_name: str | None
    user_role: str | None
    ip_address: str | None
    summary: str
    created_at: datetime

class AuditEventDetailSchema(AuditEventSchema):
    user_agent: str | None
    before_state: dict | None
    after_state: dict | None
    metadata: dict | None

class AuditStatsSchema(BaseModel):
    total_today: int
    login_events: int
    config_changes: int
    rule_changes: int
    warning_events: int

class TimelineGroupSchema(BaseModel):
    user_id: UUID
    user_name: str
    date: date
    events: list[AuditEventSchema]

class TimelineDataSchema(BaseModel):
    groups: list[TimelineGroupSchema]

class PaginatedAuditEvents(PaginatedBase):
    items: list[AuditEventSchema]
```

---

## 12. Filter Preset Schemas
**File:** `app/schemas/filter_presets.py`

```python
class FilterPresetCreateSchema(BaseModel):
    name: str
    filter_state: dict

class FilterPresetUpdateSchema(BaseModel):
    name: str | None = None
    filter_state: dict | None = None

class FilterPresetSchema(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    filter_state: dict
    created_at: datetime
```

---

## 13. Common Schemas
**File:** `app/schemas/common.py`

```python
class PaginatedBase(BaseModel):
    total: int
    page: int
    size: int
    pages: int

class MessageSchema(BaseModel):
    message: str

class ErrorSchema(BaseModel):
    detail: str

class SystemInfoSchema(BaseModel):
    os_version: str
    python_version: str
    app_version: str
    db_size_mb: float
    uptime_seconds: float
    disk_usage_pct: float
    ram_usage_pct: float
    cpu_usage_pct: float

class LogoUrlSchema(BaseModel):
    logo_url: str

class TempPasswordSchema(BaseModel):
    temp_password: str
    message: str

class CacheResultSchema(BaseModel):
    cleared: bool
    keys_removed: int

class OptimizeResultSchema(BaseModel):
    success: bool
    freed_mb: float

class RestoreResultSchema(BaseModel):
    success: bool
    message: str
    restored_at: datetime
```

---

## 14. Template Schemas
**File:** `app/schemas/templates.py`

```python
class TemplateCreateSchema(BaseModel):
    name: str
    type: str                    # warning, penalty, appreciation, awareness, custom, device_offline
    subject: str
    body_html: str               # Jinja2 HTML
    variables: list[str] = []   # Declared variable names e.g. ["student_name", "waste_grams"]

class TemplateUpdateSchema(BaseModel):   # All optional
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    variables: list[str] | None = None

class EmailTemplateSchema(BaseModel):
    id: UUID
    name: str
    type: str
    subject: str
    body_html: str
    variables: list[str]
    is_default: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime

class SampleDataSchema(BaseModel):       # Used by preview_template
    variables: dict                      # {"student_name": "Alice", "waste_grams": 250}

class RenderedHtmlSchema(BaseModel):
    html: str
```

---

## 15. Settings Schemas
**File:** `app/schemas/settings.py`

```python
class UserCreateSchema(BaseModel):
    email: EmailStr
    name: str
    role: str
    password: str | None = None   # If None, system generates a temp password

class UserUpdateSchema(BaseModel):       # All optional
    name: str | None = None
    role: str | None = None
    email: EmailStr | None = None

class BackupSchema(BaseModel):
    id: UUID
    filename: str
    file_size: int | None
    backup_type: str             # manual, scheduled, pre_restore
    status: str                  # creating, available, deleted
    triggered_by: UUID | None
    created_at: datetime
```

---

## 16. Role Schemas
**File:** `app/schemas/roles.py`

```python
class RoleSchema(BaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: dict            # {"students": ["read", "write"], "rules": ["read"]}
    is_system: bool
    created_at: datetime
    updated_at: datetime

class RoleUpdateSchema(BaseModel):       # Only permissions are updatable
    permissions: dict
    description: str | None = None
```
