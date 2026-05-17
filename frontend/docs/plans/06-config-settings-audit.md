# Phase 6 — Configuration, Settings & Audit Log

**Duration:** ~5 days  
**Depends on:** All previous phases — this is the final feature phase  
**Required before:** Nothing — final phase before QA/deploy  
**Pages implemented:**

- Page 12: `/dashboard/config` — System Configuration
- Page 13: `/dashboard/settings` — Application Settings
- Page 14: `/dashboard/audit` — Audit Log

---

## Page 12 — System Configuration (`/dashboard/config`)

### Route: `src/routes/dashboard/config/+page.svelte`

**Access:** super_admin, institution_admin (mess_admin: read-only for some sections)

### Layout — Tabbed Sections

```
┌──────────────────────────────────────────────────────────────┐
│  PageHeader: "Configuration"                    [Save All]   │
├──────────────────────────────────────────────────────────────┤
│  [Institution] [Thresholds] [Meals] [System] [Device] [App]  │
├──────────────────────────────────────────────────────────────┤
│  Config form for selected section                            │
└──────────────────────────────────────────────────────────────┘
```

### API Calls

| Action                    | Endpoint                              |
| ------------------------- | ------------------------------------- |
| Get institution config    | `GET /api/v1/config/institution`      |
| Update institution config | `PATCH /api/v1/config/institution`    |
| Get device config         | `GET /api/v1/config/device`           |
| Update device config      | `PATCH /api/v1/config/device`         |
| Get thresholds            | `GET /api/v1/config/thresholds`       |
| Update thresholds         | `PATCH /api/v1/config/thresholds`     |
| Get meal timings          | `GET /api/v1/config/meals`            |
| Update meal timings       | `PUT /api/v1/config/meals`            |
| Get system policies       | `GET /api/v1/config/system`           |
| Update system policies    | `PATCH /api/v1/config/system`         |
| Get branches              | `GET /api/v1/config/branches`         |
| Update branches           | `PUT /api/v1/config/branches`         |
| Reset section             | `POST /api/v1/config/reset/{section}` |

> **Note:** There is no `/api/v1/config/all` aggregate endpoint. Load all sections simultaneously using `Promise.all()` in the `+page.svelte` `onMount`:
>
> ```typescript
> const [institution, thresholds, meals, system, device, branches] =
>   await Promise.all([
>     api.get('/config/institution'),
>     api.get('/config/thresholds'),
>     api.get('/config/meals'),
>     api.get('/config/system'),
>     api.get('/config/device'),
>     api.get('/config/branches')
>   ]);
> ```

### Tab 1: Institution

**Fields:**

- Institution Name: `input-field`
- Institution Code: `input-field`
- Timezone: `SelectField` (list of IANA timezones — preset common ones + search)
- Address: `textarea-field`
- Phone: `input-field`
- Email: `input-field`
- Website: `input-field`
- Logo Upload: `FileUpload.svelte` (accepts .png/.jpg, max 2MB) → `POST /api/v1/settings/appearance/logo`
  - Shows current logo preview (if set) as 80×80 rounded square
  - On upload success: preview updates immediately

**Branches sub-section:**

- List of branches as editable rows:
  - Each row: `[Branch Code input] [Branch Name input] [Delete ✕]`
  - "Add Branch" button → appends new empty row
- Save branches → `PATCH /api/v1/config/institution` with branches array

### Tab 2: Waste Thresholds

**Fields (from ThresholdSchema):**

- Daily Waste Warning Level (g): `input-field type="number"` → `warning_threshold_grams`
- Daily Waste Penalty Level (g): `input-field type="number"` → `penalty_threshold_grams`
- Per-Meal Waste Limit (g): `input-field type="number"` → `per_meal_limit_grams`
- Zero Waste Reward Threshold (g): `input-field type="number"` → `zero_waste_threshold_grams`
- Auto-Warning Level: `SelectField` (yellow/orange/red) → `auto_warning_level`
- Auto-Penalty Days (number of warnings before penalty): `input-field type="number"`

**Preview strip below form:**

- Visual scale showing threshold zones (green → yellow → orange → red)
- Updates in real-time as user changes values

