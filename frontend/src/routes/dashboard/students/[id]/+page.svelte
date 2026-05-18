<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page as pageStore } from '$app/stores';
  import {
    ArrowLeft,
    Bell,
    Download,
    RefreshCw,
    ShieldAlert,
    TrendingDown
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Student } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FormField from '$lib/components/ui/FormField.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs from '$lib/components/ui/Tabs.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import Gauge from '$lib/components/charts/Gauge.svelte';
  import { dateTime, grams, number, pct, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';
  import { WARNING_LEVELS } from '$lib/utils/constants';

  type ProfileTab = 'overview' | 'waste' | 'warnings';
  type WasteStats = {
    student_id: string;
    period: string;
    total_waste_grams: number;
    avg_waste_grams: number;
    entry_count: number;
    most_wasted_food?: string | null;
    peak_meal?: string | null;
    sustainability_score: number;
    improvement_pct?: number | null;
  };
  type Timeline = {
    student_id?: string;
    period?: string;
    threshold_grams?: number;
    data: Array<{ date: string; total_grams: number; entry_count: number }>;
  };
  type FoodBreakdown = {
    student_id?: string;
    data: Array<{ food_name: string; total_grams: number; percentage: number }>;
  };
  type Improvement = {
    student_id?: string;
    current_improvement_pct?: number;
    direction?: string;
    data: Array<{
      week_label: string;
      avg_grams: number;
      improvement_pct: number;
    }>;
  };
  type WarningItem = {
    id: string;
    level: string;
    reason: string;
    status: string;
    created_at: string;
    email_sent?: boolean;
  };
  type PenaltyItem = {
    id: string;
    points: number;
    reason: string;
    status: string;
    created_at: string;
    email_sent?: boolean;
  };
  type WarningLog = {
    warnings: WarningItem[];
    penalties: PenaltyItem[];
  };
  type TimelineEvent = {
    id: string;
    type: 'warning' | 'penalty';
    label: string;
    reason: string;
    status: string;
    created_at: string;
    email_sent?: boolean;
  };

  const id = $pageStore.params.id;
  const tabs = [
    { id: 'overview', label: 'Overview', icon: TrendingDown },
    { id: 'waste', label: 'Waste History', icon: TrendingDown },
    { id: 'warnings', label: 'Warning Timeline', icon: ShieldAlert }
  ];

  let loading = true;
  let error = '';
  let warningError = '';
  let activeTab: ProfileTab = 'overview';
  let period = '30d';
  let profile: Student | null = null;
  let stats: WasteStats | null = null;
  let timeline: Timeline = { data: [] };
  let foodBreakdown: FoodBreakdown = { data: [] };
  let improvement: Improvement = { data: [] };
  let warningLog: WarningLog = { warnings: [], penalties: [] };
  let warningOpen = false;
  let penaltyOpen = false;
  let warningForm = { level: 'level_1', reason: '', send_email: true };
  let penaltyForm = { points: 5, reason: '', send_email: true };

  $: studentTitle =
    profile?.mapping?.name ?? profile?.device_id ?? 'Student profile';
  $: studentDescription = profile?.mapping
    ? `${profile.mapping.roll_number} / ${profile.mapping.branch} / Year ${profile.mapping.year}`
    : profile
      ? `Unmapped device ${profile.device_id}`
      : 'Loading student profile';
  $: sustainabilityScore = Number(
    stats?.sustainability_score ?? profile?.sustainability_score ?? 0
  );
  $: warningEvents = buildWarningEvents(warningLog);

  function buildWarningEvents(log: WarningLog): TimelineEvent[] {
    return [
      ...log.warnings.map((warning) => ({
        id: warning.id,
        type: 'warning' as const,
        label: titleCase(warning.level),
        reason: warning.reason,
        status: warning.status,
        created_at: warning.created_at,
        email_sent: warning.email_sent
      })),
      ...log.penalties.map((penalty) => ({
        id: penalty.id,
        type: 'penalty' as const,
        label: `${number(penalty.points)} points`,
        reason: penalty.reason,
        status: penalty.status,
        created_at: penalty.created_at,
        email_sent: penalty.email_sent
      }))
    ].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }

  async function loadProfile() {
    loading = true;
    error = '';
    warningError = '';
    try {
      const [
        profileData,
        statsData,
        timelineData,
        foodData,
        warningData,
        improvementData
      ] = await Promise.all([
        api.get<Student>(`/students/${id}`),
        api.get<WasteStats>(`/students/${id}/stats`, { period }),
        api.get<Timeline>(`/students/${id}/timeline`, { period }),
        api.get<FoodBreakdown>(`/students/${id}/food-breakdown`, { period }),
        api.get<WarningLog>(`/students/${id}/warnings`).catch((err) => {
          warningError =
            err instanceof Error ? err.message : 'Could not load warnings';
          return { warnings: [], penalties: [] };
        }),
        api.get<Improvement>(`/students/${id}/improvement`)
      ]);
      profile = profileData;
      stats = statsData;
      timeline = timelineData;
      foodBreakdown = foodData;
      warningLog = warningData;
      improvement = improvementData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load student profile';
    } finally {
      loading = false;
    }
  }

  async function issueWarning() {
    try {
      await api.post(`/students/${id}/warnings`, warningForm);
      notify('Warning issued.', 'success');
      warningOpen = false;
      warningForm = { level: 'level_1', reason: '', send_email: true };
      await loadProfile();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not issue warning.',
        'error'
      );
    }
  }

  async function issuePenalty() {
    try {
      await api.post(`/students/${id}/penalties`, penaltyForm);
      notify('Penalty applied.', 'success');
      penaltyOpen = false;
      penaltyForm = { points: 5, reason: '', send_email: true };
      await loadProfile();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not apply penalty.',
        'error'
      );
    }
  }

  async function exportProfile() {
    try {
      await api.post('/reports/generate', {
        type: 'student_history',
        format: 'pdf',
        student_id: id,
        filters: { period }
      });
      notify('Student profile report queued.', 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not queue report.',
        'error'
      );
    }
  }

  onMount(loadProfile);
