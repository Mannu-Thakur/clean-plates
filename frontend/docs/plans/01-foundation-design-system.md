# Phase 1 — Foundation, Design System & Auth Shell

**Duration:** ~3 days  
**Depends on:** Nothing — this is the starting phase  
**Required before:** All subsequent phases  
**Pages implemented:** Login (`/login`)  
**Shared deliverables:** Design tokens, layout shell, all primitive UI components, auth store, API client validation

---

## Context & Current State

The frontend scaffold already exists with:
- ✅ SvelteKit 2, Svelte 5, TypeScript, TailwindCSS 3, Chart.js, Lucide icons, Inter font
- ✅ `src/lib/api/client.ts` — full fetch wrapper with JWT attach + auto-refresh
- ✅ `src/lib/api/ws.ts` — `ReconnectingSocket` with exponential backoff
- ✅ `src/lib/api/types.ts` — base type definitions
- ✅ `src/lib/stores/auth.ts` — `AuthStore` with login/logout/initAuth
- ✅ `src/lib/stores/toast.ts` — toast notification store
- ✅ `src/lib/components/layout/DashboardShell.svelte` — collapsible aside nav (NEEDS design token migration)
- ✅ `src/lib/components/layout/navigation.ts` — nav items with RBAC roles
- ✅ `src/lib/components/ui/` — Button, Card, EmptyState, Modal, StatCard, StatusBadge, ToastHost (ALL need token migration)
- ✅ `src/lib/components/charts/ChartCard.svelte`, `Gauge.svelte`
- ✅ `src/lib/utils/format.ts`, `forms.ts`
- ✅ `src/routes/login/+page.svelte` (NEEDS full redesign to dark theme)
- ✅ `src/routes/dashboard/+page.svelte` (NEEDS token migration)
- ✅ `src/routes/dashboard/monitoring/+page.svelte` (NEEDS token migration)
- ⚠️ **PROBLEM:** Current design uses a LIGHT theme (`#edf2f6` canvas, `#ffffff` panels) with gradients — violates the Binance reference
- ⚠️ **PROBLEM:** Current Tailwind tokens (`bg-panel`, `text-fresh`, `border-line`, `bg-field`) do not match Binance system
- ⚠️ **PROBLEM:** `body` has gradient background — must be removed

**This phase migrates everything to the Binance-reference dark system and adds the missing shared components.**

---

## Design Token Reference (Binance-Reference.md)

| Token Name | Hex | Usage |
|------------|-----|-------|
| `canvas` | `#0b0e11` | Page background (flat, NO gradient) |
| `card` | `#1e2329` | All card, panel, modal, aside backgrounds |
| `elevated` | `#2b3139` | Table headers, dropdowns, tooltips, dividers |
| `primary` | `#fcd535` | ALL CTAs, active nav item background/text |
| `primary-hover` | `#f0b90b` | Button active/hover state |
| `primary-disabled` | `#3a3a1f` | Disabled CTA background |
| `ink` | `#181a20` | Text on primary (on yellow buttons) |
| `body` | `#eaecef` | Primary text on dark surfaces |
| `muted` | `#707a8a` | Labels, secondary text, placeholders |
| `muted-strong` | `#929aa5` | Strong muted text, icon hints |
| `border` | `#2b3139` | All borders on dark surfaces (hairline) |
| `up` | `#0ecb81` | Success, online, positive delta, improvement |
| `down` | `#f6465d` | Error, offline, negative delta, warnings |
| `info` | `#3b82f6` | Info badges, help indicators |
| `on-primary` | `#181a20` | Text on yellow — same as `ink` |
| `on-dark` | `#ffffff` | White text |

**NO box-shadows on surfaces. NO gradients anywhere. Flat design only.**

---

## Files to Modify

### 1. `frontend/tailwind.config.ts` — REPLACE all tokens

