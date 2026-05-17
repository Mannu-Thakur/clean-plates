# CleanPlates Frontend — Master Plan Index

**Stack:** SvelteKit 2 + Svelte 5 + TypeScript + TailwindCSS 3 + Chart.js  
**Backend:** FastAPI at `/api/v1` (all 19 routers implemented & tested)  
**Design:** Binance-reference dark theme — NO gradients, NO elevation/shadows on surfaces  
**Nav:** Collapsible aside nav (Material 3 style — icon-only when collapsed, full when expanded)  
**Architecture:** Modular component-first design — every primitive reused across all 14 pages

---

## Phase Map

| Phase  | Plan File                                                                    | Scope                                                    | Pages            |
| ------ | ---------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------- |
| **P1** | [01-foundation-design-system.md](./01-foundation-design-system.md)           | Design system, tokens, layout shell, nav, auth           | Login            |
| **P2** | [02-dashboard-and-monitoring.md](./02-dashboard-and-monitoring.md)           | Overview dashboard + Live monitoring (WebSocket)         | Pages 2, 3       |
| **P3** | [03-analytics-and-students.md](./03-analytics-and-students.md)               | Full analytics suite, student list, student intelligence | Pages 4, 5, 6    |
| **P4** | [04-warnings-and-rules.md](./04-warnings-and-rules.md)                       | Warnings/penalties, Rule Engine Builder                  | Pages 7, 8       |
| **P5** | [05-notifications-reports-devices.md](./05-notifications-reports-devices.md) | Notification centre, Reports, Devices                    | Pages 9, 10, 11  |
| **P6** | [06-config-settings-audit.md](./06-config-settings-audit.md)                 | Configuration, Settings, Audit log                       | Pages 12, 13, 14 |

---

## Dependency Graph

```
P1 (Foundation + Auth + Layout Shell)
 └── P2 (Dashboard + Live Monitoring)     ← uses StatCard, ChartCard, Feed, Gauge, WS
      └── P3 (Analytics + Students)       ← uses DataTable, FilterBar, ChartCard, Tabs
           └── P4 (Warnings + Rules)      ← uses DataTable, Modal, Builder panels
                └── P5 (Notif + Reports + Devices) ← uses DataTable, Modal, Timeline
                     └── P6 (Config + Settings + Audit) ← uses Form, DataTable, Modal
```

Each phase depends on all prior phases' shared components. No phase may start before the previous is complete.

---

## Shared Component Registry (defined in P1, reused by all)

| Component         | File                           | Used In             |
| ----------------- | ------------------------------ | ------------------- |
| `Button`          | `ui/Button.svelte`             | Everywhere          |
| `Card`            | `ui/Card.svelte`               | Everywhere          |
| `StatCard`        | `ui/StatCard.svelte`           | P2, P3, P4, P5      |
| `StatusBadge`     | `ui/StatusBadge.svelte`        | Everywhere          |
| `Modal`           | `ui/Modal.svelte`              | P2, P3, P4, P5, P6  |
| `DataTable`       | `ui/DataTable.svelte`          | P3, P4, P5, P6      |
| `FilterBar`       | `ui/FilterBar.svelte`          | P3, P4, P5, P6      |
| `Pagination`      | `ui/Pagination.svelte`         | P3, P4, P5, P6      |
| `EmptyState`      | `ui/EmptyState.svelte`         | Everywhere          |
| `SkeletonRow`     | `ui/SkeletonRow.svelte`        | Everywhere          |
| `ConfirmDialog`   | `ui/ConfirmDialog.svelte`      | P4, P5, P6          |
| `ToastHost`       | `ui/ToastHost.svelte`          | Root layout         |
| `ChartCard`       | `charts/ChartCard.svelte`      | P2, P3              |
| `Gauge`           | `charts/Gauge.svelte`          | P2, P3              |
| `DashboardShell`  | `layout/DashboardShell.svelte` | All dashboard pages |
| `PageHeader`      | `layout/PageHeader.svelte`     | All dashboard pages |
| `Tabs`            | `ui/Tabs.svelte`               | P3, P4, P5, P6      |
| `SearchInput`     | `ui/SearchInput.svelte`        | P3, P4, P5, P6      |
| `Toggle`          | `ui/Toggle.svelte`             | P4, P6              |
| `FormField`       | `ui/FormField.svelte`          | P1, P4, P6          |
| `DateRangePicker` | `ui/DateRangePicker.svelte`    | P3, P4, P5, P6      |
| `SelectField`     | `ui/SelectField.svelte`        | P3, P4, P5, P6      |
| `FileUpload`      | `ui/FileUpload.svelte`         | P3, P6              |