### Tab 3: Meal Times

**Fields (from MealScheduleSchema):**
For each meal (Breakfast, Lunch, Dinner):

- Start Time: `input type="time"`
- End Time: `input type="time"`
- Enabled: `Toggle`
- Label (custom name): `input-field`

**Schedule preview:**

- Horizontal timeline for the day showing all 3 meal windows as colored bars

### Tab 4: System Policy

**Fields (from SystemPolicySchema):**

- Audit Retention Days: `input-field type="number"`
- Max Upload Size (MB): `input-field type="number"`
- Session Timeout (minutes): `input-field type="number"`
- Allowed File Types: chips input (add/remove mime types)
- Maintenance Mode: `Toggle` + Note textarea (shown when enabled)
- Data Archive After (days): `input-field type="number"`

### Tab 5: Device Configuration

**Fields (from DeviceConfigSchema):**

- Device Offline Threshold (minutes): `input-field type="number"`
- Heartbeat Interval (seconds): `input-field type="number"`
- Auto-Restart on Failure: `Toggle`
- Max Retry Attempts: `input-field type="number"`
- ML Confidence Minimum (%): `input-field type="number"` with range 0-100

### Tab 6: Appearance

**Fields (from AppearanceConfigSchema):**

- Institution Logo: (same as institution tab — shows current logo)
- System Name (displayed in UI): `input-field` (e.g., "CleanPlates")
- Footer Text: `textarea-field`
- Primary Color Note (read-only): "Design is based on Binance reference. Accent color is fixed at #FCD535."

### Save All Button (PageHeader)

- Saves ALL currently unsaved changes across ALL tabs at once
- Shows loading state, then success toast
- Per-tab "Save" buttons also available for individual section saves

### Reset Section

- Each tab has a "Reset to defaults" ghost button
- `ConfirmDialog` → `POST /api/v1/config/reset/{section}` → refetch section

### API Types

```typescript
export interface InstitutionConfig {
  name: string;
  code: string;
  timezone: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_url?: string;
  branches: Array<{ code: string; name: string }>;
}
export interface ThresholdConfig {
  warning_threshold_grams: number;
  penalty_threshold_grams: number;
  per_meal_limit_grams: number;
  zero_waste_threshold_grams: number;
  auto_warning_level: 'yellow' | 'orange' | 'red';
  auto_penalty_after_warnings: number;
}
export interface MealConfig {
  breakfast: { start: string; end: string; enabled: boolean; label: string };
  lunch: { start: string; end: string; enabled: boolean; label: string };
  dinner: { start: string; end: string; enabled: boolean; label: string };
}
export interface SystemPolicyConfig {
  audit_retention_days: number;
  max_upload_size_mb: number;
  session_timeout_minutes: number;
  allowed_file_types: string[];
  maintenance_mode: boolean;
  maintenance_note?: string;
  data_archive_after_days: number;
}
export interface DeviceConfig {
  device_offline_threshold_minutes: number;
  heartbeat_interval_seconds: number;
  auto_restart_on_failure: boolean;
  max_retry_attempts: number;
  ml_confidence_minimum: number;
}
```

---

## Page 13 — Application Settings (`/dashboard/settings`)

### Route: `src/routes/dashboard/settings/+page.svelte`

**Access:** super_admin only (most sections); institution_admin (limited)

### Layout — Tabbed

```
┌────────────────────────────────────────────────────────────────┐
│  PageHeader: "Settings"                                        │
├────────────────────────────────────────────────────────────────┤
│  [Users] [Security] [Roles] [Backups] [Email] [Maintenance]    │
├────────────────────────────────────────────────────────────────┤
│  Tab content                                                   │
└────────────────────────────────────────────────────────────────┘
```

### API Calls

