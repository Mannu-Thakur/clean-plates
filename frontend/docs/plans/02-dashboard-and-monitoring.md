# Phase 2 — Overview Dashboard & Live Monitoring

**Duration:** ~4 days  
**Depends on:** Phase 1 (all design tokens, shared components, auth shell)  
**Required before:** Phase 3 (reuses StatCard, ChartCard, Gauge, WS patterns)  
**Pages implemented:**

- Page 02: `/dashboard` — Global Overview Dashboard
- Page 03: `/dashboard/monitoring` — Live Monitoring Dashboard

---

## Context & Current State

Both pages have existing implementations that work functionally but use the old light theme tokens. This phase:

1. Migrates both pages to dark Binance theme (token swap)
2. Completes any missing features per the page specs
3. Adds the new `PageHeader.svelte` layout component
4. Adds missing chart types and real-time behaviour

---

## Page 02 — Global Overview Dashboard (`/dashboard`)

### Route: `src/routes/dashboard/+page.svelte`

**Access:** super_admin, institution_admin, mess_admin, analytics_viewer  
**API Endpoints Used:**

| Call               | Endpoint                                                            | Trigger                |
| ------------------ | ------------------------------------------------------------------- | ---------------------- |
| Overview KPIs      | `GET /api/v1/analytics/overview?period={p}`                         | onMount, period change |
| Weekly Trend       | `GET /api/v1/analytics/trends?type=weekly&period={p}`               | onMount, period change |
| Monthly Comparison | `GET /api/v1/analytics/trends?type=monthly_comparison&period={p}`   | onMount                |
| Meal Distribution  | `GET /api/v1/analytics/meal-distribution?period={p}`                | onMount                |
| Food Waste Ranking | `GET /api/v1/analytics/food-waste-distribution?period={p}&limit=10` | onMount                |
| Peak Times         | `GET /api/v1/analytics/peaks?period={p}`                            | onMount                |
| Report Export      | `POST /api/v1/reports/generate`                                     | User action            |
| WS Dashboard       | `WS /ws/dashboard`                                                  | onMount                |

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  PageHeader: "Global Overview"                [Period] [↻] [↓]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                           │
│  │KPI1│ │KPI2│ │KPI3│ │KPI4│ │KPI5│    ← Row 1: Waste KPIs    │
│  └────┘ └────┘ └────┘ └────┘ └────┘                           │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                           │
│  │KPI6│ │KPI7│ │KPI8│ │KPI9│ │K10 │    ← Row 2: Ops KPIs      │
│  └────┘ └────┘ └────┘ └────┘ └────┘                           │
├───────────────────────────┬─────────────────────────────────────┤
│  Line: Weekly Trend       │  Bar: Monthly Comparison            │
├───────────────────────────┼─────────────────────────────────────┤
│  Doughnut: Meal Dist.     │  H-Bar: Top Wasted Foods            │
└───────────────────────────┴─────────────────────────────────────┘
```

### KPI Cards (10 total) — `StatCard.svelte`

| #   | Title            | Field from API                           | Tone                  | Icon          |
| --- | ---------------- | ---------------------------------------- | --------------------- | ------------- |
| 1   | Waste Today      | `total_waste_today_grams` → `grams()`    | neutral               | Scale         |
| 2   | Waste This Week  | `total_waste_week_grams`                 | neutral               | Calendar      |
| 3   | Waste This Month | `total_waste_month_grams`                | neutral               | TrendingDown  |
| 4   | Reduction %      | `waste_reduction_pct`                    | good if ≥0, bad if <0 | TrendingDown  |
| 5   | Peak Time        | `peak_waste_time` or computed            | neutral               | Clock         |
| 6   | Active Students  | `total_active_students`                  | neutral               | Users         |
| 7   | Under Warning    | `students_under_warning`                 | warn (primary)        | AlertTriangle |
| 8   | Under Penalty    | `students_under_penalty`                 | bad (down)            | Ban           |
| 9   | Active Devices   | `active_devices` / `offline_devices`     | neutral               | Cpu           |
| 10  | Alerts Today     | `alerts_today` / `rule_violations_today` | hot (primary)         | Bell          |

**Tone mapping for dark theme:**

- `good` → value label `text-up`
- `bad` → value label `text-down`
- `warn` → value label `text-primary` (yellow)
- `hot` → value label `text-primary`
- `neutral` → value label `text-body`

### StatCard dark redesign

The `StatCard.svelte` renders within `.card p-5`:

- Icon in top-right: 40×40 `rounded-lg bg-elevated flex items-center justify-center text-muted`
- Value: `text-3xl font-bold font-mono` (BinancePlex style numeric)
- Title: `text-sm font-medium text-muted`
- Helper: `text-xs text-muted mt-0.5`
- Trend indicator (optional): `badge-up` or `badge-down` with ▲▼ prefix

### Chart.js Dark Configuration

All charts within `ChartCard.svelte` must use:

- Background: `transparent` (card provides background)
- Grid lines: `#2b3139`
- Tick color: `#707a8a`
- Legend: `#eaecef`
- Primary dataset fill: `rgba(252,213,53,0.08)` for line chart area
- Line color: `#fcd535`
- Bar colors: use `CHART_COLORS.series`
- Doughnut colors: `['#fcd535','#0ecb81','#3b82f6']` for meals

