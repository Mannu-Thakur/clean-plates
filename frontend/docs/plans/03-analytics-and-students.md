# Phase 3 — Analytics Suite & Student Intelligence

**Duration:** ~5 days  
**Depends on:** Phase 1 (tokens, components), Phase 2 (ChartCard patterns)  
**Required before:** Phase 4 (DataTable, FilterBar, Pagination reused)  
**Pages implemented:**
- Page 04: `/dashboard/analytics` — Full Analytics Suite (tabbed)
- Page 05: `/dashboard/students` — Student List & Management
- Page 06: `/dashboard/students/[id]` — Student Intelligence Profile

---

## Page 04 — Analytics Suite (`/dashboard/analytics`)

### Route: `src/routes/dashboard/analytics/+page.svelte`
**Access:** super_admin, institution_admin, mess_admin, analytics_viewer (read-only)

### Layout — Tabbed Interface

```
┌───────────────────────────────────────────────────────────┐
│  PageHeader: "Analytics"    [Date Range] [Branch ▼] [↓]  │
├───────────────────────────────────────────────────────────┤
│  [Overview] [Trends] [Branch] [Sustainability] [Heatmap]  │← Tabs
├───────────────────────────────────────────────────────────┤
│  Tab content (varies per tab)                             │
└───────────────────────────────────────────────────────────┘
```

### Global Filter Bar (persists across all tabs)

Component: `FilterBar.svelte` with:
- `DateRangePicker` (start, end dates)
- `SelectField` Branch filter (options from `GET /api/v1/config/branches`)
- `SelectField` Meal filter (All / Breakfast / Lunch / Dinner)
- "Save as Preset" button → opens Modal to name + save via `POST /api/v1/filter-presets`
- "Load Preset" button → dropdown of saved presets from `GET /api/v1/filter-presets`
- Reset filters button

#### Filter Preset Store: `src/lib/stores/filterPreset.ts`
```typescript
// fetchPresets()  → GET /api/v1/filter-presets
// savePreset(name, filters) → POST /api/v1/filter-presets
// deletePreset(id) → DELETE /api/v1/filter-presets/{id}
```

---

### Tab 1: Overview

**API Calls:**
- `GET /api/v1/analytics/overview?period=...&date_from=...&date_to=...&branch=...`

**Components:**
- 4 large StatCards: Total Waste, Avg per Student, Reduction %, Active Students
- 2-column chart grid: Line + Bar (same as dashboard but with filter context)

---

### Tab 2: Trends

**API Calls:**
- `GET /api/v1/analytics/trends?type=weekly` → weekly line chart
- `GET /api/v1/analytics/trends?type=monthly_comparison` → grouped bar
- `GET /api/v1/analytics/trends?type=daily_pattern` → 7-day day-of-week breakdown
- `GET /api/v1/analytics/peaks?...` → peak meal and peak hour

**Components:**
- 3 ChartCards stacked (full-width then 2-col)
- Peak stats row: 3 StatCards (Peak Meal, Peak Hour, Peak Weekday)

---

### Tab 3: Branch Comparison

> **Note:** There is no `/api/v1/analytics/branch-comparison` endpoint in the backend. Derive branch data client-side by calling `GET /api/v1/analytics/overview` once per branch in a `Promise.all()` (using the `branch=` filter param), then aggregate the results. This tab should be marked **"Coming Soon"** or hidden behind a feature flag until the backend adds a dedicated endpoint.

**API Calls (workaround):**
- `GET /api/v1/analytics/overview?branch={branchCode}&date_from=...&date_to=...` — called per branch in parallel

**Components:**
- Grouped bar chart: one bar per branch, side-by-side comparison (derived from parallel overview calls)
- Branch table below: DataTable with columns [Branch, Total Waste, Avg/Student, Active Students]
- No export available (no backend endpoint); hide Export button for this tab

---

### Tab 4: Sustainability Scores

**API Calls:**
- `GET /api/v1/analytics/sustainability?branch=...&year=...&hostel=...&status=...`

**Components:**
- Score gauge (large center): institutional sustainability score (0–100)
- Breakdown: 4 metric contributors as progress bars
  - Weight reduction trend
  - Zero-waste entries %
  - Warning resolution rate
  - Student compliance rate
- Trend chart: sustainability score over time (30 days line chart)
- Leaderboard table: top 10 students by sustainability score (DataTable)

---

### Tab 5: Heatmap