</script>

<svelte:head>
  <title>{studentTitle} | CleanPlates</title>
</svelte:head>

<div class="mb-4">
  <Button
    variant="secondary"
    on:click={() => goto('/dashboard/students')}
    id="btn-back-students"
  >
    <ArrowLeft size={16} />
    Students
  </Button>
</div>

<PageHeader
  label="Student profile"
  title={studentTitle}
  description={studentDescription}
>
  <svelte:fragment slot="actions">
    <select
      class="select-field"
      bind:value={period}
      on:change={loadProfile}
      id="select-student-period"
    >
      <option value="7d">7 days</option>
      <option value="30d">30 days</option>
      <option value="semester">Semester</option>
      <option value="all">All</option>
    </select>
    <Button variant="secondary" on:click={loadProfile} id="btn-refresh-profile">
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={() => (warningOpen = true)}
      id="btn-issue-warning"
    >
      <ShieldAlert size={16} />
      Warning
    </Button>
    <Button
      variant="secondary"
      on:click={() => (penaltyOpen = true)}
      id="btn-issue-penalty"
    >
      <Bell size={16} />
      Penalty
    </Button>
    <Button on:click={exportProfile} id="btn-export-profile">
      <Download size={16} />
      Export
    </Button>
  </svelte:fragment>
</PageHeader>