### ChartCard.svelte Enhancement

Add `expandable` prop:

- Shows `btn-icon` Expand button in card header
- On click: opens chart in a `Modal.svelte` at larger size
- Chart re-renders at `height: 400px` inside modal

### Period Selector

Dropdown `select-field` with options:

- `today` → "Today"
- `7d` → "Last 7 days"
- `30d` → "Last 30 days"
- `semester` → "This semester"

On change: re-fetch all API calls with new period. Show skeleton during load.

### WebSocket Integration (WS `/ws/dashboard`)

```typescript
// In +page.svelte onMount:
socket = new ReconnectingSocket('/dashboard', (msg) => {
  if (
    ['waste_entry', 'warning_issued', 'rule_executed', 'kpi_update'].includes(
      msg.type
    )
  ) {
    loadOverview(); // refetch all KPIs
  }
});
socket.connect();

// Connection status badge: wsStatus -> StatusBadge
// 'connected' → badge-up   'reconnecting' → badge-muted   'closed' → badge-down
```

### Export Button

`btn-secondary` "Export" with Download icon:

- Calls `POST /api/v1/reports/generate` with `{ type: 'overview', format: 'pdf', filters: { period } }`
- Shows `notify('Report generation queued', 'success')`
- Does NOT download immediately (report is queued — user gets it via Reports page)

---

## Page 03 — Live Monitoring Dashboard (`/dashboard/monitoring`)

### Route: `src/routes/dashboard/monitoring/+page.svelte`

**Access:** All roles (staff_operator: limited — no acknowledge button shown)  
**API Endpoints Used:**