```typescript
// Full Binance-reference token set
theme: {
  extend: {
    colors: {
      canvas:           '#0b0e11',
      card:             '#1e2329',
      elevated:         '#2b3139',
      primary:          '#fcd535',
      'primary-hover':  '#f0b90b',
      'primary-disabled': '#3a3a1f',
      ink:              '#181a20',
      body:             '#eaecef',
      muted:            '#707a8a',
      'muted-strong':   '#929aa5',
      border:           '#2b3139',
      up:               '#0ecb81',
      down:             '#f6465d',
      info:             '#3b82f6',
      'on-primary':     '#181a20',
      'on-dark':        '#ffffff',
    },
    borderRadius: {
      xs:   '2px',
      sm:   '4px',
      md:   '6px',
      lg:   '8px',
      xl:   '12px',
      pill: '9999px',
    },
    boxShadow: {
      // Only focus rings — NO surface shadows
      'ring-primary': '0 0 0 2px rgba(252,213,53,0.25)',
      'ring-up':      '0 0 0 2px rgba(14,203,129,0.25)',
      'ring-down':    '0 0 0 2px rgba(246,70,93,0.25)',
    },
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
    },
  },
},
```

**Remove:** Old tokens (`panel`, `line`, `field`, `fresh`, `lime`, `amber`, `coral`, `sky`, `soft` shadow)

---

### 2. `frontend/src/app.css` — FULL REPLACEMENT