**API Calls:**
- `GET /api/v1/analytics/trends?type=daily_pattern&...` — returns 7-day breakdown
  - **Note:** There is no dedicated `/analytics/heatmap` endpoint. Derive the 7×24 heatmap grid client-side by transforming the `daily_pattern` trend data. Map each day's hourly entry counts into a grid of opacity levels.

**Components:**
- 7×24 grid heatmap: rows = days of week, columns = hours of day (derived from `daily_pattern` data)
- Cell color: `bg-canvas` (0) → `bg-primary/20` → `bg-primary/60` → `bg-primary` (max)
- No external heatmap library — pure CSS grid with inline opacity levels
- Tooltip on hover: exact waste amount
- Legend: gradient strip with min/max labels

**Client-side derivation:**
```typescript
// Transform TrendData into heatmap grid
function buildHeatmapGrid(trendData: TrendData): number[][] {
  // 7 rows (days) x 24 cols (hours), default 0
  const grid = Array.from({ length: 7 }, () => new Array(24).fill(0));
  // Fill from daily_pattern data — each TrendPoint has label = "Mon 09:00" etc.
  trendData.data?.forEach(p => {
    const [dayStr, hourStr] = p.label.split(' ');
    const dayIdx = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].indexOf(dayStr);
    const hour = parseInt(hourStr?.split(':')[0] ?? '0', 10);
    if (dayIdx >= 0 && hour >= 0) grid[dayIdx][hour] = p.value;
  });
  return grid;
}
```

---

### API Types (add to `src/lib/api/types.ts`)

```typescript
export interface TrendPoint { label: string; value: number; }
export interface TrendData {
  data?: TrendPoint[];
  current_label?: string;
  previous_label?: string;
  current_data?: TrendPoint[];
  previous_data?: TrendPoint[];
}
export interface PeakData {
  peak_hour?: number | null;
  peak_meal?: string | null;
  peak_weekday?: string | null;
}
export interface SustainabilityScore {
  overall_score: number;
  reduction_score: number;
  compliance_score: number;
  zero_waste_score: number;
  resolution_score: number;
  trend: TrendPoint[];
}
export interface BranchStat {
  branch_code: string;
  branch_name: string;
  total_waste_grams: number;
  avg_per_student: number;
  reduction_pct: number | null;
  active_students: number;
}
export interface FilterPreset {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  created_at: string;
}
```

---

## Page 05 — Student List (`/dashboard/students`)

### Route: `src/routes/dashboard/students/+page.svelte`
**Access:** super_admin, institution_admin, mess_admin, analytics_viewer (read-only)

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  PageHeader: "Students"           [Import CSV] [Export] [+]  │
├──────────────────────────────────────────────────────────────┤
│  FilterBar: [Search] [Status▼] [Branch▼] [Warning▼] [Reset] │
├──────────────────────────────────────────────────────────────┤
│  DataTable (paginated, sortable)                             │
│  + row actions: [View] [Edit] [Warn]                        │
├──────────────────────────────────────────────────────────────┤
│  Pagination                                                  │
└──────────────────────────────────────────────────────────────┘
```

### API Calls

| Action | Endpoint |
|--------|----------|
| List students | `GET /api/v1/students?page=&size=&status=&branch=&hostel=&year=&sort=&order=` |
| Create warning | `POST /api/v1/students/{id}/warnings` |
| Update mapping | `PATCH /api/v1/students/{id}/map` |
| Import mappings (CSV) | `POST /api/v1/students/import-mapping` (multipart file upload, field: `csv_file`) |
| Export CSV | `GET /api/v1/students/export` → `api.download()` |
| View student | Navigate to `/dashboard/students/{id}` |

### DataTable Columns

| Column | Field | Sortable | Width |
|--------|-------|----------|-------|
| Name | `name` | Yes | 200px |
| Roll No. | `student_id` | Yes | 120px |
| Branch | `branch` | Yes | 100px |
| Status | `status` (badge) | Yes | 100px |
| Warnings | `warning_count` | Yes | 90px |
| Penalties | `penalty_count` | Yes | 90px |
| Last Waste | `last_waste_at` | Yes | 130px |
| Mapped | `is_mapped` (badge) | No | 80px |
| Actions | — | No | 100px |

### Status Badge Mapping

| Student Status | Badge Class | Label |
|---------------|-------------|-------|
| `green` | `badge-up` | ✓ Good |
| `yellow` | `badge-primary` | ⚠ Warning |
| `orange` | Custom `text-orange-400 bg-orange-400/10` | ⚠ At Risk |
| `red` | `badge-down` | ✕ Penalty |

### Import CSV Modal

Triggered by "Import CSV" button:
1. `FileUpload.svelte` — accepts `.csv` only, max 5MB
2. Preview: first 5 rows shown in mini table
3. Confirm → `api.upload('/students/import-mapping', 'csv_file', file)`
4. Result: `ImportResultSchema` → show success/error counts in modal
5. On success: refetch student list

### Quick Warn Modal

"Warn" action button → modal with:
- Student name (read-only)
- Level selector: `SelectField` (yellow / orange / red)
- Message textarea
- Food items multiselect (optional)
- Confirm → `POST /api/v1/students/{id}/warnings`

### Store: `src/lib/stores/students.ts`

```typescript
// State:
//   students: Student[]
//   total: number
//   page: number
//   filters: StudentFilters
//   loading: boolean

