<script lang="ts">
  import { onMount } from 'svelte';
  import {
    BarChart3,
    Download,
    Flame,
    Leaf,
    RefreshCw,
    TrendingUp
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FilterBar, {
    type FilterConfig
  } from '$lib/components/ui/FilterBar.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs from '$lib/components/ui/Tabs.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { grams, number, pct, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';
  import {
    STUDENT_STATUSES,
    MEAL_TYPES,
    PERIOD_OPTIONS
  } from '$lib/utils/constants';

  type AnalyticsTab =
    | 'trends'
    | 'heatmap'
    | 'contributors'
    | 'improvement'
    | 'sustainability';
  type TrendGranularity = 'daily' | 'weekly' | 'semester';
  type TrendPoint = { label: string; value: number };
  type TrendPayload = { type?: string; data?: TrendPoint[] };
  type Contributor = {
    rank: number;
    student_id: string;
    device_id: string;
    name: string | null;
    avg_waste_grams: number;
    total_waste_grams: number;
    violation_count: number;
    status: string;
  };
  type ContributorPayload = { period: string; data: Contributor[] };
  type Improvement = {
    student_id: string;
    device_id: string;
    name: string | null;
    current_avg_grams: number;
    previous_avg_grams: number;
    improvement_pct: number;
    direction: string;
  };
  type Sustainability = {
    excellent_count: number;
    good_count: number;
    average_count: number;
    poor_count: number;
    overall_avg: number;
  };
  type HeatmapPoint = {
    weekday?: string;
    day?: string;
    hour?: number;
    value?: number;
    avg_grams?: number;
    total_grams?: number;
    grams?: number;
  };
  type HeatmapPayload = {
    data?: HeatmapPoint[];
    heatmap_data?: HeatmapPoint[];
    peak_hour?: number | null;
    peak_meal?: string | null;
    peak_weekday?: string | null;
    peak_hour_grams?: number | null;
  };
  type AnalyticsFilterValues = {
    date: { start: string | null; end: string | null };
    branch: string;
    year: string;
    hostel: string;
    meal_type: string;
    food: string;
    status: string;
  };

  const weekdays = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
  ];
  const hours = Array.from({ length: 24 }, (_, index) => index);
  const analyticsTabs = [
    { id: 'trends', label: 'Trends', icon: TrendingUp },
    { id: 'heatmap', label: 'Heatmap', icon: Flame },
    { id: 'contributors', label: 'Top Contributors', icon: BarChart3 },
    { id: 'improvement', label: 'Improvement', icon: TrendingUp },
    { id: 'sustainability', label: 'Sustainability', icon: Leaf }
  ];
  const filterConfig: FilterConfig[] = [
    { key: 'date', label: 'Date range', type: 'date-range' },
    { key: 'branch', label: 'Branch', type: 'text', placeholder: 'CSE' },
    {
      key: 'year',
      label: 'Year',
      type: 'select',
      options: [
        { value: '', label: 'All years' },
        { value: '1', label: 'Year 1' },
        { value: '2', label: 'Year 2' },
        { value: '3', label: 'Year 3' },
        { value: '4', label: 'Year 4' }
      ]
    },
    { key: 'hostel', label: 'Hostel', type: 'text', placeholder: 'A Block' },
    {
      key: 'meal_type',
      label: 'Meal',
      type: 'select',
      options: [
        { value: '', label: 'All meals' },
        ...MEAL_TYPES.map((m) => ({ value: m, label: titleCase(m) }))
      ]
    },
    { key: 'food', label: 'Food', type: 'text', placeholder: 'Rice' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: '', label: 'All statuses' },
        ...STUDENT_STATUSES.map((s) => ({ value: s, label: titleCase(s) }))
      ]
    }
  ];

  let activeTab: AnalyticsTab = 'trends';
  let period = '30d';
  let trendGranularity: TrendGranularity = 'weekly';
  let filters = defaultFilters();
  let loading = true;
  let refreshing = false;
  let error = '';
  let trendData: TrendPayload = { data: [] };
  let heatmap: HeatmapPoint[] = [];
  let heatmapSource = 'daily_pattern';
  let peakSignals: HeatmapPayload = {};
  let topContributors: Contributor[] = [];
  let improvements: Improvement[] = [];
  let sustainability: Sustainability = {
    excellent_count: 0,
    good_count: 0,
    average_count: 0,
    poor_count: 0,
    overall_avg: 0
  };

  $: filterRecord = filters as unknown as Record<string, unknown>;
  $: trendPoints = trendData.data ?? [];
  $: maxHeat = Math.max(1, ...heatmap.map((point) => heatValue(point)));
  $: totalStudents =
    sustainability.excellent_count +
    sustainability.good_count +
    sustainability.average_count +
    sustainability.poor_count;

  function defaultFilters(): AnalyticsFilterValues {
    return {
      date: { start: null, end: null },
      branch: '',
      year: '',
      hostel: '',
      meal_type: '',
      food: '',
      status: ''
    };
  }

  function normalizeFilters(
    values: Record<string, unknown>
  ): AnalyticsFilterValues {
    const date = (values.date ?? {}) as { start?: string; end?: string };
    return {
      date: {
        start: date.start ?? null,
        end: date.end ?? null
      },
      branch: String(values.branch ?? ''),
      year: String(values.year ?? ''),
      hostel: String(values.hostel ?? ''),
      meal_type: String(values.meal_type ?? ''),
      food: String(values.food ?? ''),
      status: String(values.status ?? '')
    };
  }

  function trendType() {
    return trendGranularity;
  }

  function analyticsQuery(extra: Record<string, string | number> = {}) {
    return {
      period,
      date_from: filters.date.start ?? undefined,
      date_to: filters.date.end ?? undefined,
      branch: filters.branch,
      year: filters.year ? Number(filters.year) : undefined,
      hostel: filters.hostel,
      meal_type: filters.meal_type,
      food: filters.food,
      status: filters.status,
      ...extra
    };
  }

  function sustainabilityQuery() {
    return {
      branch: filters.branch,
      year: filters.year ? Number(filters.year) : undefined,
      hostel: filters.hostel,
      status: filters.status
    };
  }

  function heatRows(payload: HeatmapPayload): HeatmapPoint[] {
    return payload.heatmap_data ?? payload.data ?? [];
  }

  function heatValue(point: HeatmapPoint) {
    return Number(
      point.avg_grams ?? point.value ?? point.total_grams ?? point.grams ?? 0
    );
  }

  function heatPoint(weekday: string, hour: number) {
    return heatmap.find(
      (point) =>
        String(point.weekday ?? point.day ?? '').toLowerCase() ===
          weekday.toLowerCase() && Number(point.hour) === hour
    );
  }

  function heatColor(value: number) {
    const alpha = Math.max(0.08, Math.min(0.95, value / maxHeat));
    return `background-color: rgba(252, 213, 53, ${alpha.toFixed(2)})`;
  }

  function applyFilters(values: Record<string, unknown>) {
    filters = normalizeFilters(values);
    loadAnalytics();
  }

  function resetFilters() {
    period = '30d';
    filters = defaultFilters();
    loadAnalytics(true);
  }

  async function loadAnalytics(fullLoad = false) {
    if (fullLoad) loading = true;
    else refreshing = true;
    error = '';
    try {
      const [
        trends,
        dailyPattern,
        peaks,
        contributors,
        improvementData,
        sustainabilityData
      ] = await Promise.all([
        api.get<TrendPayload>('/analytics/trends', {
          ...analyticsQuery({ type: trendType() })
        }),
        api
          .get<HeatmapPayload>('/analytics/trends', {
            ...analyticsQuery({ type: 'daily_pattern' })
          })
          .catch(() => ({ data: [] })),
        api.get<HeatmapPayload>('/analytics/peaks', analyticsQuery()),
        api.get<ContributorPayload>('/analytics/top-waste-contributors', {
          ...analyticsQuery(),
          limit: 15
        }),
        api.get<Improvement[]>('/analytics/improvement-tracking', {
          ...analyticsQuery()
        }),
        api.get<Sustainability>(
          '/analytics/sustainability',
          sustainabilityQuery()
        )
      ]);

      trendData = trends;
      peakSignals = peaks;
      heatmap = heatRows(dailyPattern);
      heatmapSource = 'daily_pattern';
      if (heatmap.length === 0 && heatRows(peaks).length > 0) {
        heatmap = heatRows(peaks);
        heatmapSource = 'peaks';
      }
      topContributors = contributors.data ?? [];
      improvements = improvementData;
      sustainability = sustainabilityData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load analytics';
    } finally {
      loading = false;
      refreshing = false;
    }
  }

  async function exportAnalytics(format: 'pdf' | 'csv' | 'excel') {
    try {
      await api.post('/reports/generate', {
        type: 'analytics',
        format,
        date_from: filters.date.start,
        date_to: filters.date.end,
        filters: analyticsQuery()
      });
      notify(`${titleCase(format)} analytics report queued.`, 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not queue export.',
        'error'
      );
    }
  }

  onMount(() => loadAnalytics(true));