---

## API Surface Summary

| Domain         | Key Endpoints                                                                                                                                                                                            | Phase  |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Auth           | `/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`                                                                                                                                               | P1     |
| Analytics      | `/analytics/overview`, `/analytics/trends`, `/analytics/peaks`, `/analytics/meal-distribution`, `/analytics/food-waste-distribution`, `/analytics/sustainability-scores`, `/analytics/branch-comparison` | P2, P3 |
| Monitoring     | `/monitoring/current-session`, `/monitoring/recent-entries`, `/monitoring/device-statuses`                                                                                                               | P2     |
| WS             | `WS /ws/dashboard`, `WS /ws/monitoring`                                                                                                                                                                  | P2     |
| Students       | `/students`, `/students/{id}`, `/students/{id}/stats`, `/students/{id}/timeline`, `/students/{id}/food-breakdown`, `/students/{id}/warnings`, `/students/import-csv`, `/students/export`                 | P3     |
| Waste          | `/waste/entries`, `/waste/entries/{id}`                                                                                                                                                                  | P3, P2 |
| Warnings       | `/warnings`, `/warnings/{id}`, `/warnings/export`, `/penalties`, `/escalations`                                                                                                                          | P4     |
| Rules          | `/rules`, `/rules/{id}`, `/rules/{id}/test`, `/rules/{id}/simulate`, `/rules/{id}/executions`, `/rules/chains`, `/rules/metadata/*`                                                                      | P4     |
| Notifications  | `/notifications`, `/notifications/{id}`, `/notifications/mark-all-read`, `/notifications/preferences`                                                                                                    | P5     |
| Reports        | `/reports`, `/reports/generate`, `/reports/{id}`, `/reports/{id}/download`, `/reports/schedules`                                                                                                         | P5     |
| Devices        | `/devices`, `/devices/{id}`, `/devices/{id}/health`, `/devices/{id}/history`                                                                                                                             | P5     |
| Config         | `/config/{section}`, `/config/institution`, `/config/thresholds`, `/config/meals`, `/config/branches`                                                                                                    | P6     |
| Settings       | `/settings/users`, `/settings/security`, `/settings/backups`, `/settings/maintenance`, `/settings/logo`                                                                                                  | P6     |
| Audit          | `/audit`, `/audit/{id}`, `/audit/stats`                                                                                                                                                                  | P6     |
| Filter Presets | `/filter-presets`                                                                                                                                                                                        | P3     |
| Roles          | `/roles`                                                                                                                                                                                                 | P6     |
| Templates      | `/templates`                                                                                                                                                                                             | P6     |

---

## Design Constraints (from BINANCE-REFERENCE.md)

1. **Canvas:** `#0b0e11` (deep near-black) — flat background, no gradient
2. **Card surface:** `#1e2329` — all panels, cards, modals
3. **Elevated surface:** `#2b3139` — dropdowns, tooltips, table headers
4. **Primary accent:** `#fcd535` (yellow) — ALL CTAs, active nav, brand moments
5. **Body text:** `#eaecef` on dark surfaces
6. **Muted text:** `#707a8a`
7. **Border:** `#2b3139` (hairline on dark)
8. **Up / green:** `#0ecb81` — success, improvement, online
9. **Down / red:** `#f6465d` — error, warning, offline
10. **No gradients anywhere** — not on body, not on cards, not on buttons
11. **No box-shadows on surfaces** — only focus rings are allowed
12. **Radius system:** xs=2px, sm=4px, md=6px, lg=8px, xl=12px
13. **Nav:** Aside, collapsible — icon-only (76px) or full (260px), yellow active state
14. **Typography:** Inter font (already installed) — sizes per Binance type scale