| Call              | Endpoint                                          | Trigger              |
| ----------------- | ------------------------------------------------- | -------------------- |
| Current Session   | `GET /api/v1/monitoring/current-session`          | onMount              |
| Recent Entries    | `GET /api/v1/monitoring/recent-entries?limit=50`  | onMount              |
| Device Statuses   | `GET /api/v1/monitoring/device-statuses`          | onMount + WS updates |
| Acknowledge Alert | `POST /api/v1/monitoring/alerts/{id}/acknowledge` | User action          |
| Entry Detail      | `GET /api/v1/waste/entries/{id}`                  | User clicks entry    |
| Device Health     | `GET /api/v1/devices/{id}/health`                 | User clicks device   |
| WS Monitoring     | `WS /ws/monitoring`                               | onMount              |

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  PageHeader: "Live Monitoring"        [⏸ Pause] [🔔 Sound] [⛶] │
├──────────────────────────────────────────────────────────────────┤
│  Live Bar: [Entries Today: 47]  [Active Session: Lunch]  [Rate] │
├──────────────────┬─────────────────┬────────────────────────────┤
│  Real-Time Feed  │  Active Session │  Device Status Grid        │
│  (scrolling)     │  (meal info)    │  (grid of device cards)    │
│                  │                 │                            │
├──────────────────┼─────────────────┴────────────────────────────┤
│  Alert Feed      │  Live Waste Gauge │  Session Timeline        │
└──────────────────┴───────────────────┴──────────────────────────┘
```

### Real-Time Feed Panel

- Left column, full height, scrollable `overflow-y-auto`
- Pause/Resume button at top: when paused, incoming entries queue in memory (not shown), resume flushes queue
- Filter by meal: `select-field` (All / Breakfast / Lunch / Dinner) — client-side filter on received entries
- Feed item card (WasteEntryCard):
  - `card p-3 mb-2 cursor-pointer tr-hover`
  - Student name (`text-body text-sm font-semibold`) + roll number (`text-muted text-xs`)
  - Weight in `text-primary font-mono` + meal badge
  - Food items as small `badge-muted` pills
  - Severity color: weight < 100g → `dot-up`, 100-200g → `dot-warn`, >200g → `dot-down` left border
  - Time: `text-muted text-xs` (relative, e.g. "2m ago")
  - On click: open `Modal.svelte` with full entry details including plate image from `/static/uploads/`

### Active Session Panel

- Center column
- Current meal: large `text-primary text-2xl font-bold` (LUNCH / BREAKFAST / DINNER)
- Time window: `text-muted text-sm`
- Entry count: `text-body text-3xl font-bold font-mono`
- Avg waste this session: computed client-side from feed
- "No active session" empty state when between meals

### Device Status Grid

- Right column, grid 2×N cards
- Each device: `.card p-3`
  - Device name: `text-body text-sm font-semibold`
  - Mess label: `text-muted text-xs`
  - Status dot + label: `dot-up` online / `dot-down` offline / `dot-warn` warning
  - Last seen: `text-muted text-xs`
  - CPU / RAM bars: thin `bg-elevated` track, `bg-primary` fill (via inline style %)
  - On click: opens Modal with full health from `GET /api/v1/devices/{id}/health`
    - CPU history: small line chart
    - RAM, disk, temp: gauge bars
    - Last heartbeat, uptime

### Alert Feed Panel

- Bottom-left
- New alerts prepend to top (newest first)
- Alert card: `card p-3 mb-2`
  - Priority badge: critical→`badge-down`, high→`badge-primary`, medium→`badge-info`, low→`badge-muted`
  - Message: `text-body text-sm`
  - Rule name: `text-muted text-xs`
  - Time: `text-muted text-xs`
  - Acknowledge button (hidden for staff_operator role): `btn-sm btn-secondary` → calls acknowledge API
  - Acknowledged: greys out (opacity-50), shows "✓ Acknowledged" label
- Unacknowledged count badge in panel header

### Live Waste Gauge (`Gauge.svelte`)

- Center-bottom
- SVG arc gauge: 0 to max (e.g. 500g/min)
- Current rate computed from last 5 entries' average weight / time span
- Color: <100 → `up`, 100–200 → primary, >200 → `down`
- Label: "g/min" in `text-muted`
- Value: `text-3xl font-mono` in color

### Session Timeline

- Right-bottom
- Horizontal timeline of today's meal sessions
- Past sessions: filled bar in `bg-primary/30`, current: `bg-primary`, future: `bg-elevated`
- Labels: Breakfast 7–9:30, Lunch 12–14:30, Dinner 19–21:30
- Entry count bubble above each bar

### WebSocket Integration (WS `/ws/monitoring`)

```typescript
socket = new ReconnectingSocket('/monitoring', (msg) => {
  switch (msg.type) {
    case 'waste_entry':
      if (!paused) addToFeed(msg.data);
      else pendingQueue.push(msg.data);
      updateGauge(msg.data);
      break;
    case 'alert':
      addAlert(msg.data);
      if (soundEnabled) playAlertSound();
      break;
    case 'device_status':
      updateDeviceCard(msg.data.device_id, msg.data);
      break;
    case 'session_change':
      currentSession = msg.data;
      break;
  }
});
```

### Connection Status Bar

- Top of page, below PageHeader
- `bg-elevated/50 rounded-md px-4 py-2 flex items-center gap-3`
- WS status dot + label + reconnect attempt count
- Shows "Reconnecting..." with animated pulse when disconnected

### Fullscreen Mode

- `btn-icon` button: requests `document.documentElement.requestFullscreen()`
- On fullscreen: hide page header and nav (Svelte store flag `isFullscreen`)
- `DashboardShell` checks this store and adds `fullscreen:hidden` to aside/header

---

## New API Type Definitions (add to `src/lib/api/types.ts`)

```typescript
// From GET /api/v1/monitoring/current-session
export interface MealSession {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | null;
  start_time: string;
  end_time: string;
  entry_count: number;
  is_active: boolean;
}

