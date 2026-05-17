# Phase 5 — Notifications, Reports & Devices

**Duration:** ~5 days  
**Depends on:** Phase 1 (Modal, DataTable, FilterBar, FileUpload), Phase 3 (filter/pagination patterns), Phase 4 (ConfirmDialog)  
**Required before:** Phase 6 (Modal and form patterns complete)  
**Pages implemented:**
- Page 09: `/dashboard/notifications` — Notification Centre
- Page 10: `/dashboard/reports` — Reports & Scheduled Reports
- Page 11: `/dashboard/devices` — Device Management

---

## Page 09 — Notification Centre (`/dashboard/notifications`)

### Route: `src/routes/dashboard/notifications/+page.svelte`
**Access:** All roles (notifications scoped to their own role)

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  PageHeader: "Notifications"   [Mark All Read] [Preferences] [🔔]│
├──────────────────────────────────────────────────────────────────┤
│  Stats: [Unread] [Total Today] [Alerts] [System Messages]        │
├──────────────────────────────────────────────────────────────────┤
│  FilterBar: [Type▼] [Priority▼] [Status▼] [Date Range]          │
├──────────────────────────────────────────────────────────────────┤
│  Notification list (card-based, NOT table)                       │
│  + Pagination                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### API Calls

| Action | Endpoint |
|--------|----------|
| List notifications | `GET /api/v1/notifications?page=&size=&type=&priority=&is_read=&start_date=&end_date=` |
| Mark as read | `PATCH /api/v1/notifications/{id}` with `{is_read: true}` |
| Mark all read | `POST /api/v1/notifications/mark-all-read` |
| Delete notification | `DELETE /api/v1/notifications/{id}` |
| Get preferences | `GET /api/v1/notifications/preferences` |
| Update preferences | `PATCH /api/v1/notifications/preferences` |
| Create notification | `POST /api/v1/notifications` (admin only) |
| Schedule notification | `POST /api/v1/notifications/schedule` |

### Notification Card Design

Each notification renders as a `.card p-4 mb-2` with:
- Left accent bar (4px wide) colored by priority:
  - `critical` → `bg-down`
  - `high` → `bg-primary`
  - `medium` → `bg-info`
  - `low` → `bg-muted`
- Unread state: slightly brighter background (`bg-card` → `bg-elevated/30` glow)
- Read state: normal opacity
- Type icon (Bell, AlertTriangle, Info, CheckCircle) in `text-muted`
- Title: `text-sm font-semibold text-body`
- Message: `text-sm text-muted` (max 2 lines, expandable)
- Time: `text-xs text-muted` (relative: "3m ago", "Yesterday")
- Priority badge: right-aligned
- Action buttons (on hover):
  - ✓ Mark Read / ↩ Mark Unread
  - 🗑 Delete
  - ↗ Navigate (if linked to student/rule/warning — navigate to related resource)

### Stat Row

| Card | Value | Tone |
|------|-------|------|
| Unread | count | primary |
| Total Today | count | neutral |
| Alerts (critical+high) | count | bad |
| System Messages | count | info |

### Preferences Modal

Opens on "Preferences" button click.

```
Notification Preferences:
  ┌──────────────────────────────────┐
  │  Email Notifications             │
  │  ─────────────────────────────   │
  │  Warning issued         [Toggle] │
  │  Penalty created        [Toggle] │
  │  Device offline         [Toggle] │
  │  Daily digest           [Toggle] │
  │  Weekly report          [Toggle] │
  │                                  │
  │  In-App Notifications            │
  │  ─────────────────────────────   │
  │  All alerts             [Toggle] │
  │  Rule executions        [Toggle] │
  │  System updates         [Toggle] │
  │                                  │
  │  [Cancel]  [Save Preferences]   │
  └──────────────────────────────────┘
```

PATCH → `PATCH /api/v1/notifications/preferences` with preference JSON

### Create Notification Modal (admin only)

- Target: All Users / Role / Specific User
- Title + Message
- Priority (low/medium/high/critical)
- Type (info/alert/warning/success)
- Schedule: Send Now / Schedule for later → shows datetime picker
- Submit → `POST /api/v1/notifications` or `POST /api/v1/notifications/schedule`

### Real-Time Notification Badge (global)

- In `DashboardShell.svelte`, add Bell icon in header
- Shows unread count as badge (red circle, white number)
- Fetched on init: `GET /api/v1/notifications?is_read=false&size=5`
- WS dashboard events of type `notification` update this count
- Click → navigate to `/dashboard/notifications`

### API Types

