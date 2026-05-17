# Phase 4 — Warnings & Penalties + Rule Engine

**Duration:** ~6 days  
**Depends on:** Phase 1 (tokens, Modal, ConfirmDialog, Toggle, Tabs), Phase 3 (DataTable, FilterBar, Pagination)  
**Required before:** Phase 5 (Modal and DataTable patterns stabilized)  
**Pages implemented:**

- Page 07: `/dashboard/warnings` — Warnings & Penalties Management
- Page 08: `/dashboard/rules` — Rule Engine Builder

---

## Page 07 — Warnings & Penalties (`/dashboard/warnings`)

### Route: `src/routes/dashboard/warnings/+page.svelte`

**Access:** super_admin, institution_admin, mess_admin (read-only for analytics_viewer)

### Layout

```
┌───────────────────────────────────────────────────────────────┐
│  PageHeader: "Warnings & Penalties"  [+ Manual Warn] [Export] │
├───────────────────────────────────────────────────────────────┤
│  Stat row: [Active Warnings] [Resolved] [Escalated] [Penalties]│
├───────────────────────────────────────────────────────────────┤
│  [Warnings] [Penalties] [Escalations]   ← Tabs               │
├───────────────────────────────────────────────────────────────┤
│  FilterBar + DataTable + Pagination                            │
└───────────────────────────────────────────────────────────────┘
```

### API Calls

| Action                   | Endpoint                                                                          |
| ------------------------ | --------------------------------------------------------------------------------- |
| List warnings            | `GET /api/v1/warnings?page=&size=&status=&level=&student_id=&date_from=&date_to=` |
| Get warning              | _(No single-item GET endpoint — warning detail is populated from list row data)_  |
| Create warning           | `POST /api/v1/students/{student_id}/warnings`                                     |
| Update warning           | `PATCH /api/v1/warnings/{id}`                                                     |
| Resolve warning          | `PATCH /api/v1/warnings/{id}/resolve` with `ResolveWarningSchema` body            |
| Escalate warning         | `POST /api/v1/warnings/{id}/escalate`                                             |
| Bulk resolve             | `PATCH /api/v1/warnings/bulk/resolve`                                             |
| Export warnings          | `GET /api/v1/warnings/export?format=csv` → `api.download()`                       |
| List penalties           | `GET /api/v1/penalties?page=&size=`                                               |
| Apply penalty to warning | `POST /api/v1/warnings/{warning_id}/apply-penalty`                                |
| Direct student penalty   | `POST /api/v1/students/{student_id}/penalties`                                    |
| Revoke penalty           | `PATCH /api/v1/penalties/{id}/revoke`                                             |
| List escalations         | `GET /api/v1/escalations?page=&size=`                                             |
| Review escalation        | `POST /api/v1/escalations/{id}/review`                                            |

### Stat Cards Row

| Card             | Value | Tone           |
| ---------------- | ----- | -------------- |
| Active Warnings  | count | warn (primary) |
| Resolved Today   | count | good (up)      |
| Escalated        | count | bad (down)     |
| Active Penalties | count | bad (down)     |

### Tab 1: Warnings

**FilterBar fields:**

- Search (student name / roll number)
- Status: All / Active / Resolved / Escalated
- Level: All / Yellow / Orange / Red
- Date Range picker
- Rule filter: SelectField (list of rule names)

**DataTable Columns:**

| Column  | Field                           | Sortable |
| ------- | ------------------------------- | -------- |
| Student | `student_name` + `student_roll` | Yes      |
| Level   | `level` (styled badge)          | Yes      |
| Reason  | `reason` (truncated 60 chars)   | No       |
| Rule    | `rule_name`                     | No       |
| Status  | `status` badge                  | Yes      |
| Date    | `created_at`                    | Yes      |
| Actions | —                               | No       |

**Level Badge Mapping:**

- `yellow` → `badge-primary` with ⚠ icon
- `orange` → custom `text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded-sm text-xs font-semibold`
- `red` → `badge-down` with 🚫 icon

**Status Badge:**

- `active` → `badge-primary`
- `resolved` → `badge-up`
- `escalated` → `badge-down`

**Row Actions (icon buttons):**

- 👁 View — opens detail modal
- ✓ Resolve — opens note modal then `PATCH /api/v1/warnings/{id}/resolve`
- ↑ Escalate — opens escalate modal with note input
- Revoke — `PATCH /api/v1/penalties/{id}/revoke` (Penalties tab only, admin only)

**Warning Detail Modal** (view action):