```css
@import '@fontsource/inter/400.css';
@import '@fontsource/inter/500.css';
@import '@fontsource/inter/600.css';
@import '@fontsource/inter/700.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ── Design Tokens as CSS Custom Properties ─────────── */
:root {
  --color-canvas:           #0b0e11;
  --color-card:             #1e2329;
  --color-elevated:         #2b3139;
  --color-primary:          #fcd535;
  --color-primary-hover:    #f0b90b;
  --color-primary-disabled: #3a3a1f;
  --color-body:             #eaecef;
  --color-muted:            #707a8a;
  --color-muted-strong:     #929aa5;
  --color-border:           #2b3139;
  --color-up:               #0ecb81;
  --color-down:             #f6465d;
  --color-info:             #3b82f6;
  --color-on-primary:       #181a20;
  --color-on-dark:          #ffffff;
}

/* ── Base resets ─────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html { min-width: 320px; color-scheme: dark; }
body {
  margin: 0;
  min-height: 100dvh;      /* dynamic viewport — avoids mobile browser chrome overflow */
  background: #0b0e11;     /* flat canvas — NO gradient */
  color: #eaecef;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  font-feature-settings: 'cv02','cv03','cv04','cv11';
  -webkit-font-smoothing: antialiased;
}
button, input, select, textarea { font: inherit; }
button { letter-spacing: 0; cursor: pointer; }
a { color: inherit; text-decoration: none; }
table { border-collapse: collapse; width: 100%; }
img { display: block; max-width: 100%; }

/* ── Component utilities ─────────────────────────────── */
@layer components {

  /* Buttons */
  .btn-primary {
    @apply inline-flex items-center justify-center gap-2 
           h-10 px-6 rounded-md text-sm font-semibold
           bg-primary text-on-primary
           transition-colors hover:bg-primary-hover
           disabled:bg-primary-disabled disabled:text-muted disabled:cursor-not-allowed;
  }
  .btn-secondary {
    @apply inline-flex items-center justify-center gap-2
           h-10 px-6 rounded-md text-sm font-semibold
           bg-card text-body border border-border
           transition-colors hover:bg-elevated hover:border-muted
           disabled:opacity-50 disabled:cursor-not-allowed;
  }
  .btn-ghost {
    @apply inline-flex items-center justify-center gap-2
           h-10 px-4 rounded-md text-sm font-semibold text-muted
           transition-colors hover:bg-elevated hover:text-body
           disabled:opacity-50 disabled:cursor-not-allowed;
  }
  .btn-danger {
    @apply inline-flex items-center justify-center gap-2
           h-10 px-6 rounded-md text-sm font-semibold
           bg-down text-on-dark
           transition-colors hover:opacity-90
           disabled:opacity-50 disabled:cursor-not-allowed;
  }
  .btn-sm {
    @apply h-8 px-4 text-xs;
  }

  /* Cards & surfaces */
  .card {
    @apply bg-card border border-border rounded-lg;
    /* NO box-shadow */
  }
  .card-elevated {
    @apply bg-elevated border border-border rounded-lg;
  }

  /* Form elements */
  .input-field {
    @apply w-full h-10 px-3 rounded-md text-sm text-body
           bg-elevated border border-border outline-none
           placeholder:text-muted
           focus:border-primary focus:shadow-ring-primary
           disabled:opacity-50 disabled:cursor-not-allowed
           transition-colors;
  }
  .textarea-field {
    @apply w-full px-3 py-2 rounded-md text-sm text-body
           bg-elevated border border-border outline-none
           placeholder:text-muted
           focus:border-primary focus:shadow-ring-primary
           disabled:opacity-50 resize-y min-h-[80px]
           transition-colors;
  }
  .select-field {
    @apply input-field pr-8 appearance-none bg-no-repeat cursor-pointer;
  }

  /* Labels */
  .label {
    @apply text-xs font-semibold uppercase tracking-wide text-muted;
  }
  .form-label {
    @apply block text-sm font-medium text-muted-strong mb-1;
  }

  /* Tables */
  .table-wrapper {
    @apply card overflow-hidden;
  }
  .th {
    @apply px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide 
           text-muted bg-elevated border-b border-border;
  }
  .td {
    @apply px-4 py-3 text-sm text-body border-b border-border;
  }
  .tr-hover {
    @apply hover:bg-elevated/50 transition-colors cursor-pointer;
  }

  /* Badges */
  .badge-up {
    @apply inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-semibold
           bg-up/10 text-up;
  }
  .badge-down {
    @apply inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-semibold
           bg-down/10 text-down;
  }
  .badge-muted {
    @apply inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-semibold
           bg-elevated text-muted border border-border;
  }
  .badge-primary {
    @apply inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-semibold
           bg-primary/10 text-primary;
  }
  .badge-info {
    @apply inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-semibold
           bg-info/10 text-info;
  }

  /* Icon button */
  .icon-btn {
    @apply inline-flex items-center justify-center h-9 w-9 rounded-md
           bg-card border border-border text-muted
           transition-colors hover:bg-elevated hover:text-body
           disabled:opacity-50 disabled:cursor-not-allowed;
  }

  /* Nav */
  .nav-item {
    @apply flex items-center gap-3 h-11 px-3 rounded-md text-sm font-semibold
           text-muted transition-colors hover:bg-elevated hover:text-body;
  }
  .nav-item-active {
    @apply bg-primary text-on-primary;
  }

  /* Divider */
  .divider {
    @apply border-0 border-t border-border my-4;
  }

  /* Status dots */
  .dot-up     { @apply inline-block w-2 h-2 rounded-full bg-up; }
  .dot-down   { @apply inline-block w-2 h-2 rounded-full bg-down; }
  .dot-warn   { @apply inline-block w-2 h-2 rounded-full bg-yellow-500; }
  .dot-muted  { @apply inline-block w-2 h-2 rounded-full bg-muted; }

  /* Skeleton loader */
  .skeleton {
    @apply bg-elevated animate-pulse rounded-md;
  }
}
```

---

### 3. `frontend/src/app.html` — Update meta

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="dark" />
    <meta name="theme-color" content="#0b0e11" />
    <meta name="description" content="CleanPlates — Smart Mess Waste Intelligence Platform" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

---

## Files to Create (New Shared Components)

### 4. `src/lib/utils/constants.ts`

