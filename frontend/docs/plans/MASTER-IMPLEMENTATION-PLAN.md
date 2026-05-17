# CleanPlates Frontend — Master Implementation Plan

**Stack:** SvelteKit 2 + Svelte 5 + TypeScript + TailwindCSS 3 + Chart.js  
**Backend:** FastAPI `/api/v1` — 19 routers, all tested  
**Design:** Binance dark reference — NO gradients, NO box-shadows on surfaces  
**Nav:** Collapsible aside (Material 3) — 76px icon-only / 260px expanded  
**Architecture:** Modular component-first — every primitive reused across all 14 pages

---

## Current State Audit (as of analysis)

### ✅ Files that EXIST but need migration/fixes

| File                                              | Status          | Issue                                                                                                                          |
| ------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `tailwind.config.ts`                              | ⚠️ WRONG TOKENS | Uses light palette (`panel`, `line`, `field`, `fresh`, `lime`, `amber`, `coral`, `sky`) — must be replaced with Binance tokens |
| `src/app.css`                                     | ⚠️ WRONG THEME  | Has `color-scheme: light`, gradient body background, `.surface` with `shadow-soft`                                             |
| `src/app.html`                                    | ⚠️ MISSING META | No `color-scheme: dark`, no `theme-color`                                                                                      |
| `src/routes/+layout.svelte`                       | ⚠️ STUB         | Only 67 bytes — missing Chart.js dark defaults init                                                                            |
| `DashboardShell.svelte`                           | ⚠️ WRONG TOKENS | Uses `border-line`, `bg-white`, `bg-fresh`, `bg-slate-100`, `border-line` throughout                                           |
| `Button.svelte`                                   | ⚠️ WRONG TOKENS | Uses `bg-fresh`, `bg-coral`, `border-line`                                                                                     |
| `Card.svelte`                                     | ⚠️ CHECK        | Likely uses `.surface` with shadow                                                                                             |
| `StatCard.svelte`                                 | ⚠️ WRONG TOKENS | Uses `bg-fresh/10`, `bg-amber/10`, `bg-coral/10`, `text-ink`                                                                   |
| `StatusBadge.svelte`                              | ⚠️ WRONG TOKENS | Uses `bg-fresh/10`, `bg-amber/10`, `bg-coral/10`, `bg-slate-100`                                                               |
| `Modal.svelte`                                    | ⚠️ WRONG TOKENS | Uses `bg-white`, `shadow-soft`, `border-line`                                                                                  |
| `ChartCard.svelte`                                | ⚠️ WRONG COLORS | Uses old green/blue palette `#188a6b`, light grid `#edf2f6`                                                                    |
| `Gauge.svelte`                                    | ⚠️ CHECK        | Likely uses light colors                                                                                                       |
| `ToastHost.svelte`                                | ⚠️ CHECK        | Likely uses light colors                                                                                                       |
| `EmptyState.svelte`                               | ⚠️ CHECK        | Likely uses `text-muted` with old token                                                                                        |
| `src/routes/login/+page.svelte`                   | ⚠️ WRONG TOKENS | Uses `bg-ink`, `bg-fresh`, `border-line`, `bg-field`, `.surface`, `text-coral`, `text-fresh`                                   |
| `src/routes/dashboard/+page.svelte`               | ⚠️ WRONG TOKENS | Uses `.surface`, `bg-slate-100`, `field` class on select                                                                       |
| `src/routes/dashboard/monitoring/+page.svelte`    | ⚠️ WRONG TOKENS | Full migration needed                                                                                                          |
| `src/routes/dashboard/analytics/+page.svelte`     | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/students/+page.svelte`      | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/students/[id]/+page.svelte` | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/warnings/+page.svelte`      | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/rules/+page.svelte`         | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/notifications/+page.svelte` | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/devices/+page.svelte`       | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/config/+page.svelte`        | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/settings/+page.svelte`      | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/routes/dashboard/audit/+page.svelte`         | ⚠️ WRONG TOKENS | Migration needed                                                                                                               |
| `src/lib/api/client.ts`                           | ✅ GOOD         | Full fetch wrapper, JWT attach, auto-refresh — no changes needed                                                               |
| `src/lib/api/ws.ts`                               | ✅ GOOD         | ReconnectingSocket with backoff — no changes needed                                                                            |
| `src/lib/api/types.ts`                            | ⚠️ INCOMPLETE   | Missing types for monitoring, analytics sub-types, rules, warnings, etc.                                                       |
| `src/lib/stores/auth.ts`                          | ✅ GOOD         | initAuth, login, logout — no changes needed                                                                                    |
| `src/lib/stores/toast.ts`                         | ✅ GOOD         | notify() function — verify max-5 & auto-dismiss                                                                                |
| `src/lib/utils/format.ts`                         | ✅ GOOD         | grams, number, pct, dateTime, statusTone, itemsOf — no changes needed                                                          |
| `src/lib/utils/forms.ts`                          | ✅ GOOD         | Keep as-is                                                                                                                     |
| `src/lib/components/layout/navigation.ts`         | ✅ GOOD         | All 12 nav items with correct RBAC roles                                                                                       |

### ❌ Files that are MISSING (must be created)

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
| `bg-card`             | `#1e2329` | Cards, panels, modals, aside        |
| `bg-elevated`         | `#2b3139` | Table headers, dropdowns, dividers  |
| `bg-primary`          | `#fcd535` | All CTAs, active nav, brand         |
| `bg-primary-hover`    | `#f0b90b` | Button hover                        |
| `bg-primary-disabled` | `#3a3a1f` | Disabled CTA                        |
| `text-ink`            | `#181a20` | Text on yellow (buttons)            |
| `text-body`           | `#eaecef` | Primary text on dark                |
| `text-muted`          | `#707a8a` | Labels, secondary text              |
| `text-muted-strong`   | `#929aa5` | Strong muted                        |
| `border-border`       | `#2b3139` | All borders                         |
| `text-up`             | `#0ecb81` | Success, online, positive           |
| `text-down`           | `#f6465d` | Error, offline, negative            |
| `text-info`           | `#3b82f6` | Info badges                         |
| `text-on-primary`     | `#181a20` | Same as ink                         |
| `text-on-dark`        | `#ffffff` | White text                          |