- Full warning info: student, level, reason, evidence
- Associated waste entry (if from rule): date, weight, food items, plate image if available
- Rule that triggered it (if auto)
- Penalty history for this warning
- Timeline: created → escalated → resolved (visual stepper)
- Action buttons: Resolve / Escalate

**Create Manual Warning Modal** (triggered by "+ Manual Warn"):

- Student search autocomplete (debounced `GET /api/v1/students?search=...`)
- Level selector (yellow/orange/red) — visual toggle buttons
- Reason textarea (required)
- Food items chips (optional multiselect: common items as chips)
- Send email checkbox
- Submit → `POST /api/v1/students/{student_id}/warnings` — the student must be selected via autocomplete first; their `id` is used as the path param

### Tab 2: Penalties

**DataTable Columns:**

| Column  | Field                      | Sortable |
| ------- | -------------------------- | -------- |
| Student | name + roll                | Yes      |
| Type    | `penalty_type` badge       | No       |
| Amount  | `amount`                   | Yes      |
| Reason  | `reason`                   | No       |
| Warning | linked warning (if exists) | No       |
| Status  | `status` badge             | Yes      |
| Date    | `created_at`               | Yes      |
| Actions | —                          | No       |

**Penalty Type Badge:**

- `points` → `badge-info`
- `monetary` → `badge-primary`
- `restriction` → `badge-muted`
- `suspension` → `badge-down`

**Create Direct Penalty Modal:**

- Student search autocomplete (debounced `GET /api/v1/students?search=...` client-side)
- Type selector
- Amount input (conditional: show only if type=monetary/points)
- Reason textarea
- Submit → `POST /api/v1/students/{student_id}/penalties` — the student must be selected via autocomplete first; their `id` is used as the path param

### Tab 3: Escalations

**DataTable Columns:** Student, Original Warning, Level, Escalated To, Note, Status, Date, Actions

**Resolve Escalation Modal:**

- Note textarea
- Resolution: Resolved / Further Escalated / Dismissed
- Submit → `POST /api/v1/escalations/{id}/review` with `ReviewEscalationSchema` body

### Export

- Button in PageHeader: "Export" with Download icon
- Opens mini-modal: format selector (CSV / Excel)
- CSV: `api.download('/warnings/export?format=csv', 'warnings.csv', filters)`
- Excel: same with `format=excel`

### API Types

```typescript
export interface Warning {
  id: string;
  student_id: string;
  student_name: string;
  student_roll_number?: string;
  level: 'yellow' | 'orange' | 'red';
  reason: string;
  rule_id?: string;
  rule_name?: string;
  waste_entry_id?: string;
  status: 'active' | 'resolved' | 'escalated';
  send_email: boolean;
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
  penalties: Penalty[];
  escalations: Escalation[];
}
export interface Penalty {
  id: string;
  warning_id?: string;
  student_id: string;
  penalty_type: 'points' | 'monetary' | 'restriction' | 'suspension';
  amount?: number;
  reason: string;
  status: 'active' | 'paid' | 'waived';
  created_at: string;
}
export interface Escalation {
  id: string;
  warning_id: string;
  student_id: string;
  escalated_to?: string;
  note?: string;
  status: 'pending' | 'resolved' | 'dismissed';
  created_at: string;
}
```

---

## Page 08 — Rule Engine (`/dashboard/rules`)

### Route: `src/routes/dashboard/rules/+page.svelte`

**Access:** super_admin, institution_admin ONLY