```typescript
export const ROLES = {
  SUPER_ADMIN:       'super_admin',
  INSTITUTION_ADMIN: 'institution_admin',
  MESS_ADMIN:        'mess_admin',
  ANALYTICS_VIEWER:  'analytics_viewer',
  STAFF_OPERATOR:    'staff_operator',
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];

export const MEAL_TYPES = ['breakfast', 'lunch', 'dinner'] as const;
export type MealType = typeof MEAL_TYPES[number];

export const WARNING_LEVELS = ['yellow', 'orange', 'red'] as const;
export type WarningLevel = typeof WARNING_LEVELS[number];

export const STUDENT_STATUSES = ['green', 'yellow', 'orange', 'red'] as const;
export type StudentStatus = typeof STUDENT_STATUSES[number];

export const PENALTY_TYPES = ['points', 'monetary', 'restriction', 'suspension'] as const;
export type PenaltyType = typeof PENALTY_TYPES[number];
```

---

### 5. `src/lib/components/ui/DataTable.svelte`

Generic reusable paginated table component:

```
Props:
  columns: Array<{ key: string, label: string, sortable?: boolean, width?: string }>
  rows: Array<Record<string, unknown>>
  loading: boolean
  page: number
  total: number
  pageSize: number
  onRowClick?: (row) => void
  onSort?: (key: string, dir: 'asc' | 'desc') => void

Slots:
  cell-{key}     — custom cell renderer per column
  row-actions    — action buttons column (right side)
  empty          — empty state override

Features:
  - Skeleton rows (6 rows) while loading = true
  - Striped rows via tr-hover
  - Sortable column headers (clickable, shows ▲▼)
  - Inline row action slot (Edit, Delete icons)
  - Sticky header (position: sticky top: 0)
  - No shadow on table — card border wraps it
```

---

### 6. `src/lib/components/ui/FilterBar.svelte`

Horizontal filter strip used by all list pages:

```
Props:
  filters: Array<{
    type: 'text' | 'select' | 'date-range' | 'multi-select'
    key: string
    label: string
    options?: Array<{ value: string, label: string }>
    placeholder?: string
  }>
  values: Record<string, unknown>
  onFilter: (values: Record<string, unknown>) => void
  onReset?: () => void

Features:
  - Inline reset button (ghost, small)
  - Applies on input/change (debounced 300ms for text)
  - Responsive: wraps to new line on mobile
```

---

### 7. `src/lib/components/ui/Pagination.svelte`

```
Props:
  page: number       (1-indexed)
  total: number      (total items count)
  pageSize: number
  onChange: (page: number) => void

Features:
  - Shows "1–25 of 400" label
  - Prev / Next buttons
  - Page number pills (up to 7 shown, with ellipsis)
  - Disabled state when at boundaries
```

---

### 8. `src/lib/components/ui/ConfirmDialog.svelte`

```
Props:
  open: boolean
  title: string
  message: string
  confirmLabel?: string   (default "Confirm")
  danger?: boolean        (uses btn-danger instead of btn-primary)
  onConfirm: () => void
  onCancel: () => void

Features:
  - Renders inside Modal.svelte
  - Focus trap on open
  - ESC to cancel
```

---

### 9. `src/lib/components/ui/Tabs.svelte`

```
Props:
  tabs: Array<{ id: string, label: string, icon?: Component }>
  active: string
  onChange: (id: string) => void

Features:
  - Underline style tabs (NOT pill — Binance style)
  - Active tab: primary yellow underline, body text
  - Inactive: muted text, hover body text
  - No background change on active (just underline)
```

---

### 10. `src/lib/components/ui/Toggle.svelte`

```
Props:
  value: boolean
  onChange: (value: boolean) => void
  disabled?: boolean
  label?: string

Features:
  - Track: elevated bg when off, primary when on
  - Thumb: white circle
  - Smooth CSS transition
  - Accessible: role="switch", aria-checked
```

---

### 11. `src/lib/components/ui/FormField.svelte`

Wrapper for all form inputs with label + error:

```
Props:
  label: string
  error?: string
  required?: boolean
  hint?: string

Slot: default (input-field, select-field, etc.)

Features:
  - Shows form-label above slot
  - Shows error text in text-down color below
  - Required asterisk (*) in text-down
```

---

### 12. `src/lib/components/ui/SearchInput.svelte`

```
Props:
  value: string
  placeholder?: string
  onSearch: (value: string) => void   (debounced 300ms)
  onClear?: () => void

Features:
  - Search icon left inside input
  - Clear (×) button when value non-empty
  - Auto-focuses on mount if autofocus prop set
  - Uses input-field class
```

---

### 13. `src/lib/components/ui/DateRangePicker.svelte`

```
Props:
  start: string | null   (ISO date)
  end: string | null
  onChange: (start: string, end: string) => void
  presets?: Array<{ label: string, days: number }>  (e.g. "Last 7d", "Last 30d")

Features:
  - Two native date inputs (start + end)
  - Preset buttons above inputs
  - Validates start <= end
  - Card dropdown-style container
```

---

### 14. `src/lib/components/ui/SelectField.svelte`

```
Props:
  value: string
  options: Array<{ value: string, label: string }>
  placeholder?: string
  disabled?: boolean
  onChange: (value: string) => void

Features:
  - Uses native <select> with select-field class
  - Custom caret icon via Tailwind bg-image trick
  - Full-width by default
```

---

### 15. `src/lib/components/ui/FileUpload.svelte`

```
Props:
  accept: string          (e.g. '.csv', '.json')
  maxSizeMb?: number      (default 10)
  onSelect: (file: File) => void
  label?: string

Features:
  - Drag-and-drop zone with dashed border
  - Click to browse
  - File size validation with toast error
  - Shows selected filename with clear button
  - Progress state when uploading (external prop)
```

---

### 16. `src/lib/components/layout/PageHeader.svelte`

Reusable page header used by every dashboard page:

```
Props:
  label: string          (small uppercase, text-muted — e.g. "Waste Intelligence")
  title: string          (large heading)
  description?: string

Slots:
  actions                (right side — buttons, period selectors, etc.)

Features:
  - Responsive: actions stack on mobile
  - Consistent spacing across all pages
```

---

## Files to Migrate (Dark Theme)

### 17. Migrate `DashboardShell.svelte`

Replace all old token classes:
- `bg-white` → `bg-card`
- `border-line` → `border-border`  
- `text-ink` → `text-body`
- `bg-slate-100` → `bg-elevated`
- `bg-fresh text-white` (active nav) → `bg-primary text-on-primary`
- `bg-slate-50` → `bg-elevated`
- `border-t border-line` → `border-t border-border`
- `bg-white/92` (header) → `bg-canvas/95`
- Logout button: secondary style
- Collapsed width: 76px (icon-only), expanded: 260px
- Nav item: `.nav-item`, active: `.nav-item-active`

---

### 18. Migrate All Existing UI Components

| Component | Key Changes |
|-----------|-------------|
| `Button.svelte` | Use `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger` + `.btn-sm` |
| `Card.svelte` | Use `.card` class (no shadow) |
| `StatCard.svelte` | Use `.card`, `text-body`, tone=good→`text-up`, tone=bad→`text-down`, tone=warn→`text-primary` |
| `StatusBadge.svelte` | Use `.badge-up`, `.badge-down`, `.badge-muted`, `.badge-primary` |
| `Modal.svelte` | Overlay: `bg-canvas/80` backdrop; modal: `.card` with `max-w-lg` |
| `EmptyState.svelte` | Text: `text-muted`, icon: `text-muted` |
| `ToastHost.svelte` | Success toast: `bg-card border-up/30`; error: `bg-card border-down/30` |
| `ChartCard.svelte` | `.card`, Chart.js dark theme colors (canvas, grid, labels) |
| `Gauge.svelte` | Dark gauge SVG |

---

### 19. Chart.js Dark Theme Defaults

