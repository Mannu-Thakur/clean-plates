# CleanPlates Frontend — Phase-Wise Implementation Plan

**Stack:** SvelteKit 2 + Svelte 5 + TypeScript + TailwindCSS 3 + Chart.js  
**Design:** Binance-reference dark — NO gradients, NO box-shadows on surfaces  
**Nav:** Collapsible aside — 76px icon-only / 260px expanded (Material 3 style)  
**Architecture:** Modular component-first — every primitive reused across all 14 pages

---

## CRITICAL PRE-WORK: Understand What Exists

### ✅ Files that are CORRECT — do NOT touch

| File                                      | Status                                         |
| ----------------------------------------- | ---------------------------------------------- |
| `src/lib/api/client.ts`                   | Full fetch wrapper, JWT attach, auto-refresh   |
| `src/lib/api/ws.ts`                       | ReconnectingSocket with exponential backoff    |
| `src/lib/stores/auth.ts`                  | initAuth, login, logout                        |
| `src/lib/stores/toast.ts`                 | notify() — but missing `warning` type          |
| `src/lib/utils/format.ts`                 | grams, number, pct, dateTime, statusTone, etc. |
| `src/lib/utils/forms.ts`                  | Keep as-is                                     |
| `src/lib/components/layout/navigation.ts` | All 12 nav items with RBAC                     |
| `src/routes/+page.ts`                     | Redirect to /dashboard                         |
| `src/routes/+layout.ts`                   | Static adapter prerender=false                 |

### ❌ Files that are BROKEN (wrong tokens — light theme colors)

Every component uses old light-theme tokens:

- `bg-fresh` / `text-fresh` → should be `bg-primary` / `text-primary`
- `bg-coral` → `bg-down`; `text-coral` → `text-down`
- `bg-amber` → warning uses `text-primary`
- `bg-white` / `bg-panel` → `bg-card`
- `border-line` → `border-border`
- `bg-field` / `bg-slate-100` → `bg-elevated`
- `text-ink` (when dark bg) → `text-body`
- `.surface` → `.card`
- `shadow-soft` → remove entirely
- `bg-slate-50` → `bg-elevated`
- `bg-ink/30` → `bg-canvas/80` (modal overlay)

### ❌ Missing Files (must CREATE)

| File                                           | Phase |
| ---------------------------------------------- | ----- |
| `src/lib/utils/constants.ts`                   | P1    |
| `src/lib/utils/chartDefaults.ts`               | P1    |
| `src/lib/components/ui/DataTable.svelte`       | P1    |
| `src/lib/components/ui/FilterBar.svelte`       | P1    |
| `src/lib/components/ui/Pagination.svelte`      | P1    |
| `src/lib/components/ui/ConfirmDialog.svelte`   | P1    |
| `src/lib/components/ui/Tabs.svelte`            | P1    |
| `src/lib/components/ui/Toggle.svelte`          | P1    |
| `src/lib/components/ui/FormField.svelte`       | P1    |
| `src/lib/components/ui/SearchInput.svelte`     | P1    |
| `src/lib/components/ui/DateRangePicker.svelte` | P1    |
| `src/lib/components/ui/SelectField.svelte`     | P1    |
| `src/lib/components/ui/FileUpload.svelte`      | P1    |
| `src/lib/components/ui/SkeletonRow.svelte`     | P1    |
| `src/lib/components/layout/PageHeader.svelte`  | P1    |
| `src/routes/dashboard/reports/+page.svelte`    | P5    |

---

## Design Token Reference

| Tailwind Class        | Hex       | Usage                               |
| --------------------- | --------- | ----------------------------------- |
| `bg-canvas`           | `#0b0e11` | Page background — flat, NO gradient |
| `bg-card`             | `#1e2329` | Cards, panels, modals, aside nav    |
| `bg-elevated`         | `#2b3139` | Table headers, dropdowns, dividers  |
| `bg-primary`          | `#fcd535` | All CTAs, active nav, brand         |
| `bg-primary-hover`    | `#f0b90b` | Button hover                        |
| `bg-primary-disabled` | `#3a3a1f` | Disabled CTA                        |
| `text-ink`            | `#181a20` | Text ON yellow (button labels)      |
| `text-body`           | `#eaecef` | Primary text on dark                |
| `text-muted`          | `#707a8a` | Labels, secondary text              |
| `text-muted-strong`   | `#929aa5` | Strong muted                        |
| `border-border`       | `#2b3139` | All borders                         |
| `text-up`             | `#0ecb81` | Success, online, positive           |
| `text-down`           | `#f6465d` | Error, offline, negative            |
| `text-info`           | `#3b82f6` | Info badges                         |