> This is the most complex page in the application. The Rule Engine Builder is an interactive form that constructs a JSON rule definition through a visual IF-THEN interface.

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  PageHeader: "Rule Engine"           [Create Rule] [Metadata↓] │
├────────────────────────────────────────────────────────────────┤
│  Stat row: [Total] [Active] [Triggered Today] [Chained Rules]  │
├────────────────────────────────────────────────────────────────┤
│  FilterBar: [Search] [Type▼] [Priority▼] [Status▼]            │
├────────────────────────────────────────────────────────────────┤
│  Rule List Table                          [Execution Log tab]  │
│                                           [Chain View tab]     │
├────────────────────────────────────────────────────────────────┤
│  [Rule List] [Execution Log] [Rule Chains]  ← bottom tabs      │
└────────────────────────────────────────────────────────────────┘
```

### API Calls

| Action             | Endpoint                                                            |
| ------------------ | ------------------------------------------------------------------- |
| List rules         | `GET /api/v1/rules?page=&size=&type=&priority=&status=&search=`     |
| Get rule           | `GET /api/v1/rules/{id}`                                            |
| Create rule        | `POST /api/v1/rules`                                                |
| Update rule        | `PATCH /api/v1/rules/{id}`                                          |
| Delete rule        | `DELETE /api/v1/rules/{id}`                                         |
| Toggle active      | `POST /api/v1/rules/{id}/toggle` with body `{"active": true/false}` |
| Test rule          | `POST /api/v1/rules/{id}/test`                                      |
| Simulate rule      | `POST /api/v1/rules/{id}/simulate`                                  |
| Executions         | `GET /api/v1/rules/{id}/executions?page=&size=`                     |
| Metadata fields    | `GET /api/v1/rules/metadata/fields`                                 |
| Metadata operators | `GET /api/v1/rules/metadata/operators`                              |
| Metadata actions   | `GET /api/v1/rules/metadata/actions`                                |
| Rule chains        | `GET /api/v1/rules/chains`                                          |

### Rule Stats Row

| Card            | Value | Tone      |
| --------------- | ----- | --------- |
| Total Rules     | count | neutral   |
| Active          | count | good (up) |
| Triggered Today | count | primary   |
| Chained Rules   | count | info      |

### Rule List Table

**FilterBar:**

- Search (rule name)
- Type: All / threshold / frequency / trend / composite
- Priority: All / critical / high / medium / low
- Status: All / active / inactive

**DataTable Columns:**

| Column           | Field                   | Width | Sortable |
| ---------------- | ----------------------- | ----- | -------- |
| Name             | `name`                  | 200px | Yes      |
| Type             | `type` badge            | 100px | No       |
| Priority         | `priority` badge        | 90px  | Yes      |
| Active           | Toggle                  | 70px  | No       |
| Triggered Today  | `triggered_today_count` | 100px | Yes      |
| Total Executions | `execution_count`       | 100px | Yes      |
| Last Triggered   | `last_triggered_at`     | 130px | Yes      |
| Actions          | —                       | 150px | No       |

**Priority Badge:**

- `critical` → `badge-down`
- `high` → `badge-primary`
- `medium` → `badge-info`
- `low` → `badge-muted`

**Type Badge:**

- `threshold` → `badge-info`
- `frequency` → `badge-primary`
- `trend` → `badge-muted`
- `composite` → custom style

**Active Toggle** (`Toggle.svelte`):

- Inline PATCH on toggle change → confirm if deactivating active rule

**Row Actions:**

- ✏ Edit → opens RuleBuilder panel
- 🧪 Test → opens TestSimulationModal
- ⏱ Simulate → opens SimulationModal
- 📋 Duplicate → POST with cloned data + "(Copy)" suffix
- 🗑 Delete → `ConfirmDialog` then DELETE

---

### Rule Builder Panel (side panel or modal)

This is the core complex component of the entire application.

**File:** `src/lib/components/rules/RuleBuilder.svelte`

**Layout (slide-in panel from right, 560px wide, dark `.card` background):**

```
┌──────────────────────────────────────────────┐
│  Create Rule / Edit Rule             [×]     │
├──────────────────────────────────────────────┤
│  Name: [input-field]                         │
│  Description: [textarea-field]               │
│  Type: [threshold▼] Priority: [high▼]       │
│  Active: [Toggle]                            │
├──────────────────────────────────────────────┤
│  IF (Conditions)                     [+Add]  │
│  ┌───────────────────────────────────────┐   │
│  │ Logic: [AND▼] / [OR▼]               │   │
│  │ [Field▼] [Operator▼] [Value input]  │   │
│  │ [Field▼] [Operator▼] [Value input]  │   │
│  └───────────────────────────────────────┘   │
│  [+ Add Condition Group]                     │
├──────────────────────────────────────────────┤
│  Time Constraints (optional)                 │
│  Window: [per_meal▼]  Period: [daily▼]      │
├──────────────────────────────────────────────┤
│  Scope                                       │
│  Target: [student▼]  Branch: [ALL▼]         │
├──────────────────────────────────────────────┤
│  THEN (Actions)                      [+Add]  │
│  ┌───────────────────────────────────────┐   │
│  │ Action: [generate_warning▼]          │   │
│  │   Level: [yellow▼]                   │   │
│  │   Send Email: [Toggle]               │   │
│  └───────────────────────────────────────┘   │
│  [+ Add Action]                              │
├──────────────────────────────────────────────┤
│  Chain Rule (optional)                       │
│  On Result → [None▼]  Trigger: [rule...]    │
├──────────────────────────────────────────────┤
│            [Cancel]  [Validate]  [Save Rule] │
└──────────────────────────────────────────────┘
```

**Condition Builder (`ConditionBuilder.svelte`):**

- Field selector: `SelectField` populated from `GET /api/v1/rules/metadata/fields`
  - Options include: `waste_grams`, `meal_type`, `food_item`, `student_status`, `occurrence_count`, `time_of_day`, etc.
- Operator selector: dynamically populated based on selected field type
  - Numeric: `greater_than`, `less_than`, `equals`, `between`, `greater_than_or_equal`
  - String: `equals`, `contains`, `in`
  - Time: `within_window`, `is_between`
- Value input: changes based on field + operator:
  - Numeric: `input-field type="number"`
  - String: `input-field type="text"`
  - Enum (meal_type): `SelectField`
  - Between: two number inputs
- Multiple conditions: AND / OR logic per group
- Multiple condition groups: AND between groups

**Action Builder (`ActionBuilder.svelte`):**

- Action type selector from `GET /api/v1/rules/metadata/actions`:
  - `generate_warning` → shows level (yellow/orange/red) + send_email Toggle
  - `send_email` → shows template selector (from `/api/v1/templates`)
  - `increase_penalty` → shows penalty type + amount
  - `trigger_escalation` → shows escalation level
  - `classify_student` → shows target status
  - `create_audit_log` → shows message input
- Each action is a card within the builder panel

**Validation:**

- Rule name required (non-empty)
- At least 1 condition required
- At least 1 action required
- Numeric values must be valid numbers
- Between: min < max
- Visual inline errors below each problematic field in `text-down`

**Save Flow:**

1. Client-side validation → show errors
2. On valid: `POST /api/v1/rules` (new) or `PATCH /api/v1/rules/{id}` (edit)
3. Success: close panel, refetch rule list, `notify('Rule saved', 'success')`
4. Error: show error in panel header area

---

### Test Rule Modal

**File:** `src/lib/components/rules/RuleTestModal.svelte`

```
┌──────────────────────────────────────┐
│  Test Rule: "Daily Waste Threshold"  │
├──────────────────────────────────────┤
│  Sample event type: [SelectField]    │
│  Sample data (JSON editor):          │
│  { "weight_grams": 250, ... }       │
│  [Run Test]                          │
├──────────────────────────────────────┤
│  Results:                            │
│  ✓ Condition 1: MATCHED (250 > 150) │
│  ✗ Condition 2: NOT MATCHED          │
│  → Actions that WOULD fire: [list]  │
└──────────────────────────────────────┘
```

- JSON textarea for sample data (monospace `font-mono` text-sm)
- Submit → `POST /api/v1/rules/{id}/test` with `{ event_type, sample_data }`
- Results: each condition shown as ✓ or ✗ with the computed value vs threshold

---

### Simulate Rule Modal

**File:** `src/lib/components/rules/RuleSimulateModal.svelte`

```
┌──────────────────────────────────────┐
│  Simulate: "Daily Waste Threshold"   │
├──────────────────────────────────────┤
│  Date Range: [start] → [end]         │
│  [Run Simulation]                    │
├──────────────────────────────────────┤
│  Simulation Results:                 │
│  ● 47 students matched conditions    │
│  ● 23 warnings would be issued       │
│  ● 8 penalties would be triggered    │
│  ● 3 escalations would occur         │
│                                      │
│  Sample matches (first 5):           │
│  [mini DataTable: student, date, val]│
└──────────────────────────────────────┘
```

- `DateRangePicker.svelte` for test period
- Submit → `POST /api/v1/rules/{id}/simulate?date_from={start_date}&date_to={end_date}` (dates as **query params**, not body)

---

### Tab: Execution Log

**DataTable Columns:** Rule Name, Trigger Event, Triggered At, Conditions Matched, Actions Executed, Result Status

**Filter:** Search (rule name), Rule selector, Date range, Result (success/failure/skipped)

```typescript
// Fetch: GET /api/v1/rules/{selectedRuleId}/executions (all if no rule selected)
// Use GET /api/v1/rules/executions if backend supports global listing
```

---

### Tab: Rule Chains

Visual graph showing how rules connect:

- `src/lib/components/rules/RuleChainVisualizer.svelte`
- Pure CSS/SVG flow chart (NO external graph lib required — keep bundle small)
- Data from `GET /api/v1/rules/chains`
- Nodes: `.card px-4 py-2 text-sm` boxes with rule name + priority badge
- Arrows: SVG `<line>` elements connecting nodes
- Click node → navigate to that rule in the builder
- Layout: left-to-right, top-to-bottom by priority
- If chain data is complex: simple table fallback (Rule → Triggers → Rule)

---

### Store: `src/lib/stores/rules.ts`

```typescript
// State:
//   rules: Rule[]
//   total: number
//   stats: RuleStats
//   executions: RuleExecution[]
//   chains: ChainData
//   loading: boolean
//   builderOpen: boolean
//   editingRule: Rule | null
//   metadata: { fields, operators, actions }