// From WS monitoring: waste_entry event
export interface LiveWasteEntry {
  id: string;
  student_name: string;
  student_roll_number?: string;
  weight_grams: number;
  meal_type: string;
  food_items: string[];
  severity: 'low' | 'medium' | 'high';
  plate_image_path?: string;
  timestamp: string;
  device_id: string;
}

// From GET /api/v1/monitoring/device-statuses
export interface DeviceStatus {
  id: string;
  name: string;
  mess_name?: string;
  status: 'online' | 'offline' | 'warning' | 'decommissioned';
  cpu_percent?: number;
  ram_percent?: number;
  temperature?: number;
  last_heartbeat?: string;
  ip_address?: string;
}

// From GET /api/v1/analytics/overview
export interface KpiOverview {
  total_waste_today_grams: number;
  total_waste_week_grams: number;
  total_waste_month_grams: number;
  avg_daily_waste_grams: number;
  waste_reduction_pct: number | null;
  peak_waste_time: string | null;
  total_active_students: number;
  students_under_warning: number;
  students_under_penalty: number;
  active_devices: number;
  offline_devices: number;
  alerts_today: number;
  rule_violations_today: number;
}
```

---

## Verification Checklist

- [ ] Overview dashboard renders on dark canvas with all 10 KPI cards
- [ ] All KPI values populate from real API (`/analytics/overview`)
- [ ] Period selector changes trigger re-fetch of all charts and KPIs
- [ ] Weekly trend line chart renders (dark grid, yellow line)
- [ ] Monthly comparison bar chart renders with two series
- [ ] Meal distribution doughnut renders with 3 segments
- [ ] Food waste horizontal bar chart renders top 10
- [ ] Export button queues report and shows success toast
- [ ] WS connects to `/ws/dashboard` — status badge shows "connected"
- [ ] WS message triggers KPI re-fetch
- [ ] Live monitoring: real-time feed adds entries from WS
- [ ] Feed pause/resume works
- [ ] Meal filter filters feed client-side
- [ ] Device status cards show correct online/offline state
- [ ] Alert feed shows incoming alerts with correct priority badges
- [ ] Alert acknowledge sends API call and greys out alert
- [ ] Live waste gauge animates on new entries
- [ ] Entry click opens modal with full details
- [ ] Device click opens modal with health stats
- [ ] Fullscreen mode works
- [ ] Auto-reconnect shows "Reconnecting..." banner

---

## Exit Criteria

✅ Both pages render correctly on dark Binance theme  
✅ All API calls wired and data displayed  
✅ WebSocket live updates working on both pages  
✅ No light-theme tokens remain in these pages  
✅ `npm run check` still passing
