# CleanPlates — Rule Engine Internals

**Phase:** 4  
**Files:** `app/engine/condition_matcher.py`, `app/engine/action_executor.py`, `app/engine/event_bus.py`  
**Orchestrator:** `app/services/rule_engine_service.py`

---

## Overview

The rule engine is **stateless** and **event-driven**. On every trigger event, it:
1. Loads all active rules from DB (no in-memory cache — always fresh).
2. For each rule, runs `ConditionMatcher` against the event context.
3. If matched, runs `ActionExecutor` to dispatch actions.
4. Logs a `RuleExecutionModel` record regardless of outcome.

---

## Event Types

| Event Type | Published By | Payload Fields |
|-----------|-------------|----------------|
| `waste_entry_created` | `waste_service.create_waste_entry()` | `student_id`, `device_id`, `weight_grams`, `meal_type`, `food_items[]`, `severity`, `session_date`, `timestamp` |
| `warning_issued` | `warning_service.create_warning()` | `student_id`, `warning_id`, `level`, `reason`, `current_warning_count` |
| `penalty_applied` | `warning_service.apply_penalty()` | `student_id`, `penalty_id`, `points`, `warning_id` |
| `device_offline` | `aggregation_worker` (hourly check) | `device_id`, `last_heartbeat`, `offline_duration_minutes` |

---

## `app/engine/condition_matcher.py`

### Class: `ConditionMatcher`

**Purpose:** Evaluates a rule's `conditions` JSON (array of `ConditionGroup`) against a flat event context dict.

> **Note (B5 — DB Session in ARQ context):** `ConditionMatcher` requires a DB session for frequency/trend/aggregate conditions. ARQ workers do **not** use FastAPI's `Depends(get_db_session)`. The worker must create its own session directly:
> ```python
> async with AsyncSessionLocal() as db:
>     matcher = ConditionMatcher(db=db)
>     result = await matcher.match(rule.conditions, context)
> ```
> `ConditionMatcher.__init__` must accept `db: AsyncSession` and store it as `self.db`. The session is created per `evaluate_event` call inside `rule_engine_service.evaluate_event()`, which is itself called from the ARQ worker.

```python
class ConditionMatcher:
    def __init__(self, db: AsyncSession)
    async def match(self, condition_groups: list[ConditionGroupSchema], context: dict) -> bool
    async def _match_group(self, group: ConditionGroupSchema, context: dict) -> bool
    async def _match_single(self, condition: ConditionSchema, context: dict) -> bool
    def _match_numeric(self, operator: str, field_value: float, threshold: float) -> bool
    def _match_string(self, operator: str, field_value: str, target: str) -> bool
    async def _match_frequency(self, condition: ConditionSchema, context: dict) -> bool
    async def _match_trend(self, condition: ConditionSchema, context: dict) -> bool
    async def _match_aggregate(self, condition: ConditionSchema, context: dict) -> bool
```

### Condition Fields Available

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `waste_grams` | numeric | `event.weight_grams` | Current entry waste weight |
| `meal_type` | string/enum | `event.meal_type` | `breakfast`, `lunch`, `dinner` |
| `severity` | string/enum | `event.severity` | `normal`, `warning`, `high` |
| `food_item` | string | `event.food_items[].name` | Any food item in the entry |
| `student_branch` | string | `student_mapping.branch` | Student's branch (CSE, ECE, etc.) |
| `student_year` | numeric | `student_mapping.year` | Year 1–4 |
| `warning_count` | numeric | `student.warning_count` | Current active warnings |
| `penalty_count` | numeric | `student.penalty_count` | Total penalties |
| `sustainability_score` | numeric | `student.sustainability_score` | 0–100 |
| `frequency_count` | numeric | DB query | Number of entries matching criteria within time window |
| `avg_waste_7d` | numeric | DB query | Student's avg waste grams over last 7 days |
| `avg_waste_30d` | numeric | DB query | Student's avg waste grams over last 30 days |

### Operators