**RULES:** NO `box-shadow` on cards/panels. NO gradient anywhere. Focus rings only.

---

## Phase Map

| Phase  | Scope                             | Key Deliverables                                   |
| ------ | --------------------------------- | -------------------------------------------------- |
| **P1** | Foundation + Design System + Auth | Token migration, all shared components, login page |
| **P2** | Dashboard + Live Monitoring       | KPI cards, charts, WebSocket feed                  |
| **P3** | Analytics + Students              | Full analytics, student list+profile               |
| **P4** | Warnings + Rule Engine            | Warning management, rule builder                   |
| **P5** | Notifications + Reports + Devices | Inbox, report generator, device health             |
| **P6** | Config + Settings + Audit         | Institution config, user management, audit log     |

---

## Phase 1 — Foundation, Design System & Auth

**Duration:** ~2-3 days  
**Depends on:** Nothing  
**Gate before P2:** `npm run check` passes; browser shows #0b0e11 canvas

### Step 1.1 — Fix `tailwind.config.ts`

Replace ALL old tokens with Binance system:

```typescript
colors: {
  canvas: '#0b0e11',
  card: '#1e2329',
  elevated: '#2b3139',
  primary: '#fcd535',
  'primary-hover': '#f0b90b',
  'primary-disabled': '#3a3a1f',
  ink: '#181a20',
  body: '#eaecef',
  muted: '#707a8a',
  'muted-strong': '#929aa5',
  border: '#2b3139',
  up: '#0ecb81',
  down: '#f6465d',
  info: '#3b82f6',
  'on-primary': '#181a20',
  'on-dark': '#ffffff',
},
borderRadius: {
  xs: '2px', sm: '4px', md: '6px', lg: '8px', xl: '12px', pill: '9999px'
},
boxShadow: {
  'ring-primary': '0 0 0 2px rgba(252,213,53,0.25)',
  'ring-up': '0 0 0 2px rgba(14,203,129,0.25)',
  'ring-down': '0 0 0 2px rgba(246,70,93,0.25)',
}
```

### Step 1.2 — Fix `src/app.css`

- Remove `color-scheme: light` → add `color-scheme: dark`
- Remove gradient body background → flat `background: #0b0e11`
- Replace `.surface` → `.card` (no shadow)
- Replace `.field` → `.input-field`
- Replace `.table-head` → `.th`, `.table-cell` → `.td`
- Replace `.icon-btn` with dark version
- Add all component utilities: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`, `.btn-sm`, `.card`, `.card-elevated`, `.input-field`, `.textarea-field`, `.select-field`, `.badge-up`, `.badge-down`, `.badge-muted`, `.badge-primary`, `.badge-info`, `.nav-item`, `.nav-item-active`, `.skeleton`, status dots

### Step 1.3 — Fix `src/app.html`

Add `<meta name="color-scheme" content="dark">` and `<meta name="theme-color" content="#0b0e11">`

### Step 1.4 — Fix `src/routes/+layout.svelte`

Add `onMount(() => applyDarkChartDefaults())` import

### Step 1.5 — Migrate Existing Components

| Component               | Key Changes                                                                                                                                                                 |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Button.svelte`         | Use `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger` + `.btn-sm`                                                                                               |
| `Card.svelte`           | `surface` → `.card` (no shadow)                                                                                                                                             |
| `StatCard.svelte`       | `bg-fresh/10 text-fresh` → `bg-up/10 text-up`; `bg-amber` → `bg-primary/10 text-primary`; `bg-coral` → `bg-down/10 text-down`; `text-ink` → `text-body`; `surface` → `card` |
| `StatusBadge.svelte`    | Same token replacement; use `.badge-up`, `.badge-down` etc.                                                                                                                 |
| `Modal.svelte`          | `bg-white` → `bg-card`; `shadow-soft` → remove; `border-line` → `border-border`; `bg-ink/35` → `bg-canvas/80`                                                               |
| `EmptyState.svelte`     | `border-dashed border-line` → `border-dashed border-border`; `bg-slate-50` → remove; `text-ink` → `text-body`                                                               |
| `ToastHost.svelte`      | `surface` → `card`; `border-fresh/30` → `border-up/30`; `border-coral/30` → `border-down/30`; `text-ink` → `text-body`                                                      |
| `ChartCard.svelte`      | Replace old palette with `['#fcd535','#0ecb81','#3b82f6','#f6465d','#707a8a','#929aa5']`; `grid.color: '#2b3139'`; ticks color `#707a8a`                                    |
| `Gauge.svelte`          | Use dark colors for SVG paths                                                                                                                                               |
| `DashboardShell.svelte` | All token replacements; nav item active → `bg-primary text-ink`; border-line→border-border; bg-white→bg-card; aside width 76px/260px                                        |

