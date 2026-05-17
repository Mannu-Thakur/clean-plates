<script lang="ts">
  import { onMount } from 'svelte';
  import { Download, Filter, RefreshCw, Save } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { grams, number, pct, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type Preset = {
    id: string;
    name: string;
    filter_state: Record<string, unknown>;
  };
  type Filters = {
    period: string;
    branch: string;
    year: string;
    hostel: string;
    meal_type: string;
    food: string;
    status: string;
  };

  const tabs = ['student', 'food', 'meal'] as const;

  let activeTab: 'student' | 'food' | 'meal' = 'student';
  let loading = false;
  let error = '';
  let presets: Preset[] = [];
  let selectedPreset = '';
  let filters: Filters = {
    period: '30d',
    branch: '',
    year: '',
    hostel: '',
    meal_type: '',
    food: '',
    status: ''
  };
  let topContributors: Array<Record<string, unknown>> = [];
  let improvements: Array<Record<string, unknown>> = [];
  let foodRanking: Array<Record<string, unknown>> = [];
  let mealDistribution: Array<Record<string, unknown>> = [];
  let peaks: Record<string, unknown> = {};
  let sustainability: Record<string, unknown> = {};

  function query() {
    return {
      period: filters.period,
      branch: filters.branch,
      year: filters.year ? Number(filters.year) : undefined,
      hostel: filters.hostel,
      meal_type: filters.meal_type,
      food: filters.food,
      status: filters.status
    };
  }

  async function loadPresets() {
    try {
      presets = await api.get<Preset[]>('/filters/presets');
    } catch {
      presets = [];
    }
  }

  async function loadAnalytics() {
    loading = true;
    error = '';
    try {
      const [
        contributors,
        improvementData,
        foodData,
        mealData,
        peakData,
        scoreData
      ] = await Promise.all([
        api.get<{ data: Array<Record<string, unknown>> }>(
          '/analytics/top-waste-contributors',
          { ...query(), limit: 15 }
        ),
        api.get<Array<Record<string, unknown>>>(
          '/analytics/improvement-tracking',
          query()
        ),
        api.get<{ data: Array<Record<string, unknown>> }>(
          '/analytics/food-waste-distribution',
          { ...query(), limit: 15 }
        ),
        api.get<{ data: Array<Record<string, unknown>> }>(
          '/analytics/meal-distribution',
          query()
        ),
        api.get<Record<string, unknown>>('/analytics/peaks', query()),
        api.get<Record<string, unknown>>('/analytics/sustainability', query())
      ]);
      topContributors = contributors.data;
      improvements = improvementData;
      foodRanking = foodData.data;
      mealDistribution = mealData.data;
      peaks = peakData;
      sustainability = scoreData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load analytics';
    } finally {
      loading = false;
    }
  }

  function resetFilters() {
    filters = {
      period: '30d',
      branch: '',
      year: '',
      hostel: '',
      meal_type: '',
      food: '',
      status: ''
    };
    selectedPreset = '';
    loadAnalytics();
  }

  async function savePreset() {
    const name = window.prompt('Preset name');
    if (!name) return;
    try {
      await api.post('/filters/presets', { name, filter_state: filters });
      notify('Filter preset saved.', 'success');
      await loadPresets();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save preset.',
        'error'
      );
    }
  }

  function applyPreset() {
    const preset = presets.find((item) => item.id === selectedPreset);
    if (!preset) return;
    filters = { ...filters, ...(preset.filter_state as Partial<Filters>) };
    loadAnalytics();
  }

  async function exportAnalytics(format: 'pdf' | 'csv' | 'excel') {
    try {
      await api.post('/reports/generate', {
        type: `analytics_${activeTab}`,
        format,
        filters
      });
      notify(`${titleCase(format)} analytics report queued.`, 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not queue export.',
        'error'
      );
    }
  }

  onMount(async () => {
    await Promise.all([loadPresets(), loadAnalytics()]);
  });
</script>

<svelte:head>
  <title>Analytics | CleanPlates</title>
</svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Deep analytics</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      Student, food, and meal trends
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadAnalytics} id="btn-apply-filters"
      ><RefreshCw size={16} />Apply</Button
    >
    <Button variant="secondary" on:click={resetFilters} id="btn-reset-filters"
      >Reset</Button
    >
    <Button variant="secondary" on:click={savePreset} id="btn-save-preset"
      ><Save size={16} />Preset</Button
    >
    <Button on:click={() => exportAnalytics('pdf')} id="btn-export-pdf"
      ><Download size={16} />PDF</Button
    >
  </div>
</div>

<Card
  title="Filters"
  description="Saved presets and dimensions apply to every analytics panel."
>
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
    <label
      ><span class="label">Period</span><select
        class="field mt-2 w-full"
        bind:value={filters.period}
        ><option value="today">Today</option><option value="7d">7d</option
        ><option value="30d">30d</option><option value="semester"
          >Semester</option
        ></select
      ></label
    >
    <label
      ><span class="label">Branch</span><input
        class="field mt-2 w-full"
        bind:value={filters.branch}
        placeholder="CSE"
      /></label
    >
    <label
      ><span class="label">Year</span><select
        class="field mt-2 w-full"
        bind:value={filters.year}
        ><option value="">All</option><option>1</option><option>2</option
        ><option>3</option><option>4</option></select
      ></label
    >
    <label
      ><span class="label">Hostel</span><input
        class="field mt-2 w-full"
        bind:value={filters.hostel}
        placeholder="A Block"
      /></label
    >
    <label
      ><span class="label">Meal</span><select
        class="field mt-2 w-full"
        bind:value={filters.meal_type}
        ><option value="">All</option><option value="breakfast"
          >Breakfast</option
        ><option value="lunch">Lunch</option><option value="dinner"
          >Dinner</option
        ></select
      ></label
    >
    <label
      ><span class="label">Food</span><input
        class="field mt-2 w-full"
        bind:value={filters.food}
        placeholder="Rice"
      /></label
    >
    <label
      ><span class="label">Status</span><select
        class="field mt-2 w-full"
        bind:value={filters.status}
        ><option value="">All</option><option>green</option><option
          >yellow</option
        ><option>orange</option><option>red</option></select
      ></label
    >
    <label
      ><span class="label">Preset</span><select
        class="field mt-2 w-full"
        bind:value={selectedPreset}
        on:change={applyPreset}
        id="select-preset"
        ><option value="">None</option>{#each presets as preset}<option
            value={preset.id}>{preset.name}</option
          >{/each}</select
      ></label
    >
  </div>
</Card>

<div class="mt-5 flex flex-wrap gap-2">
  {#each tabs as tab}
    <button
      class={`rounded-md px-4 py-2 text-sm font-semibold transition ${activeTab === tab ? 'bg-fresh text-white' : 'bg-white text-muted hover:text-ink'}`}
      on:click={() => (activeTab = tab)}
      id={`tab-${tab}`}
    >
      {titleCase(tab)}
    </button>
  {/each}
  <Button
    variant="secondary"
    size="sm"
    on:click={() => exportAnalytics('csv')}
    id="btn-export-csv">CSV</Button
  >
  <Button
    variant="secondary"
    size="sm"
    on:click={() => exportAnalytics('excel')}>Excel</Button
  >
</div>

{#if error}
  <div class="mt-5">
    <Card title="Analytics unavailable" description={error}
      ><Button on:click={loadAnalytics}>Retry</Button></Card
    >
  </div>
{:else if loading}
  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <div class="surface h-80 animate-pulse bg-slate-100"></div>
    <div class="surface h-80 animate-pulse bg-slate-100"></div>
  </div>
{:else if activeTab === 'student'}
  <div class="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
    <Card
      title="Top Waste Contributors"
      description="Ranked by average and total waste."
    >
      {#if topContributors.length === 0}
        <EmptyState />
      {:else}
        <div class="overflow-auto">
          <table>
            <thead class="table-head"
              ><tr
                ><th class="table-cell">Rank</th><th class="table-cell"
                  >Student</th
                ><th class="table-cell">Avg</th><th class="table-cell">Total</th
                ><th class="table-cell">Status</th></tr
              ></thead
            >
            <tbody>
              {#each topContributors as row}
                <tr>
                  <td class="table-cell">{number(row.rank as number)}</td>
                  <td class="table-cell"
                    ><a
                      class="font-semibold text-fresh"
                      href={`/dashboard/students/${row.student_id}`}
                      >{row.name ?? row.device_id}</a
                    ></td
                  >
                  <td class="table-cell"
                    >{grams(row.avg_waste_grams as number)}</td
                  >
                  <td class="table-cell"
                    >{grams(row.total_waste_grams as number)}</td
                  >
                  <td class="table-cell"
                    ><StatusBadge value={String(row.status)} compact /></td
                  >
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>
    <ChartCard
      title="Improvement Tracking"
      chartType="bar"
      labels={improvements.map((row) => String(row.name ?? row.device_id))}
      datasets={[
        {
          label: 'Improvement %',
          data: improvements.map((row) => Number(row.improvement_pct ?? 0))
        }
      ]}
    />
    <ChartCard
      title="Sustainability Distribution"
      chartType="doughnut"
      labels={['Excellent', 'Good', 'Average', 'Poor']}
      datasets={[
        {
          label: 'Students',
          data: [
            'excellent_count',
            'good_count',
            'average_count',
            'poor_count'
          ].map((key) => Number(sustainability[key] ?? 0))
        }
      ]}
    />
    <Card title="Peak Waste Signals">
      <div class="grid gap-3 sm:grid-cols-3">
        <div class="rounded-lg bg-slate-50 p-4">
          <span class="label">Hour</span>
          <p class="mt-2 text-xl font-semibold">{peaks.peak_hour ?? 'None'}</p>
        </div>
        <div class="rounded-lg bg-slate-50 p-4">
          <span class="label">Meal</span>
          <p class="mt-2 text-xl font-semibold">
            {titleCase(String(peaks.peak_meal ?? 'None'))}
          </p>
        </div>
        <div class="rounded-lg bg-slate-50 p-4">
          <span class="label">Weekday</span>
          <p class="mt-2 text-xl font-semibold">
            {String(peaks.peak_weekday ?? 'None')}
          </p>
        </div>
      </div>
    </Card>
  </div>
{:else if activeTab === 'food'}
  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <ChartCard
      title="Most Wasted Foods"
      chartType="bar"
      labels={foodRanking.map((row) => String(row.food_name))}
      datasets={[
        {
          label: 'Waste',
          data: foodRanking.map((row) => Number(row.total_grams ?? 0))
        }
      ]}
    />
    <Card title="Food Ranking">
      {#if foodRanking.length === 0}<EmptyState />{:else}
        <div class="space-y-3">
          {#each foodRanking as row}
            <div class="rounded-lg border border-line p-3">
              <div class="flex justify-between gap-3">
                <p class="font-semibold">{row.food_name}</p>
                <span>{grams(row.total_grams as number)}</span>
              </div>
              <div class="mt-2 h-2 rounded-full bg-slate-100">
                <div
                  class="h-2 rounded-full bg-fresh"
                  style={`width:${Math.min(100, Number(row.percentage ?? 0))}%`}
                ></div>
              </div>
              <p class="mt-1 text-xs text-muted">
                {pct(Number(row.percentage ?? 0))} of filtered waste
              </p>
            </div>
          {/each}
        </div>
      {/if}
    </Card>
  </div>
{:else}
  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <ChartCard
      title="Meal-Wise Distribution"
      chartType="doughnut"
      labels={mealDistribution.map((row) => titleCase(String(row.meal_type)))}
      datasets={[
        {
          label: 'Waste',
          data: mealDistribution.map((row) => Number(row.total_grams ?? 0))
        }
      ]}
    />
    <Card title="Meal Comparison">
      {#if mealDistribution.length === 0}<EmptyState />{:else}
        <div class="grid gap-3">
          {#each mealDistribution as row}
            <div
              class="flex items-center justify-between rounded-lg border border-line p-4"
            >
              <div>
                <p class="font-semibold">{titleCase(String(row.meal_type))}</p>
                <p class="text-sm text-muted">
                  {pct(Number(row.percentage ?? 0))} share
                </p>
              </div>
              <p class="text-lg font-semibold">
                {grams(row.total_grams as number)}
              </p>
            </div>
          {/each}
        </div>
      {/if}
    </Card>
  </div>
{/if}