```typescript
export interface Notification {
  id: string;
  type: 'info' | 'alert' | 'warning' | 'success' | 'system';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  is_read: boolean;
  target_user_id?: string;
  target_role?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  scheduled_at?: string;
  sent_at?: string;
  created_at: string;
}
export interface NotificationPreferences {
  email_on_warning: boolean;
  email_on_penalty: boolean;
  email_on_device_offline: boolean;
  email_daily_digest: boolean;
  email_weekly_report: boolean;
  inapp_all_alerts: boolean;
  inapp_rule_executions: boolean;
  inapp_system_updates: boolean;
}
```

---

## Page 10 — Reports (`/dashboard/reports`)

### Route: `src/routes/dashboard/reports/+page.svelte`
**Access:** super_admin, institution_admin, mess_admin

### Layout

```
┌───────────────────────────────────────────────────────────┐
│  PageHeader: "Reports"              [Generate Report]     │
├───────────────────────────────────────────────────────────┤
│  [Reports Library] [Scheduled Reports]  ← Tabs            │
├───────────────────────────────────────────────────────────┤
│  FilterBar + DataTable + Pagination                        │
└───────────────────────────────────────────────────────────┘
```

### API Calls

| Action | Endpoint |
|--------|----------|
| List reports | `GET /api/v1/reports?page=&size=&type=&format=&status=&start_date=&end_date=` |
| Generate report | `POST /api/v1/reports/generate` |
| Get report | `GET /api/v1/reports/{id}` |
| Download report | `GET /api/v1/reports/{id}/download` → `api.download()` |
| Delete report | `DELETE /api/v1/reports/{id}` |
| List schedules | `GET /api/v1/reports/schedules` |
| Create schedule | `POST /api/v1/reports/schedules` |
| Update schedule | `PATCH /api/v1/reports/schedules/{id}` |
| Delete schedule | `DELETE /api/v1/reports/schedules/{id}` |

### Tab 1: Reports Library

**FilterBar:** Date range, Type (daily/weekly/custom/overview), Format (pdf/csv/excel), Status (pending/generating/ready/failed)

**DataTable Columns:**

| Column | Field | Sortable |
|--------|-------|----------|
| Name | `name` | No |
| Type | `type` badge | Yes |
| Format | `format` badge | No |
| Status | `status` badge | Yes |
| Generated By | `generated_by_name` | No |
| Date Range | `period_start` – `period_end` | Yes |
| Generated At | `generated_at` | Yes |
| Size | file size | No |
| Actions | — | No |

**Status Badge:**
- `pending` → `badge-muted` with ⏳
- `generating` → `badge-info` with spinner animation
- `ready` → `badge-up` with ✓
- `failed` → `badge-down` with ✕

**Row Actions:**
- ⬇ Download (only if status=ready) → `api.download('/reports/{id}/download', filename)`
- 👁 Preview → `GET /api/v1/reports/{id}` → shows metadata in modal (NOT inline PDF rendering)
- 🗑 Delete → `ConfirmDialog` then DELETE

**Polling for generating reports:**
- If any report has status=`generating`, poll `GET /api/v1/reports/{id}` every 5s
- On status change to `ready`: update row, show `notify('Report ready!', 'success')` with download action in toast
- Stop polling when all are ready/failed

### Generate Report Modal

```
┌────────────────────────────────────┐
│  Generate Report                   │
├────────────────────────────────────┤
│  Report Name: [input-field]        │
│  Type: [overview▼ / daily / weekly │
│          / custom / branch]        │
│  Format: [pdf▼] [csv] [excel]      │
│  Date Range: [start] → [end]       │
│  Filters:                          │
│    Branch: [ALL▼]                  │
│    Meal: [ALL▼]                    │
│  Options:                          │
│    Include charts: [Toggle]        │
│    Include student details:[Toggle]│
│  [Cancel]  [Generate]              │
└────────────────────────────────────┘
```

Submit → `POST /api/v1/reports/generate`
- Response: report object with status=`pending` or `generating`
- Add to table immediately, start polling

### Tab 2: Scheduled Reports

**DataTable Columns:** Name, Type, Format, Frequency, Next Run, Last Run, Created By, Actions

**Frequency Badge:**
- `daily` → `badge-info`
- `weekly` → `badge-primary`
- `monthly` → `badge-muted`

**Schedule Upsert Modal:**

```
┌────────────────────────────────────┐
│  Schedule Report                   │
├────────────────────────────────────┤
│  Report Name: [input-field]        │
│  Type: [SelectField]               │
│  Format: [SelectField]             │
│  Frequency: [daily▼/weekly/monthly]│
│  Time of Day: [time input]         │
│  Day of Week (if weekly):          │
│    [Mon] [Tue] [Wed] ... toggles   │
│  Recipients (emails):              │
│  [email1], [email2] ...            │
│  [Cancel]  [Save Schedule]         │
└────────────────────────────────────┘
```