### Step 1.6 — Create New Utils

- `src/lib/utils/constants.ts` — ROLES, MEAL_TYPES, WARNING_LEVELS, STUDENT_STATUSES, PENALTY_TYPES
- `src/lib/utils/chartDefaults.ts` — applyDarkChartDefaults(), CHART_COLORS

### Step 1.7 — Create New UI Components

All use Binance tokens. No shadows on surfaces.

**`DataTable.svelte`** — Generic paginated table  
Props: `columns[]`, `rows[]`, `loading`, `page`, `total`, `pageSize`, `onRowClick?`, `onSort?`  
Slots: `cell-{key}`, `row-actions`, `empty`  
Features: skeleton rows while loading, `.th`/`.td`/`.tr-hover`, sortable headers, sticky header

**`FilterBar.svelte`** — Horizontal filter strip  
Props: `filters[]`, `values`, `onFilter`, `onReset?`  
Features: text/select/date-range types, debounced 300ms, inline reset button

**`Pagination.svelte`** — Page navigation  
Props: `page`, `total`, `pageSize`, `onChange`  
Features: "1–25 of 400" label, Prev/Next, page pills (max 7 with ellipsis)

**`ConfirmDialog.svelte`** — Danger confirmation  
Props: `open`, `title`, `message`, `confirmLabel?`, `danger?`, `onConfirm`, `onCancel`  
Renders inside `Modal.svelte`, focus trap, ESC to cancel

**`Tabs.svelte`** — Binance underline tabs  
Props: `tabs[]`, `active`, `onChange`  
Features: underline style (NOT pill), yellow underline on active, muted inactive

**`Toggle.svelte`** — Switch toggle  
Props: `value`, `onChange`, `disabled?`, `label?`  
Features: elevated track when off, primary when on, smooth CSS transition, aria-checked

**`FormField.svelte`** — Form wrapper  
Props: `label`, `error?`, `required?`, `hint?`  
Features: label above, error text in text-down, required asterisk

**`SearchInput.svelte`** — Debounced search  
Props: `value`, `placeholder?`, `onSearch`, `onClear?`  
Features: search icon left, clear ×, uses input-field class

**`DateRangePicker.svelte`** — Date range  
Props: `start`, `end`, `onChange`, `presets?`  
Features: two native date inputs, preset buttons (7d/30d/semester)

**`SelectField.svelte`** — Native select  
Props: `value`, `options[]`, `placeholder?`, `disabled?`, `onChange`  
Uses native `<select>` with select-field class

**`FileUpload.svelte`** — Drag and drop  
Props: `accept`, `maxSizeMb?`, `onSelect`, `label?`  
Features: dashed border drag zone, click to browse, size validation

**`SkeletonRow.svelte`** — Skeleton loader  
Props: `cols?`, `rows?`  
Features: animated pulse blocks matching table row layout

**`PageHeader.svelte`** — Reusable page header  
Props: `label`, `title`, `description?`  
Slot: `actions` (right side)

### Step 1.8 — Redesign Login Page

Dark two-column layout: left brand panel + right form  
API: `POST /api/v1/auth/login` → `AuthStore.login(email, password, rememberMe)`  
On success: redirect to `/dashboard` (admin) or `/dashboard/monitoring` (staff_operator)

### Step 1.9 — Fix `src/lib/stores/toast.ts`

Add `'warning'` type to Toast union

### P1 Verification Gate

- [ ] `npm run check` — zero TypeScript errors
- [ ] `npm run dev` — no console errors
- [ ] Browser: `#0b0e11` canvas — NO light bg, NO gradient
- [ ] No `box-shadow` on any card/panel
- [ ] No old tokens remain: `bg-panel`, `border-line`, `bg-field`, `bg-fresh`, `text-fresh`, `bg-coral`, `bg-amber`, `bg-slate`, `shadow-soft`, `.surface`

---