| Action                | Endpoint                                                                    |
| --------------------- | --------------------------------------------------------------------------- |
| List users            | `GET /api/v1/settings/users`                                                |
| Create user           | `POST /api/v1/settings/users`                                               |
| Update user           | `PATCH /api/v1/settings/users/{id}`                                         |
| Deactivate user       | `POST /api/v1/settings/users/{id}/deactivate`                               |
| Reset password        | `POST /api/v1/settings/users/{id}/reset-password`                           |
| Get security config   | `GET /api/v1/settings/security`                                             |
| Update security       | `PATCH /api/v1/settings/security`                                           |
| List roles            | `GET /api/v1/roles`                                                         |
| Update role           | `PATCH /api/v1/roles/{id}`                                                  |
| List backups          | `GET /api/v1/settings/backups`                                              |
| Create backup         | `POST /api/v1/settings/backups`                                             |
| Restore backup        | `POST /api/v1/settings/backups/restore` (file upload, field: `backup_file`) |
| Download backup       | `GET /api/v1/settings/backups/{id}/download`                                |
| Get appearance config | `GET /api/v1/settings/appearance`                                           |
| Update appearance     | `PATCH /api/v1/settings/appearance`                                         |
| Upload logo           | `POST /api/v1/settings/appearance/logo`                                     |
| Get email config      | (via `GET /api/v1/settings/appearance` — or future endpoint)                |
| List templates        | `GET /api/v1/templates`                                                     |
| Get template          | `GET /api/v1/templates/{id}`                                                |
| Update template       | `PATCH /api/v1/templates/{id}`                                              |
| Preview template      | `POST /api/v1/templates/{id}/preview`                                       |
| Clear cache           | `POST /api/v1/settings/maintenance/clear-cache`                             |
| Optimize DB           | `POST /api/v1/settings/maintenance/optimize-db`                             |
| System info           | `GET /api/v1/settings/maintenance/system-info`                              |

### Tab 1: User Management

**DataTable Columns:** Name, Email, Role, Status, Created, Last Login, Actions

**Role Badge:**

- `super_admin` → `badge-down` (red — most privileged)
- `institution_admin` → `badge-primary`
- `mess_admin` → `badge-info`
- `analytics_viewer` → `badge-muted`
- `staff_operator` → `badge-up`

**Row Actions:**

- ✏ Edit → opens edit modal (name, role, active status)
- 🔑 Reset Password → `ConfirmDialog` → POST reset → shows temp password in success modal
- 🚫 Deactivate → `ConfirmDialog` (cannot deactivate own account, cannot deactivate last super_admin) → `POST /api/v1/settings/users/{id}/deactivate`

> **Note:** Users are **deactivated**, not permanently deleted. The backend has no DELETE endpoint for users.

**Create User Modal:**

```
  Name: [input-field]
  Email: [input-field]
  Role: [SelectField]
  Temporary Password: [input-field] (auto-generated toggle)
  Send Welcome Email: [Toggle]
  [Cancel]  [Create User]
```

POST → success modal shows temp password (if not emailing)

**Edit User Modal:**

```
  Name: [input-field]
  Email: [input-field] (read-only)
  Role: [SelectField]
  Active: [Toggle]
  [Cancel]  [Save Changes]
```

### Tab 2: Security

**Fields (from SecurityConfigSchema):**

- Access Token Expiry (minutes): `input-field type="number"`
- Refresh Token Expiry (days): `input-field type="number"`
- Max Login Attempts: `input-field type="number"`
- Lockout Duration (minutes): `input-field type="number"`
- Require Strong Password: `Toggle`
- Two-Factor Auth (future): `Toggle` (disabled, shows "Coming Soon" label)

Note box: `card p-4 border-l-4 border-primary text-sm text-muted`

> "Security settings take effect immediately. Existing sessions are not terminated by token expiry changes."

### Tab 3: Roles & Permissions

- List all 5 system roles: DataTable
- Columns: Role Name, Display Name, Description, Permissions Count, System Role (lock icon if true)
- System roles (is_system=true): cannot be deleted — show lock icon
- Edit modal: update description + permissions (if backend supports permission granularity)
- Permissions shown as chip list with `Toggle` per permission

### Tab 4: Backups

```
┌───────────────────────────────────────────┐
│  Backup Storage: 148 MB / ~2 GB          │
│  Last Backup: 2h ago  [Create Backup Now] │
├───────────────────────────────────────────┤
│  DataTable: backups list                  │
│  Columns: Name, Size, Type, Status, Date  │
│  Actions: [Download] [Restore] [Delete]   │
└───────────────────────────────────────────┘
```