| Operator | Applies To | Description |
|----------|-----------|-------------|
| `gt` | numeric | Greater than |
| `gte` | numeric | Greater than or equal |
| `lt` | numeric | Less than |
| `lte` | numeric | Less than or equal |
| `eq` | numeric, string | Equals |
| `neq` | numeric, string | Not equals |
| `in` | string, enum | Value in list |
| `not_in` | string, enum | Value not in list |
| `contains` | string | Substring match |
| `between` | numeric | Inclusive range `[min, max]` |

### Logic: ConditionGroup evaluation

- `logic: "AND"` → ALL conditions in the group must match  
- `logic: "OR"` → ANY condition in the group must match  
- **Multiple groups** → ALL groups must match (groups are always AND-chained)

### Frequency / Trend Matching (DB-backed)

These conditions require a DB query:

- `frequency_count`: counts `waste_entries` for `student_id` within `time_constraints.window` period matching optional sub-filters (e.g., `meal_type`, `min_grams`). If count ≥ threshold → match.
- `avg_waste_7d` / `avg_waste_30d`: compute rolling average from `waste_entries` → compare with operator+value.
- `match_trend`: compare current 7-day avg vs previous 7-day avg → compute delta% → apply operator.

---

## `app/engine/action_executor.py`

### Class: `ActionExecutor`

**Purpose:** Dispatches actions from `rule.actions` JSON array after a rule match. Each action is independent — failure of one does not block others. All outcomes are collected and returned.

```python
class ActionExecutor:
    async def execute(self, actions: list[ActionSchema], context: dict, db: AsyncSession) -> list[ActionResult]
    async def generate_warning(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
    async def send_email(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
    async def increase_penalty(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
    async def trigger_escalation(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
    async def classify_student(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
    async def create_audit_log(self, params: dict, context: dict, db: AsyncSession) -> ActionResult
```

> **Action Execution Order Contract:** `execute()` must sort the `actions` list by the following priority before dispatching, regardless of the order they appear in `rule.actions` JSON:
>
> | Priority | Action Type |
> |----------|-------------|
> | 1 | `generate_warning` |
> | 2 | `send_email` |
> | 3 | `trigger_escalation` |
> | 4 | `increase_penalty` |
> | 5 | `classify_student` |
> | 6 | `create_audit_log` |
>
> **Rationale:** `trigger_escalation` requires an existing active warning for the student. If a rule's actions include both `generate_warning` and `trigger_escalation`, `generate_warning` must complete first so that the warning row exists when `trigger_escalation` queries for it. Sorting by priority makes this deterministic regardless of how the rule author ordered actions in the UI.
>
> **Failure isolation:** Each action is run independently — a failure in one action must not abort the remaining actions. Collect all `ActionResult` outcomes and log the full list in `RuleExecutionModel.executed_actions`.

### Action Types & Params

| Action Type | Required Params | Optional Params | Description |
|-------------|----------------|----------------|-------------|
| `generate_warning` | `level` (`level_1`/`level_2`/`level_3`), `reason` | `send_email` (bool, default false) | Creates a `WarningModel` for the student; increments `student.warning_count`; queues email if flag set |
| `send_email` | `template_id` or `subject`+`body` | `recipient_override` | Sends email to student's mapped email (from `student_mappings.email`); creates a `NotificationModel` record |
| `increase_penalty` | `points` (int) | `reason`, `send_email` | Creates a `PenaltyModel` with source `rule_id`; updates `student.penalty_count`; recalculates student status |
| `trigger_escalation` | `escalated_to_role`, `reason` | — | Requires an existing active warning for the student; creates `EscalationModel`; sets `warning.status=escalated` |
| `classify_student` | `status` (`green`/`yellow`/`orange`/`red`) | — | Force-sets `student.status`; bypasses normal threshold logic; logs audit event |
| `create_audit_log` | `summary` | `metadata` (dict) | Inserts an `AuditEventModel` with `event_type=rule.action`, `resource_type=student`; no side effects |