## Phase 2 — Dashboard + Live Monitoring

**Duration:** ~2-3 days  
**Depends on:** P1 complete and verified

### Pages

1. **Overview Dashboard** (`/dashboard`) — already scaffolded, needs token migration
2. **Live Monitoring** (`/dashboard/monitoring`) — already scaffolded, needs token migration

### Step 2.1 — Overview Dashboard Token Migration

File: `src/routes/dashboard/+page.svelte`

- `class="field"` select → `class="select-field"`
- `h2 ... text-ink` → `text-body`
- skeleton `animate-pulse bg-slate-100` → `skeleton`
- All component props (already uses correct API calls)

### Step 2.2 — Dashboard Layout

- Use `PageHeader` with `label="Global overview"`, `title="Institution-wide waste operations"`
- Period selector in `actions` slot

### Step 2.3 — Live Monitoring Token Migration

File: `src/routes/dashboard/monitoring/+page.svelte`  
API endpoints:

- `GET /api/v1/monitoring/current-session`
- `GET /api/v1/monitoring/recent-entries`
- `GET /api/v1/monitoring/device-statuses`
- `WS /ws/monitoring` (no `/api/v1` prefix)

Features:

- Live waste feed (scrolling list of recent entries)
- Session metrics: today's waste, active devices, alert count
- Device status grid with online/offline indicators
- WS status badge, pause/resume button

### P2 Verification Gate

- [ ] Dashboard loads KPI cards with real data
- [ ] Charts render with dark theme colors
- [ ] Monitoring page connects to WS
- [ ] Device statuses show online/offline badges

---

## Phase 3 — Analytics + Students

**Duration:** ~3 days  
**Depends on:** P2 complete

### Pages

3. **Analytics** (`/dashboard/analytics`) — already scaffolded
4. **Students List** (`/dashboard/students`) — already scaffolded
5. **Student Profile** (`/dashboard/students/[id]`) — needs creation

### Step 3.1 — Analytics Page Migration

File: `src/routes/dashboard/analytics/+page.svelte`  
Token migration + feature completion

**Tabs:**

- Tab 1: Trends (line chart — daily/weekly/monthly)
- Tab 2: Heatmap (7×24 grid from `GET /api/v1/analytics/trends?type=daily_pattern`)
- Tab 3: Top Contributors (bar chart from `GET /api/v1/analytics/top-waste-contributors`)
- Tab 4: Improvement Tracking (`GET /api/v1/analytics/improvement-tracking`)
- Tab 5: Sustainability (`GET /api/v1/analytics/sustainability` ← NOT `sustainability-scores`)

**Corrected API params:** Use `date_from` / `date_to` (NOT `start_date` / `end_date`)  
**Branch comparison:** NOT available in backend — remove or show "coming soon"

### Step 3.2 — Students List Page Migration

File: `src/routes/dashboard/students/+page.svelte`  
Token migration + correct FilterBar

**Correct filters:** `status`, `branch`, `hostel`, `year` (NO `search` or `warning_status` as server params — search is client-side only)

**Bulk actions:**

- Bulk warn → `POST /api/v1/students/bulk/warn` (NOT `/{id}/bulk-warn`)

**Quick warn modal:**

- `POST /api/v1/students/{id}/warnings` (NOT `/students/{id}/warn`)

**Student import:**

- `POST /api/v1/students/import-mapping` (CSV upload)

### Step 3.3 — Student Profile Page

File: `src/routes/dashboard/students/[id]/+page.svelte`

API calls:

- `GET /api/v1/students/{id}`
- `GET /api/v1/students/{id}/stats`
- `GET /api/v1/students/{id}/timeline`
- `GET /api/v1/students/{id}/food-breakdown`
- `GET /api/v1/students/{id}/warnings`
- `GET /api/v1/students/{id}/improvement`

Features: profile header, sustainability score gauge, waste history chart, warning timeline, food breakdown doughnut

### P3 Verification Gate

- [ ] Analytics tabs all load real data
- [ ] Heatmap renders from daily_pattern API
- [ ] Students list filters work with correct params
- [ ] Student profile loads all sections

---

## Phase 4 — Warnings + Rule Engine

**Duration:** ~3 days  
**Depends on:** P3 complete

### Pages

6. **Warnings & Penalties** (`/dashboard/warnings`) — already scaffolded
7. **Rule Engine** (`/dashboard/rules`) — already scaffolded

### Step 4.1 — Warnings Page Migration