{#if error}
  <Card title="Student unavailable" description={error}>
    <Button on:click={loadProfile}>Retry</Button>
  </Card>
{:else if loading && !profile}
  <div class="grid gap-5 xl:grid-cols-2">
    <div class="skeleton h-56"></div>
    <div class="skeleton h-56"></div>
  </div>
{:else if profile}
  <Card>
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-4">
        <div
          class="grid h-16 w-16 shrink-0 place-items-center rounded-lg bg-primary text-xl font-semibold text-ink"
        >
          {(profile.mapping?.name ?? profile.device_id)
            .slice(0, 2)
            .toUpperCase()}
        </div>
        <div class="min-w-0">
          <h3 class="truncate text-xl font-semibold text-body">
            {profile.mapping?.name ?? 'Unmapped student'}
          </h3>
          <p class="mt-1 text-sm text-muted">
            {profile.mapping?.roll_number ?? profile.device_id}
          </p>
          <p class="mt-1 text-sm text-muted">
            {profile.mapping
              ? `${profile.mapping.hostel ?? 'No hostel'} / ${profile.mapping.room_number ?? 'No room'}`
              : 'Map this device to unlock identity fields.'}
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge value={profile.status} />
        <StatusBadge value={profile.is_active ? 'active' : 'inactive'} />
      </div>
    </div>
  </Card>

  <div class="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <StatCard
      title="Total Waste"
      value={grams(stats?.total_waste_grams)}
      helper={`${number(stats?.entry_count)} entries`}
    >
      <svelte:fragment slot="icon"><TrendingDown size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Avg Waste"
      value={grams(stats?.avg_waste_grams ?? profile.avg_waste_grams)}
      helper={`Peak meal ${titleCase(stats?.peak_meal ?? 'none')}`}
    >
      <svelte:fragment slot="icon"><TrendingDown size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Warnings"
      value={number(profile.warning_count)}
      helper="Active warning count"
      tone="warn"
    >
      <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Improvement"
      value={pct(stats?.improvement_pct ?? improvement.current_improvement_pct)}
      helper={titleCase(improvement.direction ?? 'stable')}
      tone={(stats?.improvement_pct ??
        improvement.current_improvement_pct ??
        0) >= 0
        ? 'good'
        : 'bad'}
    >
      <svelte:fragment slot="icon"><TrendingDown size={19} /></svelte:fragment>
    </StatCard>
  </div>

  <div class="mt-5">
    <Tabs
      {tabs}
      active={activeTab}
      onChange={(tab) => (activeTab = tab as ProfileTab)}
    />
  </div>

  {#if activeTab === 'overview'}
    <div class="mt-5 grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
      <Card title="Sustainability score">
        <Gauge
          value={sustainabilityScore}
          max={100}
          unit="score"
          label="Higher score means lower sustained waste"
          tone="score"
        />
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div class="rounded-md bg-elevated p-3">
            <p class="label">Status</p>
            <div class="mt-2">
              <StatusBadge value={profile.status} compact />
            </div>
          </div>
          <div class="rounded-md bg-elevated p-3">
            <p class="label">Most wasted</p>
            <p class="mt-2 truncate text-sm font-semibold text-body">
              {stats?.most_wasted_food ?? 'None'}
            </p>
          </div>
        </div>
      </Card>

      <ChartCard
        title="Waste History"
        description="Daily total waste for the selected period."
        chartType="line"
        expandable
        labels={timeline.data.map((point) => String(point.date))}
        datasets={[
          {
            label: 'Waste',
            data: timeline.data.map((point) => point.total_grams),
            fill: true
          },
          {
            label: 'Threshold',
            data: timeline.data.map(() => Number(timeline.threshold_grams ?? 0))
          }
        ]}
      />

      <ChartCard
        title="Food Breakdown"
        chartType="doughnut"
        expandable
        labels={foodBreakdown.data.map((item) => item.food_name)}
        datasets={[
          {
            label: 'Waste',
            data: foodBreakdown.data.map((item) => item.total_grams)
          }
        ]}
      />

      <ChartCard
        title="Improvement Trend"
        chartType="line"
        expandable
        labels={improvement.data.map((item) => item.week_label)}
        datasets={[
          {
            label: 'Average grams',
            data: improvement.data.map((item) => item.avg_grams)
          },
          {
            label: 'Improvement %',
            data: improvement.data.map((item) => item.improvement_pct)
          }
        ]}
      />
    </div>
  {:else if activeTab === 'waste'}
    <div class="mt-5 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
      <ChartCard
        title="Waste History"
        description="Entry counts are represented by the second series."
        chartType="bar"
        expandable
        labels={timeline.data.map((point) => String(point.date))}
        datasets={[
          {
            label: 'Waste',
            data: timeline.data.map((point) => point.total_grams)
          },
          {
            label: 'Entries',
            data: timeline.data.map((point) => point.entry_count)
          }
        ]}
      />

      <Card title="Food breakdown">
        {#if foodBreakdown.data.length === 0}
          <EmptyState title="No food data" />
        {:else}
          <div class="space-y-3">
            {#each foodBreakdown.data as item}
              <div class="rounded-lg border border-border p-3">
                <div class="flex items-center justify-between gap-3">
                  <p class="font-semibold text-body">{item.food_name}</p>
                  <span class="font-mono text-sm text-primary">
                    {grams(item.total_grams)}
                  </span>
                </div>
                <div class="mt-2 h-2 rounded-full bg-elevated">
                  <div
                    class="h-full rounded-full bg-primary"
                    style={`width:${Math.min(100, Number(item.percentage ?? 0))}%`}
                  ></div>
                </div>
                <p class="mt-1 text-xs text-muted">
                  {pct(item.percentage)} of this student's waste
                </p>
              </div>
            {/each}
          </div>
        {/if}
      </Card>
    </div>
  {:else}
    <div class="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <Card title="Warning timeline" description={warningError}>
        {#if warningEvents.length === 0}
          <EmptyState
            title="No warnings"
            message={warningError || 'Warnings and penalties will appear here.'}
          />
        {:else}
          <div class="space-y-3">
            {#each warningEvents as event}
              <div class="rounded-lg border border-border p-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                      <span
                        class={event.type === 'penalty'
                          ? 'badge-down'
                          : 'badge-primary'}
                      >
                        {titleCase(event.type)}
                      </span>
                      <span class="text-sm font-semibold text-body">
                        {event.label}
                      </span>
                    </div>
                    <p class="mt-2 text-sm text-muted">{event.reason}</p>
                    <p class="mt-1 text-xs text-muted">
                      {dateTime(event.created_at)}
                      {event.email_sent ? ' / email sent' : ''}
                    </p>
                  </div>
                  <StatusBadge value={event.status} compact />
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </Card>

      <Card title="Warning summary">
        <div class="grid gap-3">
          <div class="rounded-md bg-elevated p-4">
            <p class="label">Warnings</p>
            <p class="mt-2 text-3xl font-semibold text-primary">
              {number(warningLog.warnings.length)}
            </p>
          </div>
          <div class="rounded-md bg-elevated p-4">
            <p class="label">Penalties</p>
            <p class="mt-2 text-3xl font-semibold text-down">
              {number(warningLog.penalties.length)}
            </p>
          </div>
          <div class="rounded-md bg-elevated p-4">
            <p class="label">Profile counters</p>
            <p class="mt-2 text-sm text-body">
              {number(profile.warning_count)} active warnings / {number(
                profile.penalty_count
              )} active penalties
            </p>
          </div>
        </div>
      </Card>
    </div>
  {/if}
{/if}

<Modal
  open={warningOpen}
  title="Issue warning"
  description={studentTitle}
  on:close={() => (warningOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={issueWarning}>
    <FormField label="Level" required>
      <select class="select-field" bind:value={warningForm.level}>
        {#each WARNING_LEVELS as level, i}
          <option value={level}>Level {i + 1}</option>
        {/each}
      </select>
    </FormField>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={warningForm.reason} required
      ></textarea>
    </FormField>
    <label class="flex items-center gap-2 text-sm text-muted-strong">
      <input type="checkbox" bind:checked={warningForm.send_email} />
      Send email
    </label>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (warningOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit">Issue warning</Button>
    </div>
  </form>
</Modal>

<Modal
  open={penaltyOpen}
  title="Apply penalty"
  description={studentTitle}
  on:close={() => (penaltyOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={issuePenalty}>
    <FormField label="Points" required>
      <input
        class="input-field"
        type="number"
        min="1"
        max="100"
        bind:value={penaltyForm.points}
      />
    </FormField>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={penaltyForm.reason} required
      ></textarea>
    </FormField>
    <label class="flex items-center gap-2 text-sm text-muted-strong">
      <input type="checkbox" bind:checked={penaltyForm.send_email} />
      Send email
    </label>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (penaltyOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit">Apply penalty</Button>
    </div>
  </form>
</Modal>