**Create Backup:**

- Button in section header
- `ConfirmDialog`: "Create a full database backup now?"
- POST → shows generating status
- Polls backup status (like reports polling)

**Restore Backup:**

- `ConfirmDialog` with WARNING alert:
  > ⚠️ Restoring will overwrite ALL current data. The application will restart. This cannot be undone.
- Requires typing "RESTORE" to confirm (text input check before enabling button)
- Click Restore → show file picker (`FileUpload.svelte`) → user selects the downloaded backup file
- `api.upload('/settings/backups/restore', 'backup_file', file)` sends the file as multipart upload
- App shows "Restoring backup..." overlay → API processes async via ARQ worker
- **Important:** The server may restart during restore; the `fetch` may time out. Frontend must catch network errors and poll `GET /health` until the server responds again.

**Backup Status Badge:**

- `creating` → `badge-info` + spinner
- `completed` → `badge-up`
- `failed` → `badge-down`
- `restoring` → `badge-primary` + spinner

### Tab 5: Email Configuration

**Fields:**

- SMTP Host: `input-field`
- SMTP Port: `input-field type="number"`
- Use TLS: `Toggle`
- Username: `input-field`
- Password: `input-field type="password"` + show/hide
- From Email: `input-field`
- From Name: `input-field`

**Test Email Section:**

```
  Send Test Email To: [input-field type="email"]
  [Send Test] → shows success/failure inline
```

**Email Templates Sub-section:**

- DataTable: templates list (warning, penalty, welcome, reset-password, daily-digest, weekly-report)
- Edit template button → opens Template Editor Modal

**Template Editor Modal:**

```
┌──────────────────────────────────────────┐
│  Edit Template: Warning Email            │
├──────────────────────────────────────────┤
│  Subject: [input-field]                  │
│  Body (HTML):                            │
│  [textarea - monospace, tall]            │
│  Available variables:                    │
│  {{student_name}} {{waste_grams}} ...   │
│  [Preview]  [Reset to Default]  [Save]   │
└──────────────────────────────────────────┘
```

Preview → `POST /api/v1/templates/{id}/preview` → shows rendered HTML in iframe

### Tab 6: Maintenance

**System Info Card:**

- App Version: `text-primary font-mono`
- Python Version, FastAPI Version
- DB Size: formatted bytes
- Redis Status: badge
- ARQ Workers: badge
- Uptime: formatted duration
- Active Connections: WS count

Fetch from `GET /api/v1/settings/maintenance/system-info` on tab open.

**Cache Management:**

```
  Redis Cache: [240 keys, 4.2 MB]  [Clear Cache]
```

Clear Cache → `ConfirmDialog` → POST → `notify('Cache cleared', 'success')`

**Maintenance Mode Toggle:**

- `Toggle` → if enabled, shows maintenance message input
- PATCH to config endpoint (or settings endpoint)
- When enabled: shows red banner across top of all pages

**Database Optimization:**

- "Optimize Database" button → `POST /api/v1/settings/maintenance/optimize-db`
- Shows result: before/after size, time taken

---

## Page 14 — Audit Log (`/dashboard/audit`)

### Route: `src/routes/dashboard/audit/+page.svelte`