**Rules:** NO `box-shadow` on cards/panels. NO gradient anywhere. Focus rings only.  
**Radius:** xs=2px, sm=4px, md=6px, lg=8px, xl=12px  
**Nav widths:** Collapsed=76px (icon only), Expanded=260px

---

## Phase Map

| Phase  | Scope                                                            | Duration | Pages            |
| ------ | ---------------------------------------------------------------- | -------- | ---------------- |
| **P1** | Design system migration + missing shared components + auth       | 2–3 days | Login            |
| **P2** | Dashboard + Live Monitoring token migration + feature completion | 2–3 days | Pages 2, 3       |
| **P3** | Analytics + Students list + Student intelligence                 | 3 days   | Pages 4, 5, 6    |
| **P4** | Warnings/Penalties + Rule Engine Builder                         | 3 days   | Pages 7, 8       |
| **P5** | Notifications + Reports + Devices                                | 3 days   | Pages 9, 10, 11  |
| **P6** | Configuration + Settings + Audit log                             | 2–3 days | Pages 12, 13, 14 |

Each phase is independently executable. No phase may begin until all prior phases pass `npm run check` and render correctly in the browser.

---

## Shared Component Registry

| Component         | File                           | Created In   | Used By             |
| ----------------- | ------------------------------ | ------------ | ------------------- |
| `Button`          | `ui/Button.svelte`             | P1 (migrate) | All                 |
| `Card`            | `ui/Card.svelte`               | P1 (migrate) | All                 |
| `StatCard`        | `ui/StatCard.svelte`           | P1 (migrate) | P2, P3, P4, P5      |
| `StatusBadge`     | `ui/StatusBadge.svelte`        | P1 (migrate) | All                 |
| `Modal`           | `ui/Modal.svelte`              | P1 (migrate) | P2–P6               |
| `EmptyState`      | `ui/EmptyState.svelte`         | P1 (migrate) | All                 |
| `ToastHost`       | `ui/ToastHost.svelte`          | P1 (migrate) | Root layout         |
| `DataTable`       | `ui/DataTable.svelte`          | P1 (CREATE)  | P3–P6               |
| `FilterBar`       | `ui/FilterBar.svelte`          | P1 (CREATE)  | P3–P6               |
| `Pagination`      | `ui/Pagination.svelte`         | P1 (CREATE)  | P3–P6               |
| `ConfirmDialog`   | `ui/ConfirmDialog.svelte`      | P1 (CREATE)  | P4–P6               |
| `Tabs`            | `ui/Tabs.svelte`               | P1 (CREATE)  | P3–P6               |
| `Toggle`          | `ui/Toggle.svelte`             | P1 (CREATE)  | P4, P6              |
| `FormField`       | `ui/FormField.svelte`          | P1 (CREATE)  | P1, P4, P6          |
| `SearchInput`     | `ui/SearchInput.svelte`        | P1 (CREATE)  | P3–P6               |
| `DateRangePicker` | `ui/DateRangePicker.svelte`    | P1 (CREATE)  | P3–P6               |
| `SelectField`     | `ui/SelectField.svelte`        | P1 (CREATE)  | P3–P6               |
| `FileUpload`      | `ui/FileUpload.svelte`         | P1 (CREATE)  | P3, P6              |
| `SkeletonRow`     | `ui/SkeletonRow.svelte`        | P1 (CREATE)  | All                 |
| `ChartCard`       | `charts/ChartCard.svelte`      | P1 (migrate) | P2, P3              |
| `Gauge`           | `charts/Gauge.svelte`          | P1 (migrate) | P2                  |
| `DashboardShell`  | `layout/DashboardShell.svelte` | P1 (migrate) | All dashboard pages |
| `PageHeader`      | `layout/PageHeader.svelte`     | P1 (CREATE)  | All dashboard pages |