Create `src/lib/utils/chartDefaults.ts`:

```typescript
// Called once in root layout to set Chart.js global defaults for dark theme
import { Chart, defaults } from 'chart.js';

export function applyDarkChartDefaults() {
  defaults.color = '#707a8a';           // muted text for labels
  defaults.borderColor = '#2b3139';    // border for grid lines
  defaults.font.family = 'Inter, sans-serif';
  defaults.plugins.legend.labels.color = '#eaecef';
  defaults.scale.grid.color = '#2b3139';
  defaults.scale.ticks.color = '#707a8a';
}

// Standard dataset colors
export const CHART_COLORS = {
  primary: '#fcd535',
  up:      '#0ecb81',
  down:    '#f6465d',
  info:    '#3b82f6',
  muted:   '#707a8a',
  series:  ['#fcd535', '#0ecb81', '#3b82f6', '#f6465d', '#707a8a', '#929aa5'],
};
```

Call `applyDarkChartDefaults()` in `src/routes/+layout.svelte` on mount.

---

### 20. `src/routes/login/+page.svelte` — Full Redesign

**Layout:** Two-column on desktop (left brand panel + right form), single column on mobile.

**Left panel (hidden on mobile):**
- Full height, `bg-card` background
- CleanPlates logo (CP monogram) in `bg-primary text-on-primary` circle
- Product name in `text-body`, tagline in `text-muted`
- Stats strip: total waste tracked, institutions, devices — `text-primary` numbers

**Right panel (form):**
- `bg-canvas` background (or `bg-card` on mobile)
- Card for the form: `card p-8 max-w-sm w-full`
- `<h1>` "Welcome back"
- Email input: `input-field`
- Password input with show/hide toggle: `input-field` + icon button inside
- Remember Me: custom `Toggle.svelte` or native checkbox with label
- Sign In: `btn-primary w-full`
- Forgot Password link: `text-primary text-sm hover:underline`
- Error state: `badge-down` alert box above form
- Loading: spinner inside button, button disabled

**API calls:**
- `POST /api/v1/auth/login` → `AuthStore.login(email, password, rememberMe)`
- `GET /api/v1/auth/me` → load user on refresh
- On success: navigate to `/dashboard` (admin roles) or `/dashboard/monitoring` (staff_operator)
- On 401: inline error
- On 403: "Account locked" message

---

## Shared Store Additions

### 21. `src/lib/stores/toast.ts` — Verify API

Current `notify(msg, type)` must support:
- `notify(message, 'success' | 'error' | 'warning' | 'info')`
- Auto-dismiss after 4s
- Max 5 toasts visible
- Stack from bottom-right

---

## Verification Checklist

- [ ] `npm run dev` starts without errors
- [ ] `npm run check` passes with zero TypeScript errors
- [ ] Browser shows `#0b0e11` canvas — NO light background, NO gradient
- [ ] Login page renders correctly with dark form
- [ ] Successful login redirects to `/dashboard`
- [ ] Failed login shows error badge
- [ ] Auth token stored in localStorage (rememberMe=true) or sessionStorage
- [ ] Token auto-refresh works on 401
- [ ] Nav aside collapses to icon-only (76px) on toggle
- [ ] Active nav item shows primary yellow background
- [ ] All old tokens (`bg-panel`, `text-fresh`, `border-line`, `bg-field`) are gone — search and confirm
- [ ] No box-shadows on cards or panels in devtools
- [ ] Chart.js charts use dark background and muted axis colors
- [ ] All new shared components render in Storybook/test harness

---

## Exit Criteria

✅ Binance dark token system committed and resolving in every component  
✅ All old conflicting token names removed  
✅ Login page fully functional, dark themed  
✅ DashboardShell collapsible nav working on dark theme  
✅ All 20 shared component building blocks ready for Phase 2  
✅ No gradients or box-shadows anywhere  
✅ `npm run check` passes cleanly
