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
    Utensils,
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

  type MealSlot = 'breakfast' | 'lunch' | 'dinner';
  type WeeklyMenuDay = {
    day: string;
    short: string;
    meals: Record<MealSlot, string[]>;
  };

  const mealSlots: Array<{ key: MealSlot; label: string }> = [
    { key: 'breakfast', label: 'Breakfast' },
    { key: 'lunch', label: 'Lunch' },
    { key: 'dinner', label: 'Dinner' }
  ];

  const weeklyMenu: WeeklyMenuDay[] = [
    {
      day: 'Monday',
      short: 'Mon',
      meals: {
        breakfast: ['Idli', 'Sambar', 'Coconut chutney'],
        lunch: ['Chapati', 'Dal tadka', 'Aloo gobi', 'Curd'],
        dinner: ['Jeera rice', 'Rajma', 'Mixed veg', 'Salad']
      }
    },
    {
      day: 'Tuesday',
      short: 'Tue',
      meals: {
        breakfast: ['Poha', 'Boiled egg', 'Tea'],
        lunch: ['Rice', 'Sambar', 'Beans poriyal', 'Papad'],
        dinner: ['Chapati', 'Paneer curry', 'Dal fry', 'Fruit']
      }
    },
    {
      day: 'Wednesday',
      short: 'Wed',
      meals: {
        breakfast: ['Upma', 'Peanut chutney', 'Banana'],
        lunch: ['Veg pulao', 'Raita', 'Chana masala', 'Salad'],
        dinner: ['Rice', 'Rasam', 'Potato fry', 'Curd']
      }
    },
    {
      day: 'Thursday',
      short: 'Thu',
      meals: {
        breakfast: ['Dosa', 'Sambar', 'Tomato chutney'],
        lunch: ['Chapati', 'Dal makhani', 'Cabbage sabzi', 'Rice'],
        dinner: ['Khichdi', 'Kadhi', 'Roasted papad', 'Pickle']
      }
    },
    {
      day: 'Friday',
      short: 'Fri',
      meals: {
        breakfast: ['Aloo paratha', 'Curd', 'Tea'],
        lunch: ['Lemon rice', 'Vegetable kurma', 'Buttermilk', 'Salad'],
        dinner: ['Chapati', 'Egg curry', 'Dal', 'Rice']
      }
    },
    {
      day: 'Saturday',
      short: 'Sat',
      meals: {
        breakfast: ['Puri', 'Chana', 'Halwa'],
        lunch: ['Rice', 'Fish curry', 'Dal', 'Seasonal veg'],
        dinner: ['Veg noodles', 'Manchurian gravy', 'Soup']
      }
    },
    {
      day: 'Sunday',
      short: 'Sun',
      meals: {
        breakfast: ['Masala dosa', 'Sambar', 'Coffee'],
        lunch: ['Biryani', 'Raita', 'Paneer masala', 'Sweet'],
        dinner: ['Chapati', 'Light dal', 'Vegetable stew', 'Fruit']
      }
    }
  ];

  const today = new Date();
  const currentDayIndex = today.getDay() === 0 ? 6 : today.getDay() - 1;
  const weekStart = startOfWeek(today);
  const weekEnd = addDays(weekStart, 6);
  const currentWeekLabel = `${formatMenuDate(weekStart)} - ${formatMenuDate(
    weekEnd
  )}`;

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

  function startOfWeek(date: Date) {
    const weekDate = new Date(date);
    const day = weekDate.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    weekDate.setHours(0, 0, 0, 0);
    weekDate.setDate(weekDate.getDate() + diff);
    return weekDate;
  }

  function addDays(date: Date, days: number) {
    const nextDate = new Date(date);
    nextDate.setDate(nextDate.getDate() + days);
    return nextDate;
  }

  function formatMenuDate(date: Date) {
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short'
    }).format(date);
  }

  function scrollToWeeklyMenu() {
    document
      .getElementById('current-week-menu')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
      on:click={scrollToWeeklyMenu}
      id="btn-current-week-menu"
    >
      <Utensils size={16} />
      Week menu
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

<section id="current-week-menu" class="mb-5 scroll-mt-5">
  <div class="mb-3 flex flex-wrap items-end justify-between gap-3">
    <div>
      <p class="label">Current week menu</p>
      <h2 class="mt-1 text-lg font-semibold text-body">
        Planned meals for {currentWeekLabel}
      </h2>
    </div>
    <div
      class="inline-flex items-center gap-2 rounded-full border border-border bg-elevated px-3 py-1.5 text-sm text-muted-strong"
    >
      <CalendarDays size={15} class="text-primary" />
      {weeklyMenu[currentDayIndex].day}
    </div>
  </div>

  <div class="-mx-1 overflow-x-auto pb-2">
    <div class="grid min-w-[1540px] grid-cols-7 gap-3 px-1">
      {#each weeklyMenu as menuDay, index}
        <article
          class={`rounded-lg border p-4 ${
            index === currentDayIndex
              ? 'border-primary bg-primary/5'
              : 'border-border bg-card'
          }`}
        >
          <div class="mb-4 flex items-start justify-between gap-2">
            <div>
              <p class="label">{menuDay.short}</p>
              <h3 class="mt-1 text-base font-semibold text-body">
                {menuDay.day}
              </h3>
              <p class="mt-1 text-xs text-muted">
                {formatMenuDate(addDays(weekStart, index))}
              </p>
            </div>
            {#if index === currentDayIndex}
              <span class="badge-primary">Today</span>
            {/if}
          </div>

          <div class="space-y-3">
            {#each mealSlots as slot}
              <div>
                <p
                  class="text-[11px] font-semibold uppercase tracking-wide text-muted"
                >
                  {slot.label}
                </p>
                <p class="mt-1 line-clamp-2 text-sm leading-5 text-muted-strong">
                  {menuDay.meals[slot.key].join(', ')}
                </p>
              </div>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  </div>
</section>

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