File: `src/routes/dashboard/warnings/+page.svelte`

**CRITICAL API corrections:**

- No `GET /api/v1/warnings/{id}` — detail modal uses row data (prop)
- Create manual warning → `POST /api/v1/students/{student_id}/warnings` (NOT `/warnings`)
- Create direct penalty → `POST /api/v1/students/{student_id}/penalties` (NOT `/warnings/penalties`)
- Resolve → `PATCH /api/v1/warnings/{id}/resolve`
- Bulk resolve → `POST /api/v1/warnings/bulk-resolve`
- Export → `GET /api/v1/warnings/export`

**Tabs:** Active Warnings | Resolved | Penalties | Escalations

### Step 4.2 — Rule Engine Page Migration

File: `src/routes/dashboard/rules/+page.svelte`

API calls:

- `GET /api/v1/rules` (list)
- `POST /api/v1/rules` (create)
- `PATCH /api/v1/rules/{id}`
- `DELETE /api/v1/rules/{id}`
- `POST /api/v1/rules/{id}/toggle` with `{"active": true/false}`
- `POST /api/v1/rules/{id}/test`
- `POST /api/v1/rules/{id}/simulate?date_from={}&date_to={}` (query params, NOT body)
- `GET /api/v1/rules/{id}/executions`
- `GET /api/v1/rules/chains`
- `GET /api/v1/rules/metadata/conditions`
- `GET /api/v1/rules/metadata/actions`

Features: Rule list with toggle, rule builder modal (conditions + actions), test panel, simulation panel, execution history tab

### P4 Verification Gate

- [ ] Warnings list shows with correct status badges
- [ ] Create warning modal submits to `/students/{id}/warnings`
- [ ] Resolve/escalate actions work
- [ ] Rules can be toggled on/off
- [ ] Rule builder modal opens and submits correctly

---

## Phase 5 — Notifications + Reports + Devices

**Duration:** ~3 days  
**Depends on:** P4 complete

### Pages

8. **Notifications** (`/dashboard/notifications`) — already scaffolded
9. **Reports** (`/dashboard/reports`) — DOES NOT EXIST, must create
10. **Devices** (`/dashboard/devices`) — already scaffolded

### Step 5.1 — Notifications Page Migration

File: `src/routes/dashboard/notifications/+page.svelte`

API calls:

- `GET /api/v1/notifications` (paginated, filters: type, channel, status, is_read)
- `PATCH /api/v1/notifications/{id}` (mark read)
- `POST /api/v1/notifications/mark-all-read`
- `GET /api/v1/notifications/preferences`
- `PUT /api/v1/notifications/preferences`

Features: notification inbox list, unread badge count, mark-all-read button, preferences panel (toggle channels per type)

### Step 5.2 — Reports Page (CREATE)

File: `src/routes/dashboard/reports/+page.svelte` (MISSING — must create)

API calls:

- `GET /api/v1/reports` (list past reports)
- `POST /api/v1/reports/generate` (queue new report)
- `GET /api/v1/reports/{id}` (status polling)
- `GET /api/v1/reports/{id}/download` (trigger download)
- `GET /api/v1/reports/schedules`

Features:

- Report history table with status (pending/completed/failed)
- Generate Report modal: type selector (overview/students/warnings/devices), format (pdf/xlsx/csv), date range
- Download button for completed reports
- Schedule list (recurring reports)

### Step 5.3 — Devices Page Migration

File: `src/routes/dashboard/devices/+page.svelte`

API calls:

- `GET /api/v1/devices` (paginated)
- `GET /api/v1/devices/{id}`
- `GET /api/v1/devices/{id}/health`
- `GET /api/v1/devices/{id}/history`
- `PATCH /api/v1/devices/{id}`

Features:

- Device grid/list with online/offline status
- Device detail modal: health metrics (CPU%, RAM%, temp), last heartbeat, firmware
- Device history timeline

### P5 Verification Gate

- [ ] Notifications inbox loads and mark-read works
- [ ] Reports page exists and report generation queues
- [ ] Download triggers file save
- [ ] Devices list shows with correct status indicators

---

## Phase 6 — Config + Settings + Audit

**Duration:** ~2-3 days  
**Depends on:** P5 complete

### Pages

11. **Configuration** (`/dashboard/config`) — already scaffolded
12. **Settings** (`/dashboard/settings`) — already scaffolded
13. **Audit Log** (`/dashboard/audit`) — already scaffolded