Submit → `POST /api/v1/reports/schedules` or `PATCH .../schedules/{id}`

### API Types

```typescript
export interface Report {
  id: string;
  name: string;
  type: 'daily' | 'weekly' | 'custom' | 'overview' | 'branch';
  format: 'pdf' | 'csv' | 'excel';
  status: 'pending' | 'generating' | 'ready' | 'failed';
  file_path?: string;
  file_size?: number;
  generated_by: string;
  generated_by_name?: string;
  period_start?: string;
  period_end?: string;
  filters?: Record<string, unknown>;
  generated_at?: string;
  error_message?: string;
  created_at: string;
}
export interface ReportSchedule {
  id: string;
  name: string;
  type: string;
  format: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time_of_day: string;
  day_of_week?: number;
  recipients?: string[];
  next_run?: string;
  last_run?: string;
  created_by: string;
  created_at: string;
}
```

---

## Page 11 — Device Management (`/dashboard/devices`)

### Route: `src/routes/dashboard/devices/+page.svelte`
**Access:** super_admin, institution_admin, mess_admin

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  PageHeader: "Devices"              [Register Device] [↻]   │
├─────────────────────────────────────────────────────────────┤
│  Stat row: [Online] [Offline] [Warning] [Total]             │
├─────────────────────────────────────────────────────────────┤
│  FilterBar: [Search] [Status▼] [Mess▼]                      │
├─────────────────────────────────────────────────────────────┤
│  Device Grid (card view) OR [Toggle to Table view]          │
└─────────────────────────────────────────────────────────────┘
```

### API Calls

| Action | Endpoint |
|--------|----------|
| List devices | `GET /api/v1/devices?page=&size=&status=&search=` |
| Get device | `GET /api/v1/devices/{id}` |
| Register device | `POST /api/v1/devices` |
| Update device | `PATCH /api/v1/devices/{id}` |
| Decommission | `DELETE /api/v1/devices/{id}` |
| Device health | `GET /api/v1/devices/{id}/health` |
| Device history | `GET /api/v1/devices/{id}/history?page=&size=` |
| Restart service | `POST /api/v1/devices/{id}/restart` |

### Stat Row

| Card | Value | Tone |
|------|-------|------|
| Online | count | good (up) |
| Offline | count | bad (down) |
| Warning | count | warn (primary) |
| Total | count | neutral |

### Device Card View

Default view: responsive grid (2–4 cols based on screen width)

Each device card (`.card p-5`):
```
┌───────────────────────────────┐
│  ● Online    [Edit] [⟳] [⋮]  │  ← status dot + action icons
├───────────────────────────────┤
│  🖥 DEVICE NAME               │
│  Mess: Main Block             │
│  Last seen: 2m ago            │
├───────────────────────────────┤
│  CPU  ████████░░ 82%          │  ← progress bar
│  RAM  ████░░░░░░ 45%          │
│  Temp 🌡 62°C                 │
├───────────────────────────────┤
│  IP: 192.168.1.45             │
│  API Key: ••••••7a3f          │
│  [View Health] [History]      │
└───────────────────────────────┘
```

Status color:
- `online` → `dot-up` + `badge-up`
- `offline` → `dot-down` + `badge-down`
- `warning` → `dot-warn` + `badge-primary`
- `decommissioned` → `dot-muted` + `badge-muted`

Progress bars: `bg-elevated rounded-full overflow-hidden h-1.5`, fill `bg-primary` (CPU), `bg-info` (RAM), `bg-down` if >90%

**Table View Toggle:** Icon button in page header switches between card grid and DataTable layout

### DataTable View (columns)

| Column | Field |
|--------|-------|
| Name | `name` |
| Mess | `mess_name` |
| Status | badge |
| CPU% | progress bar |
| RAM% | progress bar |
| Temp | `temperature`°C |
| IP | `ip_address` |
| Last Seen | `last_heartbeat` |
| Actions | — |

### Device Health Modal

Opened via "View Health" button:

```
┌────────────────────────────────────────────┐
│  Device: MAIN-BLOCK-01         ● Online    │
├────────────────────────────────────────────┤
│  CPU Usage (last 1h) → small line chart   │
│  RAM Usage (last 1h) → small line chart   │
│  Temperature         → small line chart   │
├────────────────────────────────────────────┤
│  Disk: ████████░░ 78% / 64GB              │
│  Uptime: 3 days 14h 22m                   │
│  ML Pipeline: ● Running                   │
│  Last Heartbeat: 00:42:15 ago             │
├────────────────────────────────────────────┤
│  [Restart Service]  [Decommission]        │
└────────────────────────────────────────────┘
```

Charts: `ChartCard.svelte` with `type='line'`, small height (120px), time axis

### Device History Modal

- `GET /api/v1/devices/{id}/history?page=&size=`
- Shows health event log: DataTable with [Timestamp, CPU, RAM, Temp, Status, Event]
- Health events: heartbeat, online, offline, warning

### Register Device Modal

```
┌──────────────────────────────────┐
│  Register New Device             │
├──────────────────────────────────┤
│  Name: [input-field]             │
│  Mess Assignment: [SelectField]  │
│  Location Notes: [textarea]      │
│  [Cancel]  [Register]            │
└──────────────────────────────────┘
```

On submit → `POST /api/v1/devices` → response includes `api_key`
Show success modal with generated API key:
```
Device registered!
API Key (copy this now — shown once):
[████████████████████████] [📋 Copy]
```

### Edit Device Modal

- Name, mess assignment, notes, status (active/decommissioned)
- PATCH `/api/v1/devices/{id}`

### Restart Service

- ConfirmDialog: "Restart ML service on this device?"
- POST → `/api/v1/devices/{id}/restart`
- Show loading state, then notify result

### API Types

```typescript
export interface Device {
  id: string;
  name: string;
  mess_name?: string;
  status: 'online' | 'offline' | 'warning' | 'decommissioned';
  ip_address?: string;
  api_key?: string;         // shown only at creation
  api_key_preview?: string; // last 4 chars
  cpu_percent?: number;
  ram_percent?: number;
  disk_percent?: number;
  temperature?: number;
  uptime_seconds?: number;
  ml_pipeline_running?: boolean;
  last_heartbeat?: string;
  location_notes?: string;
  registered_at: string;
}
export interface DeviceHealth {
  device_id: string;
  cpu_history: Array<{ timestamp: string; value: number }>;
  ram_history: Array<{ timestamp: string; value: number }>;
  temp_history: Array<{ timestamp: string; value: number }>;
  disk_percent: number;
  disk_gb_used: number;
  disk_gb_total: number;
  uptime_seconds: number;
  ml_pipeline_running: boolean;
  last_heartbeat: string;
}
export interface DeviceHealthEvent {
  id: string;
  device_id: string;
  event_type: 'heartbeat' | 'online' | 'offline' | 'warning';
  cpu_percent?: number;
  ram_percent?: number;
  temperature?: number;
  timestamp: string;
}
```

---

## Shared Stores for This Phase

### `src/lib/stores/notifications.ts`
```typescript
// State: notifications[], unreadCount, preferences, loading
// Actions: fetchNotifications(filters), markRead(id), markAllRead(),
//          delete(id), fetchPreferences(), updatePreferences(prefs),
//          fetchUnreadCount()
```

### `src/lib/stores/reports.ts`
```typescript
// State: reports[], total, schedules, loading, pollingIds (Set<string>)
// Actions: fetchReports(filters), generateReport(data), downloadReport(id, name),
//          deleteReport(id), fetchSchedules(), createSchedule(data),
//          updateSchedule(id, data), deleteSchedule(id), startPolling(id)
```

### `src/lib/stores/devices.ts`
```typescript
// State: devices[], total, loading, viewMode ('card' | 'table')
// Actions: fetchDevices(filters), registerDevice(data), updateDevice(id, data),
//          decommission(id), fetchHealth(id), fetchHistory(id, page), restart(id)
```

---

## Verification Checklist

**Notifications:**
- [ ] Notifications load with pagination
- [ ] Unread count shown in global header
- [ ] Mark as read works (card dims)
- [ ] Mark all read works
- [ ] Priority left bar colors correct
- [ ] Preferences modal loads, toggles save
- [ ] Create notification modal (admin) works
- [ ] Date/type/priority filters work

**Reports:**
- [ ] Reports table loads
- [ ] Status badges correct
- [ ] Generate report modal: all fields, submit queues report
- [ ] Generating status shows spinner
- [ ] Polling updates status to 'ready'
- [ ] Download button triggers file download
- [ ] Scheduled reports tab: list, create, edit, delete schedules

**Devices:**
- [ ] Device cards render with status dots and progress bars
- [ ] Table view toggle works
- [ ] Health modal shows CPU/RAM/temp charts
- [ ] Device history DataTable loads
- [ ] Register device: shows API key on success
- [ ] Edit device modal works
- [ ] Restart service confirm + notify
- [ ] Decommission works with confirm

---

## Exit Criteria

✅ All three pages fully functional  
✅ Notification centre with real-time unread badge  
✅ Report generation and polling working  
✅ Device health modal with mini charts  
✅ No TypeScript errors
