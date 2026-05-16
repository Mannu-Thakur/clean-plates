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

> **Note (B5 — DB Session in ARQ context):** `ConditionMatcher` requires a DB session for frequency/trend/aggregate conditions. ARQ workers do **not** use FastAPI's `Depends(get_db_session)`. The worker must create its own session via `ctx['db_session_factory']` — **[F8-fix]** do NOT call `AsyncSessionLocal()` directly:
> ```python
> db_session_factory = ctx['db_session_factory']
> async with db_session_factory() as db:
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
    async def execute(self, actions: list[ActionSchema], context: dict, db: AsyncSession, arq_pool: ArqRedis) -> list[ActionResult]
    async def generate_warning(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
    async def send_email(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
    async def increase_penalty(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
    async def trigger_escalation(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
    async def classify_student(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
    async def create_audit_log(self, params: dict, context: dict, db: AsyncSession, arq_pool: ArqRedis) -> ActionResult
```

> **⚠ B2-fix (ARQ Pool Required):** `arq_pool: ArqRedis` is required because several actions enqueue downstream jobs: `generate_warning` calls `warning_service.create_warning()` which enqueues a `warning_issued` event job; `send_email` enqueues `send_email_task` (Phase 6+); `increase_penalty` may trigger events. Per Cross-Cutting Rule #11, all service functions that enqueue jobs must explicitly receive `arq_pool`. The ARQ worker passes `ctx['redis']`; FastAPI routes pass `Depends(get_arq_pool)`.

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
>
> **⚠ L2-audit-fix (Contradictory Action Validation):** Add validation to `RuleCreateSchema` or `RuleController.create_rule()` that rejects rule definitions containing mutually exclusive actions of the exact same type (e.g., two `classify_student` actions attempting to set the student to both `green` and `red` simultaneously). This prevents admin misconfigurations from causing unpredictable side effects.

### Action Types & Params

| Action Type | Required Params | Optional Params | Description |
|-------------|----------------|----------------|-------------|
| `generate_warning` | `level` (`level_1`/`level_2`/`level_3`), `reason` | `send_email` (bool, default false) | Creates a `WarningModel` for the student; **⚠ H3-audit-fix:** increments `student.warning_count` via SQL-level atomic update (`UPDATE students SET warning_count = warning_count + 1 WHERE id = :id`) instead of ORM memory update to prevent lost updates under concurrency; queues email if flag set |
| `send_email` | `template_id` or `subject`+`body` | `recipient_override` | Sends email to student's mapped email (from `student_mappings.email`); creates a `NotificationModel` record |
| `increase_penalty` | `points` (int) | `reason`, `send_email` | Creates a `PenaltyModel` with source `rule_id`; **⚠ H3-audit-fix:** updates `student.penalty_count` via SQL-level atomic update; recalculates student status |
| `trigger_escalation` | `escalated_to_role`, `reason` | — | Requires an existing active warning for the student; creates `EscalationModel`; sets `warning.status=escalated` |
| `classify_student` | `status` (`green`/`yellow`/`orange`/`red`) | — | Force-sets `student.status`; **⚠ H4-audit-fix:** MUST also set `student.is_status_manual = True` so that `aggregation_service.update_student_status()` skips this student and does not overwrite the manually-set status back to a threshold-computed value; bypasses normal threshold logic; logs audit event |
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

**Purpose:** Redis Pub/Sub backed event bus **reserved strictly for WebSocket fan-out in Phase 7**. The event bus does **NOT** drive rule evaluation — rule evaluation uses ARQ job queue for at-least-once delivery (see below).

```python
class EventBus:
    def __init__(self, redis_url: str)
    async def publish(self, event_type: str, event_data: dict) -> None
    async def subscribe(self, event_type: str, handler: Callable) -> None
    async def listen(self) -> None          # Called by ws_service subscriber loop (Phase 7)
```

### Implementation Notes

- **Channel naming:** Redis channel = `cleanplates:events:{event_type}` (e.g., `cleanplates:events:waste_entry_created`)
- **Payload:** JSON-serialized dict. Always includes `event_type`, `timestamp`, and all event-specific fields.
- **Publisher** (`publish`): serialise dict → `redis.publish(channel, json_payload)`. Fire-and-forget (no await on delivery confirmation).
- **Subscriber** (`listen`): `redis.subscribe(...)` → loop on messages → deserialise → call handler. Used by `ws_service.subscriber_loop()` in Phase 7 to push events to connected WebSocket clients.
- **⚠ NOT for rule evaluation:** Redis Pub/Sub is fire-and-forget. Events are silently lost if no subscriber is active. Rule evaluation requires at-least-once delivery — use ARQ job queue instead.

### ARQ Worker Integration (`app/workers/rule_worker.py`)

> **⚠ B1-fix (Corrected):** Rule evaluation uses **ARQ job queue** (not Redis Pub/Sub). Services enqueue jobs via `await arq_pool.enqueue_job("evaluate_event", event_type, event_data)`. The ARQ worker receives these jobs and calls `rule_engine_service.evaluate_event()`. This provides at-least-once delivery with automatic retry.

```python
# ARQ task function — registered in WorkerSettings.functions
async def evaluate_event(ctx, event_type: str, event_data: dict):
    """Receives enqueued rule evaluation jobs from waste_service / warning_service."""
    db_session_factory = ctx['db_session_factory']
    arq_pool = ctx['redis']  # ArqRedis instance
    async with db_session_factory() as db:
        await rule_engine_service.evaluate_event(
            event_type=event_type,
            event_data=event_data,
            db=db,
            arq_pool=arq_pool,
        )
```

> **Note:** `event_bus.publish()` is still called by services alongside `arq_pool.enqueue_job()` — but only for WebSocket fan-out (Phase 7). The two mechanisms serve different purposes: ARQ for reliable rule processing, Pub/Sub for real-time UI updates.

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
│   ├── If rule.chain_to_rule_id is set:
│   │   ├── **[M2-audit-fix]** Fetch the chained rule by ID
│   │   ├── If chained rule is_deleted=true OR active=false → **HALT chain** (log warning, do NOT raise exception)
│   │   └── If chained rule is valid → evaluate it (with depth tracking per M4-fix)
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