**Access:** super_admin, institution_admin (read-only)

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  PageHeader: "Audit Log"                          [Export]   │
├──────────────────────────────────────────────────────────────┤
│  Stats: [Total Events] [Today] [Failed] [By User]            │
├──────────────────────────────────────────────────────────────┤
│  FilterBar: [Search] [Action▼] [Resource▼] [User▼] [Date]   │
├──────────────────────────────────────────────────────────────┤
│  DataTable (large, full-width)                               │
│  + Pagination                                                │
└──────────────────────────────────────────────────────────────┘
```

### API Calls

| Action            | Endpoint                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------- |
| List audit events | `GET /api/v1/audit?page=&size=&action=&resource_type=&user_id=&start_date=&end_date=&search=` |
| Get event         | `GET /api/v1/audit/{id}`                                                                      |
| Audit stats       | `GET /api/v1/audit/stats`                                                                     |
| Export audit      | `GET /api/v1/audit/export?format=csv` → `api.download()`                                      |

### Stat Row

| Card          | Value            | Tone    |
| ------------- | ---------------- | ------- |
| Total Events  | count (all time) | neutral |
| Today         | count            | neutral |
| Failed Events | count            | bad     |
| Unique Users  | count            | info    |

### DataTable Columns

| Column     | Field                                        | Width | Sortable |
| ---------- | -------------------------------------------- | ----- | -------- |
| Time       | `created_at` (relative + abs on hover)       | 150px | Yes      |
| User       | `user_name` or "System"                      | 160px | No       |
| Action     | `action` badge                               | 130px | Yes      |
| Resource   | `resource_type` + `resource_id`              | 180px | No       |
| IP Address | `ip_address`                                 | 130px | No       |
| Status     | `status` badge                               | 80px  | Yes      |
| Changes    | `before_state` → `after_state` (icon button) | 80px  | No       |

**Action Badge Coloring:**

- `CREATE`, `REGISTER` → `badge-up`
- `UPDATE`, `PATCH` → `badge-info`
- `DELETE`, `DECOMMISSION` → `badge-down`
- `LOGIN`, `LOGOUT` → `badge-muted`
- `LOGIN_FAILED`, `ERROR` → `badge-down`
- `GENERATE`, `EXPORT` → `badge-primary`

**Status Badge:**

- `success` → `badge-up`
- `failed` → `badge-down`
- `partial` → `badge-primary`

### Change Diff Modal

Click the diff icon (changes column) → modal showing:

```
Before:                    After:
{                          {
  "status": "active",        "status": "resolved",
  "level": "yellow"          "level": "yellow",
}                            "resolved_by": "admin@..."
                           }
```

- Side-by-side JSON diff view
- Changed keys highlighted: added → `text-up bg-up/10`, removed → `text-down bg-down/10`, unchanged → `text-muted`
- JSON formatted with 2-space indent in `font-mono text-sm`
- Pure client-side JSON diffing (no lib needed — just compare keys)

### Audit Event Detail Modal

Click any row → full event detail:

```
Audit Event Details:
  ID:          [uuid]
  Timestamp:   [full datetime]
  User:        Admin User (admin@mess.edu)
  Action:      UPDATE
  Resource:    Warning #abc123
  IP Address:  192.168.1.100
  User Agent:  Chrome/125 ...
  Status:      ✓ success

  Request Data:
  [JSON]

  Before State:
  [JSON]

  After State:
  [JSON]