// Actions:
//   fetchStudents(filters?)
//   importCsv(file: File)
//   exportCsv(filters?)
//   createWarning(studentId, data)
//   reset()
```

### API Types

```typescript
export interface Student {
  id: string;
  name: string;
  student_id: string;       // roll number
  branch: string;
  email?: string;
  phone?: string;
  status: 'green' | 'yellow' | 'orange' | 'red';
  warning_count: number;
  penalty_count: number;
  is_mapped: boolean;
  last_waste_at?: string;
  sustainability_score?: number;
  created_at: string;
}
export interface StudentMapping {
  student_id: string;   // face/card ID
  mess_id?: string;
  is_active: boolean;
}
export interface ImportResult {
  total: number;
  created: number;
  updated: number;
  errors: Array<{ row: number; message: string }>;
}
export interface StudentFilters {
  // Note: no free-text search param exists in the backend — search is client-side only
  status?: string;          // alias: status_filter in backend
  branch?: string;
  hostel?: string;          // added — supported by backend
  year?: number;            // added — supported by backend (1-4)
  // warning_status removed — does not exist in backend
  page?: number;
  size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}
```

---

## Page 06 — Student Intelligence Profile (`/dashboard/students/[id]`)

### Route: `src/routes/dashboard/students/[id]/+page.svelte`
**Access:** super_admin, institution_admin, mess_admin, analytics_viewer (read-only)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back to Students     Student: Rahul Gupta                  │
│  [Roll: 21CSE045]  [Branch: CSE]  [Status: badge]  [Warn]     │
├─────────────┬──────────────────────────────────────────────────┤
│ Profile     │  [Overview] [Timeline] [Food] [Warnings] [ML]   │
│ Card        ├──────────────────────────────────────────────────┤
│             │  Tab content                                     │
│             │                                                  │
│ Sustainability│                                                │
│ Score Gauge │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### API Calls

| Endpoint | Used For |
|----------|----------|
| `GET /api/v1/students/{id}` | Profile data |
| `GET /api/v1/students/{id}/stats` | Overview tab |
| `GET /api/v1/students/{id}/timeline` | Timeline tab |
| `GET /api/v1/students/{id}/food-breakdown` | Food tab |
| `GET /api/v1/students/{id}/warnings` | Warnings tab |
| `GET /api/v1/students/{id}/meal-pattern` | Timeline tab |
| `GET /api/v1/students/{id}/improvement` | Overview tab |
| `GET /api/v1/students/{id}/history` | Timeline tab |
| `POST /api/v1/students/{id}/warnings` | Manual warn button |
| `POST /api/v1/students/bulk/warn` | Bulk warn (admin) — body: `BulkWarnSchema` (list of student IDs + level + message) |

### Left Panel — Profile Card

```
.card p-5 (sticky while scrolling tabs)