</script>

<svelte:head>
  <title>Analytics | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Deep analytics"
  title="Trends, waste patterns, and student performance"
  description="Phase 3 analytics across trend cadence, hourly heatmaps, top contributors, improvement tracking, and sustainability scores."
>
  <svelte:fragment slot="actions">
    <select
      class="select-field"
      bind:value={period}
      on:change={() => loadAnalytics()}
      id="select-analytics-period"
    >
      {#each PERIOD_OPTIONS as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
      <option value="all">All</option>
    </select>
    <Button
      variant="secondary"
      on:click={() => loadAnalytics()}
      id="btn-refresh-analytics"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={() => exportAnalytics('csv')}
      id="btn-export-analytics-csv"
    >
      <Download size={16} />
      CSV
    </Button>
    <Button on:click={() => exportAnalytics('pdf')} id="btn-export-analytics">
      <Download size={16} />
      PDF
    </Button>
  </svelte:fragment>
</PageHeader>

<FilterBar
  filters={filterConfig}
  values={filterRecord}
  onFilter={applyFilters}
  onReset={resetFilters}
/>

{#if refreshing}
  <div class="mt-2 h-0.5 w-full animate-pulse rounded-full bg-primary/40"></div>
{/if}

<div class="mt-5">
  <Tabs
    tabs={analyticsTabs}
    active={activeTab}
    onChange={(id) => (activeTab = id as AnalyticsTab)}
  />
</div>

{#if error}
  <div class="mt-5">
    <Card title="Analytics unavailable" description={error}>
      <Button on:click={() => loadAnalytics(true)}>Retry</Button>
    </Card>
  </div>
{:else if loading}
  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <div class="skeleton h-80"></div>
    <div class="skeleton h-80"></div>
  </div>
{:else if activeTab === 'trends'}
  <div class="mt-5 space-y-5">
    <Card
      title="Trend cadence"
      description="Line chart can pivot between daily, weekly, and monthly views."
    >
      <div class="flex flex-wrap gap-2">
        {#each ['daily', 'weekly', 'semester'] as cadence}
          <button
            class={`h-9 rounded-md px-4 text-sm font-semibold transition-colors ${
              trendGranularity === cadence
                ? 'bg-primary text-ink'
                : 'bg-elevated text-muted hover:text-body'
            }`}
            type="button"
            on:click={() => {
              trendGranularity = cadence as TrendGranularity;
              loadAnalytics();
            }}
          >
            {titleCase(cadence)}
          </button>
        {/each}
      </div>
    </Card>
    {#if trendPoints.length === 0}
      <EmptyState
        title="No trend data"
        message="Waste entries in the selected window will populate this chart."
      />
    {:else}
      <ChartCard
        title={`${titleCase(trendGranularity)} Waste Trend`}
        description="Uses analytics trend data with date_from/date_to filters when selected."
        chartType="line"
        expandable
        labels={trendPoints.map((point) => point.label)}
        datasets={[
          {
            label: 'Waste',
            data: trendPoints.map((point) => point.value),
            fill: true
          }
        ]}
      />
    {/if}
  </div>
{:else if activeTab === 'heatmap'}
  <div class="mt-5 grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
    <Card
      title="7 x 24 Daily Pattern"
      description={`Hourly waste intensity from ${heatmapSource}. Darker cells mean higher average grams.`}
    >
      {#if heatmap.length === 0}
        <EmptyState
          title="No hourly pattern"
          message="The heatmap will appear when the daily pattern endpoint returns hourly buckets."
        />
      {:else}
        <div class="overflow-auto">
          <div class="min-w-[920px]">
            <div
              class="grid grid-cols-[84px_repeat(24,minmax(28px,1fr))] gap-1"
            >
              <div></div>
              {#each hours as hour}
                <div class="text-center text-[10px] font-semibold text-muted">
                  {hour}
                </div>
              {/each}
              {#each weekdays as weekday}
                <div
                  class="flex h-8 items-center text-xs font-semibold text-muted"
                >
                  {weekday.slice(0, 3)}
                </div>
                {#each hours as hour}
                  {@const point = heatPoint(weekday, hour)}
                  {@const value = heatValue(point ?? {})}
                  <div
                    class="grid h-8 place-items-center rounded-sm border border-border text-[10px] font-semibold text-body"
                    style={heatColor(value)}
                    title={`${weekday} ${hour}:00 - ${grams(value)}`}
                    aria-label={`${weekday} ${hour}:00 ${grams(value)}`}
                  >
                    {value > 0 ? Math.round(value) : ''}
                  </div>
                {/each}
              {/each}
            </div>
          </div>
        </div>
      {/if}
    </Card>

    <Card title="Peak signals">
      <div class="grid gap-3">
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Peak hour</p>
          <p class="mt-2 text-2xl font-semibold text-body">
            {peakSignals.peak_hour === null ||
            peakSignals.peak_hour === undefined
              ? 'None'
              : `${peakSignals.peak_hour}:00`}
          </p>
          <p class="mt-1 text-sm text-muted">
            {grams(peakSignals.peak_hour_grams)}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Peak meal</p>
          <p class="mt-2 text-2xl font-semibold text-body">
            {titleCase(peakSignals.peak_meal ?? 'None')}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Peak weekday</p>
          <p class="mt-2 text-2xl font-semibold text-body">
            {peakSignals.peak_weekday ?? 'None'}
          </p>
        </div>
      </div>
    </Card>
  </div>
{:else if activeTab === 'contributors'}
  <div class="mt-5 grid gap-5 xl:grid-cols-[1fr_1.1fr]">
    <ChartCard
      title="Top Waste Contributors"
      description="Highest total waste in the selected window."
      chartType="bar"
      horizontal
      expandable
      labels={topContributors.map(
        (row) => row.name ?? row.device_id ?? 'Unknown'
      )}
      datasets={[
        {
          label: 'Total waste',
          data: topContributors.map((row) => row.total_waste_grams)
        }
      ]}
    />

    <Card title="Contributor ranking">
      {#if topContributors.length === 0}
        <EmptyState title="No contributors" />
      {:else}
        <div class="overflow-auto">
          <table>
            <thead>
              <tr>
                <th class="th">Rank</th>
                <th class="th">Student</th>
                <th class="th text-right">Avg</th>
                <th class="th text-right">Total</th>
                <th class="th text-right">Events</th>
                <th class="th">Status</th>
              </tr>
            </thead>
            <tbody>
              {#each topContributors as row}
                <tr>
                  <td class="td">{number(row.rank)}</td>
                  <td class="td">
                    <a
                      class="font-semibold text-primary"
                      href={`/dashboard/students/${row.student_id}`}
                    >
                      {row.name ?? row.device_id}
                    </a>
                    <p class="mt-1 font-mono text-xs text-muted">
                      {row.device_id}
                    </p>
                  </td>
                  <td class="td text-right">{grams(row.avg_waste_grams)}</td>
                  <td class="td text-right">{grams(row.total_waste_grams)}</td>
                  <td class="td text-right">{number(row.violation_count)}</td>
                  <td class="td"><StatusBadge value={row.status} compact /></td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>
  </div>
{:else if activeTab === 'improvement'}
  <div class="mt-5 grid gap-5 xl:grid-cols-[1fr_1.1fr]">
    <ChartCard
      title="Improvement Tracking"
      description="Positive values mean lower average waste than the previous window."
      chartType="bar"
      horizontal
      expandable
      labels={improvements.map((row) => row.name ?? row.device_id)}
      datasets={[
        {
          label: 'Improvement %',
          data: improvements.map((row) => row.improvement_pct)
        }
      ]}
    />

    <Card title="Student improvement">
      {#if improvements.length === 0}
        <EmptyState title="No improvement data" />
      {:else}
        <div class="space-y-3">
          {#each improvements as row}
            <a
              class="block rounded-lg border border-border p-3 transition-colors hover:border-primary"
              href={`/dashboard/students/${row.student_id}`}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate font-semibold text-body">
                    {row.name ?? row.device_id}
                  </p>
                  <p class="mt-1 text-xs text-muted">
                    {grams(row.previous_avg_grams)} previous avg / {grams(
                      row.current_avg_grams
                    )} current avg
                  </p>
                </div>
                <div class="text-right">
                  <p
                    class={`font-mono text-lg font-semibold ${
                      row.improvement_pct >= 0 ? 'text-up' : 'text-down'
                    }`}
                  >
                    {pct(row.improvement_pct)}
                  </p>
                  <StatusBadge value={row.direction} compact />
                </div>
              </div>
            </a>
          {/each}
        </div>
      {/if}
    </Card>
  </div>
{:else}
  <div class="mt-5 grid gap-5 xl:grid-cols-[1fr_0.9fr]">
    <ChartCard
      title="Sustainability Distribution"
      description="Score bands from the sustainability endpoint."
      chartType="doughnut"
      expandable
      labels={['Excellent', 'Good', 'Average', 'Poor']}
      datasets={[
        {
          label: 'Students',
          data: [
            sustainability.excellent_count,
            sustainability.good_count,
            sustainability.average_count,
            sustainability.poor_count
          ]
        }
      ]}
    />

    <Card title="Sustainability scorecard">
      <div class="grid gap-3 sm:grid-cols-2">
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Overall average</p>
          <p class="mt-2 text-3xl font-semibold text-body">
            {number(sustainability.overall_avg)}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Students scored</p>
          <p class="mt-2 text-3xl font-semibold text-body">
            {number(totalStudents)}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Excellent</p>
          <p class="mt-2 text-2xl font-semibold text-up">
            {number(sustainability.excellent_count)}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-4">
          <p class="label">Needs attention</p>
          <p class="mt-2 text-2xl font-semibold text-down">
            {number(sustainability.poor_count)}
          </p>
        </div>
      </div>
    </Card>
  </div>
{/if}