---

## API Surface by Phase

| Phase | Domain         | Key Endpoints                                                                                                                                                                            |
| ----- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1    | Auth           | `/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`                                                                                                      |
| P2    | Analytics      | `/analytics/overview`, `/analytics/trends`, `/analytics/peaks`, `/analytics/meal-distribution`, `/analytics/food-waste-distribution`                                                     |
| P2    | Monitoring     | `/monitoring/current-session`, `/monitoring/recent-entries`, `/monitoring/device-statuses`                                                                                               |
| P2    | WebSocket      | `WS /ws/dashboard`, `WS /ws/monitoring`                                                                                                                                                  |
| P3    | Analytics      | `/analytics/sustainability-scores`, `/analytics/branch-comparison`                                                                                                                       |
| P3    | Students       | `/students`, `/students/{id}`, `/students/{id}/stats`, `/students/{id}/timeline`, `/students/{id}/food-breakdown`, `/students/{id}/warnings`, `/students/import-csv`, `/students/export` |
| P3    | Waste          | `/waste/entries`                                                                                                                                                                         |
| P3    | Filter Presets | `/filter-presets`                                                                                                                                                                        |
| P4    | Warnings       | `/warnings`, `/warnings/{id}`, `/warnings/export`, `/penalties`, `/escalations`                                                                                                          |
| P4    | Rules          | `/rules`, `/rules/{id}`, `/rules/{id}/test`, `/rules/{id}/simulate`, `/rules/{id}/executions`, `/rules/chains`, `/rules/metadata/*`                                                      |
| P5    | Notifications  | `/notifications`, `/notifications/{id}`, `/notifications/mark-all-read`, `/notifications/preferences`                                                                                    |
| P5    | Reports        | `/reports`, `/reports/generate`, `/reports/{id}`, `/reports/{id}/download`, `/reports/schedules`                                                                                         |
| P5    | Devices        | `/devices`, `/devices/{id}`, `/devices/{id}/health`, `/devices/{id}/history`                                                                                                             |
| P6    | Config         | `/config/{section}`, `/config/institution`, `/config/thresholds`, `/config/meals`, `/config/branches`                                                                                    |
| P6    | Settings       | `/settings/users`, `/settings/security`, `/settings/backups`, `/settings/maintenance`, `/settings/logo`                                                                                  |
| P6    | Audit          | `/audit`, `/audit/{id}`, `/audit/stats`                                                                                                                                                  |
| P6    | Roles          | `/roles`                                                                                                                                                                                 |
| P6    | Templates      | `/templates`                                                                                                                                                                             |

---

## Verification Gates

After each phase, ALL of the following must pass before starting the next:

1. `npm run check` — zero TypeScript errors
2. `npm run dev` — no console errors on page load
3. Browser: `#0b0e11` canvas background — NO light, NO gradient
4. No `box-shadow` on any card/panel (check DevTools)
5. No old tokens (`bg-panel`, `border-line`, `bg-field`, `bg-fresh`, `text-ink` as dark-mode primary) remain
6. All API calls load real data (backend must be running)

---

## Notes for Implementer

1. **Token search-replace pattern:** Before touching any file, run a search for old tokens: `border-line`, `bg-white`, `bg-field`, `bg-fresh`, `text-fresh`, `bg-coral`, `bg-amber`, `bg-slate`, `shadow-soft`, `.surface`, `bg-ink` (when used as near-black page bg in Svelte templates).
2. **Svelte 5 syntax:** The codebase uses Svelte 5 — use `$props()`, `$state()` runes syntax where appropriate. Existing files use Svelte 4 event syntax (`on:click`) — keep consistent with what's there unless migrating.
3. **No reports route:** `src/routes/dashboard/reports/+page.svelte` is the ONLY missing route page. All other 14 pages exist.
4. **Token mapping for migration:**
   - `bg-fresh` → `bg-primary`, `text-fresh` → `text-primary`
   - `bg-coral` → `bg-down`, `text-coral` → `text-down`
   - `bg-amber` → `bg-primary` (warning tone), `text-amber` → `text-primary`
   - `bg-white` → `bg-card`
   - `border-line` → `border-border`
   - `bg-field` → `bg-elevated`
   - `bg-slate-100`, `bg-slate-50` → `bg-elevated`
   - `text-ink` → `text-body` (body text on dark)
   - `.surface` → `.card`
   - `shadow-soft` → remove entirely
   - `bg-ink` (near-black overlay) → `bg-canvas`
   - `ring-fresh` → `ring-primary`