```

### FilterBar Fields

- Search input: searches message / resource_id
- Action: SelectField (all actions from distinct values or predefined list)
- Resource Type: SelectField (student, device, rule, warning, user, config, report, ...)
- User: SelectField (all users from `/api/v1/settings/users` → `{id, name}` pairs)
- Date Range: `DateRangePicker`

### Export

- Button in PageHeader
- Format modal: CSV / Excel
- `api.download('/audit/export?format=csv', 'audit-log.csv', filters)`

### API Types

```typescript
export interface AuditEvent {
  id: string;
  user_id?: string;
  user_name?: string;
  user_role?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
  request_data?: Record<string, unknown> | null;
  status: 'success' | 'failed' | 'partial';
  error_message?: string;
  created_at: string;
}
export interface AuditStats {
  total_events: number;
  events_today: number;
  failed_events: number;
  unique_users: number;
  top_actions: Array<{ action: string; count: number }>;
  top_users: Array<{ user_name: string; count: number }>;
}
```

---

## Shared Stores for This Phase

### `src/lib/stores/config.ts`

```typescript
// State: sections (each config section), loading, dirty (which sections have unsaved changes)
// Actions: fetchSection(section), updateSection(section, data), resetSection(section), saveAll()
```

### `src/lib/stores/settings.ts`

```typescript
// State: users[], roles[], backups[], templates[], systemInfo, securityConfig, emailConfig, loading
// Actions: fetchUsers(), createUser(data), updateUser(id, data), deactivateUser(id), resetPassword(id),
//          fetchRoles(), updateRole(id, data),
//          fetchBackups(), createBackup(), restoreBackup(file), downloadBackup(id),
//          fetchTemplates(), updateTemplate(id, data), previewTemplate(id),
//          fetchSystemInfo(), clearCache(), optimizeDb()
```

### `src/lib/stores/audit.ts`

```typescript
// State: events[], total, stats, loading, filters
// Actions: fetchEvents(filters), fetchStats(), exportEvents(filters)
```

---

## Additional Global Features (completed in this phase)

### Global Notification Bell

- In `DashboardShell.svelte`: Bell icon with unread count badge
- Fetches unread on mount: `GET /api/v1/notifications?is_read=false&size=1` (just for count)
- WS events of type `notification` increment count

### Global Maintenance Banner

- In `DashboardShell.svelte`: checks config for maintenance mode
- If enabled: yellow banner at top of page `bg-primary text-on-primary text-center py-2`
- Text from maintenance_note config field

### 404 / Unauthorized Pages

- `src/routes/+error.svelte`: generic error page for SvelteKit errors
- 401 → shows "Please log in" with redirect to login
- 403 → shows "Access denied — insufficient permissions"
- 404 → shows "Page not found" with navigation back to dashboard

---

## Verification Checklist

**Config page:**

- [ ] All 6 tabs load correct data from API
- [ ] Institution: name, timezone, branches CRUD works
- [ ] Logo upload works, preview updates
- [ ] Thresholds: number inputs save correctly
- [ ] Meal times: time inputs and toggles save
- [ ] System policy: all fields save
- [ ] Device config: heartbeat, threshold fields save
- [ ] Reset to defaults shows ConfirmDialog and works
- [ ] Save All button saves all dirty sections

**Settings page:**

- [ ] Users DataTable loads
- [ ] Create user: all fields, temp password shown on success
- [ ] Edit user: name, role, active toggle
- [ ] Deactivate user: confirm dialog, cannot deactivate own account or last super_admin
- [ ] Reset password: confirm, shows temp password
- [ ] Security tab: all fields load and save
- [ ] Roles tab: 5 roles listed, system roles locked
- [ ] Backups tab: list loads, create backup polls to completion
- [ ] Restore backup: type "RESTORE" confirmation works
- [ ] Email config: fields save, test email sends
- [ ] Template editor: HTML textarea, preview iframe
- [ ] Maintenance tab: system info loads, cache clear works

**Audit page:**

- [ ] Table loads with pagination
- [ ] Stats cards show correct data
- [ ] Action badges correctly colored by action type
- [ ] Diff icon opens change diff modal
- [ ] JSON diff shows changed keys highlighted
- [ ] Row click opens full event detail modal
- [ ] All filters work (search, action, resource, user, date)
- [ ] Export CSV triggers download

---

## Final Cross-Phase QA Checklist

After Phase 6 is complete, verify across the entire application:

- [ ] Dark Binance theme consistent on ALL 14 pages — no light backgrounds anywhere
- [ ] No gradients, no box-shadows on surfaces
- [ ] Primary yellow (#fcd535) used only for CTAs, active nav, brand accents
- [ ] Up/down green/red (#0ecb81 / #f6465d) used for positive/negative indicators
- [ ] Nav collapses correctly on all pages
- [ ] All RBAC rules enforced (admin-only actions hidden for lower roles)
- [ ] WebSocket reconnects on all pages that use it
- [ ] Loading skeletons show on initial data fetch for all DataTables
- [ ] Empty states show when no data returned
- [ ] Error states + Retry buttons on all pages
- [ ] Confirm dialogs before all destructive actions
- [ ] Success/error toasts on all API mutations
- [ ] `npm run check` passes with zero TypeScript errors
- [ ] `npm run build` succeeds without errors
- [ ] All 14 page titles set via `<svelte:head><title>`

---

## Exit Criteria

✅ All 14 pages fully implemented and functional  
✅ Config, Settings, Audit pages complete  
✅ Global notification bell working  
✅ Maintenance banner working  
✅ Error pages working  
✅ Full QA checklist passed  
✅ `npm run build` succeeds cleanly