// Actions:
//   fetchRules(filters)
//   fetchMetadata()          → GET all 3 metadata endpoints in parallel
//   createRule(data)
//   updateRule(id, data)
//   deleteRule(id)
//   toggleActive(id, active)
//   duplicateRule(id)
//   testRule(id, sampleData)
//   simulateRule(id, dateRange)
//   fetchExecutions(ruleId?)
//   fetchChains()
//   openBuilder(rule?)
//   closeBuilder()
```

---

### API Types

```typescript
export interface Rule {
  id: string;
  name: string;
  description?: string;
  type: 'threshold' | 'frequency' | 'trend' | 'composite';
  priority: 'critical' | 'high' | 'medium' | 'low';
  active: boolean;
  conditions: ConditionGroup[];
  time_constraints?: TimeConstraint;
  scope?: RuleScope;
  actions: RuleAction[];
  execution_count: number;
  triggered_today_count?: number;
  last_triggered_at?: string;
  created_by: string;
  created_at: string;
}

export interface ConditionGroup {
  logic: 'AND' | 'OR';
  conditions: Condition[];
}

export interface Condition {
  field: string;
  operator: string;
  value: unknown;
  value_max?: unknown; // for 'between'
}

export interface TimeConstraint {
  window: 'per_meal' | 'daily' | 'weekly' | 'monthly';
  period?: string;
}