┌────────────────────────────┐
│  [Avatar/Monogram]         │
│  Name: bold, body text     │
│  Roll: muted               │
│  Branch badge              │
│  Email | Phone             │
│  ─────────────────         │
│  Status: badge             │
│  Warnings: number          │
│  Penalties: number         │
│  ─────────────────         │
│  Sustainability            │
│  [Gauge component]         │
│  Score: 72/100             │
│  ─────────────────         │
│  Mapped: badge             │
│  Last Active: date         │
│  [Warn] [Edit Mapping]     │
└────────────────────────────┘
```

### Tab: Overview

- 4 StatCards: Total Waste, Avg per Meal, Best Session, Worst Session
- Line chart: waste trend last 30 days (`improvement_trend`)
- Mini stat: streak (consecutive days under limit — computed from stats)
- "Improvement: +12%" badge if positive trend

### Tab: Timeline

- Chronological list of waste entries
- Date-grouped (today, yesterday, last week, older)
- Each entry: `card p-3 mb-2`
  - Meal badge + time
  - Weight in `text-primary font-mono`
  - Food items as `badge-muted` pills
  - Plate image thumbnail (if `plate_image_path`) → click opens image modal
  - Severity dot left border
- Load more pagination (not infinite scroll)
- Meal pattern heatmap at top: mini 7×3 grid (days × meals) colored by waste level

### Tab: Food Breakdown

- Doughnut chart: top 5 food items by waste weight
- DataTable: all food items with columns [Food Item, Total Waste, Entries, Avg/Entry, % of Total]
- Export food breakdown CSV button

### Tab: Warnings & Penalties

- Two sub-sections stacked:
  1. **Warnings** — DataTable: [Date, Level, Reason, Rule, Status, Actions]
     - Status: active→`badge-primary`, resolved→`badge-up`, escalated→`badge-down`
     - Action: Resolve button (if active, admin only)
  2. **Penalties** — DataTable: [Date, Type, Amount, Reason, Status]
     - Status: active→`badge-down`, paid→`badge-up`, waived→`badge-muted`

### Tab: ML Data (if plate images exist)

- Grid of plate image thumbnails from `/static/uploads/`
- Each card: date, meal, weight, confidence score
- Click to expand image in modal

### Route Parameter Loading

```typescript
// src/routes/dashboard/students/[id]/+page.ts
export const load = async ({ params }) => {
  return { studentId: params.id };
};

// In +page.svelte: onMount fetches all data using studentId
```

### New API Types

```typescript
export interface StudentStats {
  total_waste_grams: number;
  avg_per_meal_grams: number;
  best_session_grams: number;
  worst_session_grams: number;
  zero_waste_days: number;
  improvement_trend_pct: number | null;
  sustainability_score: number;
  streak_days: number;
}
export interface WasteEntry {
  id: string;
  student_id?: string;
  device_id?: string;
  weight_grams: number;
  meal_type: string;
  food_items: string[];
  severity: 'low' | 'medium' | 'high';
  plate_image_path?: string;
  timestamp: string;
  session_id?: string;
  confidence_score?: number;
}
export interface FoodBreakdown {
  food_name: string;
  total_grams: number;
  entry_count: number;
  avg_per_entry: number;
  percentage: number;
}
export interface StudentWarning {
  id: string;
  level: 'yellow' | 'orange' | 'red';
  reason: string;
  rule_name?: string;
  status: 'active' | 'resolved' | 'escalated';
  created_at: string;
  resolved_at?: string;
}
export interface StudentPenalty {
  id: string;
  penalty_type: string;
  amount?: number;
  reason: string;
  status: 'active' | 'paid' | 'waived';
  created_at: string;
}
```

---

## Shared Components for this Phase

### `src/lib/components/students/StudentStatusBadge.svelte`
Specialized badge for student status (green/yellow/orange/red) with dot + label.

### `src/lib/components/students/WasteEntryCard.svelte`
Reusable entry card used in monitoring feed AND student timeline.

### `src/lib/components/students/MealPatternGrid.svelte`
7×3 mini heatmap grid (days × meal types) — coloured cells by waste level.

---

## Verification Checklist

**Analytics page:**
- [ ] Tab switching works, each tab loads correct data
- [ ] Date range filter applies to all API calls
- [ ] Branch filter applies
- [ ] Save/Load preset works via `/filter-presets` API
- [ ] Heatmap renders as CSS grid with correct intensity colors
- [ ] Branch comparison table sortable
- [ ] Sustainability gauge animates to correct score
- [ ] Export CSV triggers download

**Student list page:**
- [ ] Table loads paginated students
- [ ] Search debounces and filters
- [ ] Status filter works
- [ ] Branch filter works
- [ ] Import CSV modal — file upload, preview, confirm, success/error counts
- [ ] Export CSV triggers download
- [ ] Row click navigates to `/dashboard/students/{id}`
- [ ] Quick Warn modal submits correctly

**Student profile page:**
- [ ] Profile card shows correct data
- [ ] Sustainability gauge renders
- [ ] All tabs load correct data from their respective endpoints
- [ ] Timeline shows date-grouped entries
- [ ] Plate image thumbnails load from `/static/uploads/`
- [ ] Warnings/penalties sub-tables render correctly
- [ ] Admin can resolve warnings (button visible, fires API)
- [ ] Food breakdown doughnut + table render

---

## Exit Criteria

✅ All three pages fully functional with live API data  
✅ DataTable, FilterBar, Pagination components reusable for Phase 4  
✅ Student profile with all 5 tabs working  
✅ Filter presets save/load working  
✅ `npm run check` passing
