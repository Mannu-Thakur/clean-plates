<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    AlertTriangle,
    Bell,
    CalendarDays,
    Clock,
    Cpu,
    Download,
    RefreshCw,
    Scale,
    TrendingDown,
    Users
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { KpiOverview, ReportItem } from '$lib/api/types';
  import { ReconnectingSocket } from '$lib/api/ws';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { grams, number, pct } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  let period = '30d';
  let loading = true;
  let error = '';
  let wsStatus = 'closed';
  let socket: ReconnectingSocket | null = null;

  let overview: KpiOverview | null = null;
  let weekly: { data: Array<{ label: string; value: number }> } = { data: [] };
  let monthly: {
    current_label?: string;
    previous_label?: string;
    current_data?: Array<{ label: string; value: number }>;
    previous_data?: Array<{ label: string; value: number }>;
  } = {};
  let meals: {
    data: Array<{ meal_type: string; total_grams: number; percentage: number }>;
  } = { data: [] };
  let foods: {
    data: Array<{ food_name: string; total_grams: number; percentage: number }>;
  } = { data: [] };
  let peaks: {
    peak_hour?: number | null;
    peak_meal?: string | null;
    peak_weekday?: string | null;
  } = {};

  async function loadOverview() {
    loading = true;
    error = '';
    try {
      const [
        overviewData,
        weeklyData,
        monthlyData,
        mealData,
        foodData,
        peakData
      ] = await Promise.all([
        api.get<KpiOverview>('/analytics/overview', { period }),
        api.get<typeof weekly>('/analytics/trends', { type: 'weekly', period }),
        api.get<typeof monthly>('/analytics/trends', {
          type: 'monthly_comparison',
          period
        }),
        api.get<typeof meals>('/analytics/meal-distribution', { period }),
        api.get<typeof foods>('/analytics/food-waste-distribution', {
          period,
          limit: 10
        }),
        api.get<typeof peaks>('/analytics/peaks', { period })
      ]);
      overview = overviewData;
      weekly = weeklyData;
      monthly = monthlyData;
      meals = mealData;
      foods = foodData;
      peaks = peakData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load dashboard data';
    } finally {
      loading = false;
    }
  }

  async function exportOverview() {
    try {
      const report = await api.post<ReportItem>('/reports/generate', {
        type: 'overview',
        format: 'pdf',
        filters: { period }
      });
      if (report.status === 'ready') {
        await api.download(
          `/reports/${report.id}/download`,
          `overview-${period}.${report.format === 'excel' ? 'xlsx' : report.format}`
        );
        notify('Overview report downloaded.', 'success');
      } else {
        notify('Overview report is generating. Download it from Reports when ready.', 'success');
      }
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export overview.',
        'error'
      );
    }
  }

  onMount(() => {
    loadOverview();
    socket = new ReconnectingSocket(
      '/dashboard',
      (message) => {
        if (
          [
            'waste_entry',
            'warning_issued',
            'rule_executed',
            'kpi_update',
            'alert'
          ].includes(String(message.type))
        )
          loadOverview();
      },
      (status) => (wsStatus = status)
    );
    socket.connect();
  });

  onDestroy(() => socket?.close());
</script>

<svelte:head>
  <title>Overview | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Global overview"
  title="Institution-wide waste operations"
  description="Live KPIs, trend charts, and queueable reporting across the institution."
>
  <svelte:fragment slot="actions">
    <StatusBadge value={wsStatus} />
    <select
      class="select-field"
      bind:value={period}
      on:change={loadOverview}
      id="select-overview-period"
    >
      <option value="today">Today</option>
      <option value="7d">7 days</option>
      <option value="30d">30 days</option>
      <option value="semester">Semester</option>
    </select>
    <Button
      variant="secondary"
      on:click={loadOverview}
      id="btn-refresh-overview"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={exportOverview}
      id="btn-export-overview"
    >
      <Download size={16} />
      Export
    </Button>
  </svelte:fragment>
</PageHeader>

{#if error}
  <Card title="Dashboard unavailable" description={error}>
    <Button on:click={loadOverview}>Retry</Button>
  </Card>
{:else if loading && !overview}
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
    {#each Array(10) as _}
      <div class="skeleton h-32"></div>
    {/each}
  </div>
{:else if overview}
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
    <StatCard
      title="Waste Today"
      value={grams(overview.total_waste_today_grams)}
      helper="All meal sessions"
    >
      <svelte:fragment slot="icon"><Scale size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Waste This Week"
      value={grams(overview.total_waste_week_grams)}
      helper="Rolling weekly total"
    >
      <svelte:fragment slot="icon"><CalendarDays size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Waste This Month"
      value={grams(overview.total_waste_month_grams)}
      helper={`${grams(overview.avg_daily_waste_grams)} daily avg`}
    >
      <svelte:fragment slot="icon"><TrendingDown size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Reduction"
      value={pct(overview.waste_reduction_pct)}
      helper="Compared with previous period"
      tone={(overview.waste_reduction_pct ?? 0) >= 0 ? 'good' : 'bad'}
    >
      <svelte:fragment slot="icon"><TrendingDown size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Peak Time"
      value={overview.peak_waste_time ??
        (peaks.peak_hour !== null && peaks.peak_hour !== undefined
          ? `${peaks.peak_hour}:00`
          : 'None')}
      helper={peaks.peak_meal ?? 'No meal peak yet'}
    >
      <svelte:fragment slot="icon"><Clock size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Active Students"
      value={number(overview.total_active_students)}
      helper="Mapped and unmapped"
    >
      <svelte:fragment slot="icon"><Users size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Under Warning"
      value={number(overview.students_under_warning)}
      helper="Active warning status"
      tone="warn"
    >
      <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Under Penalty"
      value={number(overview.students_under_penalty)}
      helper="Active penalties"
      tone="bad"
    >
      <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Active Devices"
      value={number(overview.active_devices)}
      helper={`${number(overview.offline_devices)} offline`}
    >
      <svelte:fragment slot="icon"><Cpu size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Alerts Today"
      value={number(overview.alerts_today)}
      helper={`${number(overview.rule_violations_today)} rule events`}
      tone="hot"
    >
      <svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment>
    </StatCard>
  </div>

  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <ChartCard
      title="Weekly Waste Trend"
      chartType="line"
      expandable
      labels={weekly.data.map((point) => point.label)}
      datasets={[
        {
          label: 'Waste',
          data: weekly.data.map((point) => point.value),
          fill: true
        }
      ]}
    />
    <ChartCard
      title="Monthly Comparison"
      chartType="bar"
      expandable
      labels={(monthly.current_data ?? monthly.previous_data ?? []).map(
        (point) => point.label
      )}
      datasets={[
        {
          label: monthly.current_label ?? 'Current',
          data: (monthly.current_data ?? []).map((point) => point.value)
        },
        {
          label: monthly.previous_label ?? 'Previous',
          data: (monthly.previous_data ?? []).map((point) => point.value)
        }
      ]}
    />
    <ChartCard
      title="Meal Distribution"
      chartType="doughnut"
      expandable
      labels={meals.data.map((item) => item.meal_type)}
      datasets={[
        { label: 'Waste', data: meals.data.map((item) => item.total_grams) }
      ]}
    />
    <ChartCard
      title="Top Wasted Foods"
      chartType="bar"
      horizontal
      expandable
      labels={foods.data.map((item) => item.food_name)}
      datasets={[
        { label: 'Waste', data: foods.data.map((item) => item.total_grams) }
      ]}
    />
  </div>
{:else}
  <EmptyState
    title="No overview data"
    message="Create waste entries or run aggregations to populate the overview."
  />
{/if}