export interface RuleScope {
  target: 'student' | 'device' | 'institution';
  branch?: string;
  mess_id?: string;
}

export interface RuleAction {
  type:
    | 'generate_warning'
    | 'send_email'
    | 'increase_penalty'
    | 'trigger_escalation'
    | 'classify_student'
    | 'create_audit_log';
  params: Record<string, unknown>;
}

export interface RuleExecution {
  id: string;
  rule_id: string;
  rule_name: string;
  trigger_source: string;
  matched_conditions: unknown;
  executed_actions: unknown;
  result_status: 'success' | 'failed' | 'skipped';
  executed_at: string;
}

export interface RuleStats {
  total: number;
  active: number;
  triggered_today: number;
  chained_rules: number;
}

export interface RuleMetadata {
  fields: Array<{
    key: string;
    label: string;
    type: 'number' | 'string' | 'enum' | 'datetime';
    options?: string[];
  }>;
  operators: Array<{ key: string; label: string; applicable_to: string[] }>;
  actions: Array<{
    type: string;
    label: string;
    params: Record<
      string,
      { type: string; required: boolean; options?: string[] }
    >;
  }>;
}
```

---

## Verification Checklist

**Warnings page:**

- [ ] Stat cards show correct counts
- [ ] Warnings DataTable loads paginated with filters
- [ ] Level badges styled correctly (yellow/orange/red)
- [ ] Status badges styled correctly
- [ ] View modal shows full warning detail with timeline stepper
- [ ] Resolve action sends PATCH, table updates
- [ ] Escalate modal works with note input
- [ ] Manual warn modal: student search autocomplete works
- [ ] Export CSV downloads correctly
- [ ] Penalties tab loads and creates direct penalty
- [ ] Escalations tab loads and resolves escalation

**Rules page:**

- [ ] Stat cards show correct rule counts
- [ ] Rule list table loads with filters
- [ ] Active toggle PATCH works with confirm
- [ ] Row actions (Edit, Test, Simulate, Duplicate, Delete) all work
- [ ] Rule Builder panel opens from right (slide-in)
- [ ] Condition builder: fields/operators/values load from metadata
- [ ] Action builder: action types from metadata, params dynamic
- [ ] Validation errors show inline in builder
- [ ] Save creates/updates rule and closes panel
- [ ] Test rule modal: JSON input, results show condition match status
- [ ] Simulate modal: date range, results with student counts
- [ ] Execution log tab loads executions
- [ ] Rule chains tab renders chain graph/table

---

## Exit Criteria

✅ Warnings/penalties full CRUD working  
✅ Rule Builder creates valid rules that the backend accepts  
✅ Rule test/simulate working  
✅ Rule toggle and delete working  
✅ Execution log and chains tabs functional  
✅ No TypeScript errors (`npm run check`)