### Step 6.1 — Configuration Page Migration

File: `src/routes/dashboard/config/+page.svelte`

API calls (all fetched in `Promise.all()`):

- `GET /api/v1/config/institution`
- `GET /api/v1/config/thresholds`
- `GET /api/v1/config/meals`
- `GET /api/v1/config/branches`
- `PUT /api/v1/config/{section}` (save per tab)
- `POST /api/v1/config/reset/{section}` ← CORRECT order (NOT `/{section}/reset`)

**Tabs:** Institution | Thresholds | Meal Schedule | Branches

### Step 6.2 — Settings Page Migration

File: `src/routes/dashboard/settings/+page.svelte`

API calls:

- `GET /api/v1/settings/users` / `POST` / `PATCH /settings/users/{id}` / `POST /settings/users/{id}/deactivate` (NOT delete)
- `GET /api/v1/settings/security` / `PUT`
- `GET /api/v1/settings/backups` / `POST /settings/backups/trigger` / `POST /settings/backups/restore` (file upload, field: `backup_file`)
- `GET /api/v1/settings/maintenance/system-info` (NOT `/settings/system-info`)
- `POST /api/v1/settings/maintenance/clear-cache`
- `POST /api/v1/settings/maintenance/optimize-db` (NOT `/settings/optimize`)
- `POST /api/v1/settings/appearance/logo` (logo upload)
- `GET /api/v1/roles`

Store actions: `fetchUsers()`, `createUser()`, `updateUser()`, `deactivateUser()` (NOT `deleteUser`)

**Tabs:** Users | Security | Backups | Maintenance | Appearance

### Step 6.3 — Audit Log Page Migration

File: `src/routes/dashboard/audit/+page.svelte`

API calls:

- `GET /api/v1/audit` (paginated, filters: action, resource_type, date_from, date_to, user_id)
- `GET /api/v1/audit/{id}` (detail)
- `GET /api/v1/audit/stats`

Features: audit table with timestamp, actor, action, resource; detail drawer showing full payload; stats cards (top actions, top actors)

### P6 Verification Gate

- [ ] Config tabs save and reset correctly
- [ ] Config reset uses `POST /config/reset/{section}` (correct order)
- [ ] User deactivate (not delete) works
- [ ] System info loads from `/settings/maintenance/system-info`
- [ ] Optimize DB calls `/settings/maintenance/optimize-db`
- [ ] Audit log paginates and filters correctly

---

## Execution Rules

1. **Each phase must pass `npm run check` before starting the next**
2. **Never use:** `box-shadow`, gradients, `bg-white`, `border-line`, `bg-fresh`, `bg-coral`, `bg-amber`, `.surface`
3. **Always use Svelte 4 event syntax** (`on:click`) — codebase uses Svelte 4 events consistently
4. **API correctness:** All endpoints verified against live backend — follow this plan, not the 00-master-index
5. **Component reuse:** Import shared components — never duplicate inline styles
6. **Search before editing:** Always check if a token is used elsewhere in the file before replacing

---

## Token Quick-Reference Migration Map

| Old (wrong)                               | New (correct)                       |
| ----------------------------------------- | ----------------------------------- |
| `bg-fresh`                                | `bg-primary`                        |
| `text-fresh`                              | `text-primary`                      |
| `bg-coral`                                | `bg-down`                           |
| `text-coral`                              | `text-down`                         |
| `bg-amber`                                | `bg-primary/10` (warn context)      |
| `text-amber`                              | `text-primary` (warn context)       |
| `bg-white`                                | `bg-card`                           |
| `bg-panel`                                | `bg-card`                           |
| `border-line`                             | `border-border`                     |
| `bg-field`                                | `bg-elevated`                       |
| `bg-slate-100`, `bg-slate-50`             | `bg-elevated`                       |
| `text-ink` (body text on dark)            | `text-body`                         |
| `text-ink` (text ON yellow)               | `text-ink` (keep!)                  |
| `.surface`                                | `.card`                             |
| `shadow-soft`                             | _(remove)_                          |
| `bg-ink/30` (overlay)                     | `bg-canvas/80`                      |
| `ring-fresh`                              | `ring-primary`                      |
| `border-t-fresh` (spinner)                | `border-t-primary`                  |
| `bg-fresh text-white` (nav active)        | `bg-primary text-ink`               |
| `hover:bg-slate-100 hover:text-ink` (nav) | `hover:bg-elevated hover:text-body` |