### ActionResult

```python
class ActionResult:
    action_type: str
    success: bool
    entity_id: UUID | None   # ID of created warning/penalty/notif
    error: str | None
```

---

## `app/engine/event_bus.py`

### Class: `EventBus`

**Purpose:** Redis Pub/Sub backed event bus. Publishers push events; the ARQ worker subscribes and dispatches to `RuleEngineService.evaluate_event()`.

```python
class EventBus:
    def __init__(self, redis_url: str)
    async def publish(self, event_type: str, event_data: dict) -> None
    async def subscribe(self, event_type: str, handler: Callable) -> None
    async def listen(self) -> None          # Called by ARQ worker loop
```

### Implementation Notes

- **Channel naming:** Redis channel = `cleanplates:events:{event_type}` (e.g., `cleanplates:events:waste_entry_created`)
- **Payload:** JSON-serialized dict. Always includes `event_type`, `timestamp`, and all event-specific fields.
- **Publisher** (`publish`): serialise dict → `redis.publish(channel, json_payload)`. Fire-and-forget (no await on delivery confirmation).
- **Subscriber** (`listen`): `redis.subscribe(...)` → loop on messages → deserialise → call handler. Run in ARQ worker.
- **Dead-letter handling:** If handler raises, use standard `logger.error` to log the failure. Do NOT retry automatically.

### ARQ Worker Integration (`app/workers/rule_worker.py`)

```python
async def rule_engine_worker(ctx):
    bus = EventBus(settings.REDIS_URL)
    await bus.subscribe("waste_entry_created", rule_engine_service.evaluate_event)
    await bus.subscribe("warning_issued", rule_engine_service.evaluate_event)
    await bus.subscribe("penalty_applied", rule_engine_service.evaluate_event)
    await bus.subscribe("device_offline", rule_engine_service.evaluate_event)
    await bus.listen()
```

---

## `app/services/rule_engine_service.py`

### Orchestration Flow

```
evaluate_event(event_type, event_data)
│
├── Load all rules WHERE active=true AND is_deleted=false FROM DB
│
├── For each rule:
│   ├── Build context dict from event_data + DB lookups (student, mapping)
│   ├── ConditionMatcher.match(rule.conditions, context)
│   │   ├── True  → ActionExecutor.execute(rule.actions, context)
│   │   │           └── Collect ActionResult[]
│   │   └── False → skip
│   │
│   └── Insert RuleExecutionModel(
│           rule_id, trigger_event_type, trigger_entity_id,
│           student_id, matched_conditions, executed_actions,
│           result_status, executed_at
│       )
│
└── Return EvaluationResult[] (one per rule that was evaluated)
```

### Context Building

Before matching, the service builds a flat `context` dict:

```python
context = {
    # From event payload
    "waste_grams": event_data.get("weight_grams"),
    "meal_type": event_data.get("meal_type"),
    "severity": event_data.get("severity"),
    "food_items": event_data.get("food_items", []),
    "student_id": event_data.get("student_id"),
    "device_id": event_data.get("device_id"),
    "timestamp": event_data.get("timestamp"),
    "event_type": event_type,

    # From DB — fetched once per evaluate_event call
    "student_branch": mapping.branch if mapping else None,
    "student_year": mapping.year if mapping else None,
    "warning_count": student.warning_count,
    "penalty_count": student.penalty_count,
    "sustainability_score": student.sustainability_score,
    "student_status": student.status,
}
```

---

## Rule Engine Statelessness Contract

Per `06-phase-wise-plan.md` Cross-Cutting Rule #4:

> **Rule engine must be stateless — reload active rules from DB on each evaluation.**

This means:
- No in-memory rule cache.
- No persistent rule object between events.
- Rules are always read fresh: `SELECT * FROM rules WHERE active=true AND is_deleted=false`.
- Config thresholds (waste_threshold_grams etc.) are read via `config_service.get_config("thresholds")` inside condition matchers that reference threshold fields — never hardcoded.
