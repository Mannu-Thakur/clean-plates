<script lang="ts">
  import { onMount } from 'svelte';
  import { page as pageStore } from '$app/stores';
  import { goto } from '$app/navigation';
  import { ArrowLeft, Bell, Download, Mail, ShieldAlert } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, Student, WasteEntry } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { dateTime, grams, number, pct, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  const id = $pageStore.params.id;
  const tabs = ['overview', 'history', 'warnings'] as const;

  let loading = true;
  let error = '';
  let activeTab: 'overview' | 'history' | 'warnings' = 'overview';
  let period = '30d';
  let profile: Student | null = null;
  let stats: Record<string, unknown> | null = null;
  let timeline: {
    threshold_grams?: number;
    data: Array<{ date: string; total_grams: number; entry_count: number }>;
  } = { data: [] };
  let foodBreakdown: {
    data: Array<{ food_name: string; total_grams: number; percentage: number }>;
  } = { data: [] };
  let mealPattern: {
    data: Array<{ meal_type: string; avg_grams: number; entry_count: number }>;
  } = { data: [] };
  let improvement: {
    current_improvement_pct?: number;
    direction?: string;
    data: Array<{
      week_label: string;
      avg_grams: number;
      improvement_pct: number;
    }>;
  } = { data: [] };
  let history: Paginated<WasteEntry> = {
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 1
  };
  let warningLog: {
    warnings: Array<Record<string, unknown>>;
    penalties: Array<Record<string, unknown>>;
  } = { warnings: [], penalties: [] };
  let historyPage = 1;
  let warningOpen = false;
  let penaltyOpen = false;
  let notifyOpen = false;
  let warningForm = { level: 'level_1', reason: '', send_email: true };
  let penaltyForm = { points: 5, reason: '', send_email: true };
  let notificationForm = { subject: '', body: '', channel: 'dashboard' };

  async function loadProfile() {
    loading = true;
    error = '';
    try {
      const [
        profileData,
        statsData,
        timelineData,
        foodData,
        mealData,
        improvementData,
        historyData,
        warningData
      ] = await Promise.all([
        api.get<Student>(`/students/${id}`),
        api.get<Record<string, unknown>>(`/students/${id}/stats`, { period }),
        api.get<typeof timeline>(`/students/${id}/timeline`, { period }),
        api.get<typeof foodBreakdown>(`/students/${id}/food-breakdown`, {
          period
        }),
        api.get<typeof mealPattern>(`/students/${id}/meal-pattern`, { period }),
        api.get<typeof improvement>(`/students/${id}/improvement`),
        api.get<Paginated<WasteEntry>>(`/students/${id}/history`, {
          page: historyPage,
          size: 20
        }),
        api.get<typeof warningLog>(`/students/${id}/warnings`)
      ]);
      profile = profileData;
      stats = statsData;
      timeline = timelineData;
      foodBreakdown = foodData;
      mealPattern = mealData;
      improvement = improvementData;
      history = historyData;
      warningLog = warningData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load student profile';
    } finally {
      loading = false;
    }
  }

  async function loadHistory() {
    history = await api.get<Paginated<WasteEntry>>(`/students/${id}/history`, {
      page: historyPage,
      size: 20
    });
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

  async function sendNotification() {
    try {
      await api.post('/notifications', {
        type: 'custom',
        channel: notificationForm.channel,
        subject: notificationForm.subject,
        body: notificationForm.body,
        recipient_type: 'individual',
        recipient_ids: [id]
      });
      notify('Notification queued.', 'success');
      notifyOpen = false;
      notificationForm = { subject: '', body: '', channel: 'dashboard' };
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not send notification.',
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
  <title>Student Intelligence | CleanPlates</title>
</svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div class="flex min-w-0 items-center gap-3">
    <Button
      variant="secondary"
      on:click={() => goto('/dashboard/students')}
      id="btn-back-students"><ArrowLeft size={16} /></Button
    >
    <div class="min-w-0">
      <p class="label">Student intelligence</p>
      <h2 class="mt-1 truncate text-2xl font-semibold text-body">
        {profile?.mapping?.name ?? profile?.device_id ?? 'Student profile'}
      </h2>
    </div>
  </div>
  <div class="flex flex-wrap gap-2">
    <select
      class="select-field"
      bind:value={period}
      on:change={loadProfile}
      id="select-student-period"
    >
      <option value="7d">7d</option><option value="30d">30d</option><option
        value="semester">Semester</option
      ><option value="all">All</option>
    </select>
    <Button
      variant="secondary"
      on:click={() => (warningOpen = true)}
      id="btn-issue-warning"><ShieldAlert size={16} />Warning</Button
    >
    <Button
      variant="secondary"
      on:click={() => (penaltyOpen = true)}
      id="btn-issue-penalty"><Bell size={16} />Penalty</Button
    >
    <Button
      variant="secondary"
      on:click={() => (notifyOpen = true)}
      id="btn-send-notification"><Mail size={16} />Notify</Button
    >
    <Button on:click={exportProfile} id="btn-export-profile"
      ><Download size={16} />Export</Button
    >
  </div>
</div>

{#if error}
  <Card title="Student unavailable" description={error}
    ><Button on:click={loadProfile}>Retry</Button></Card
  >
{:else if loading && !profile}
  <div class="card h-96 animate-pulse bg-elevated"></div>
{:else if profile}
  <Card>
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-4">
        <div
          class="grid h-16 w-16 place-items-center rounded-lg bg-primary text-xl font-semibold text-white"
        >
          {(profile.mapping?.name ?? profile.device_id)
            .slice(0, 2)
            .toUpperCase()}
        </div>
        <div class="min-w-0">
          <h3 class="truncate text-xl font-semibold">
            {profile.mapping?.name ?? 'Unmapped student'}
          </h3>
          <p class="text-sm text-muted">
            {profile.mapping?.roll_number ?? profile.device_id}
          </p>
          <p class="mt-1 text-sm text-muted">
            {profile.mapping
              ? `${profile.mapping.branch} · Year ${profile.mapping.year} · ${profile.mapping.hostel ?? 'No hostel'}`
              : 'Map this card to unlock identity fields.'}
          </p>
        </div>
      </div>
      <StatusBadge value={profile.status} />
    </div>
  </Card>

  <div class="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <StatCard
      title="Avg Waste"
      value={grams(Number(stats?.avg_waste_grams ?? profile.avg_waste_grams))}
      helper={`${number(stats?.entry_count as number)} entries`}
    >
      <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Sustainability"
      value={number(profile.sustainability_score)}
      helper="Score"
    >
      <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Warnings"
      value={number(profile.warning_count)}
      helper="Active warnings"
      tone="warn"
    >
      <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Penalties"
      value={number(profile.penalty_count)}
      helper={`Improvement ${pct(improvement.current_improvement_pct)}`}
      tone="bad"
    >
      <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
    </StatCard>
  </div>

  <div class="mt-5 flex flex-wrap gap-2">
    {#each tabs as tab}
      <button
        class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === tab ? 'bg-primary text-ink' : 'bg-card text-muted hover:text-body'}`}
        on:click={() => (activeTab = tab)}
        id={`tab-${tab}`}>{titleCase(tab)}</button
      >
    {/each}
  </div>

  {#if activeTab === 'overview'}
    <div class="mt-5 grid gap-5 xl:grid-cols-2">
      <ChartCard
        title="Waste Timeline"
        chartType="line"
        labels={timeline.data.map((point) => point.date)}
        datasets={[
          {
            label: 'Waste',
            data: timeline.data.map((point) => point.total_grams),
            fill: true
          }
        ]}
      />
      <ChartCard
        title="Food Breakdown"
        chartType="doughnut"
        labels={foodBreakdown.data.map((item) => item.food_name)}
        datasets={[
          {
            label: 'Waste',
            data: foodBreakdown.data.map((item) => item.total_grams)
          }
        ]}
      />
      <ChartCard
        title="Meal Pattern"
        chartType="bar"
        labels={mealPattern.data.map((item) => titleCase(item.meal_type))}
        datasets={[
          {
            label: 'Avg grams',
            data: mealPattern.data.map((item) => item.avg_grams)
          }
        ]}
      />
      <ChartCard
        title="Improvement Tracker"
        chartType="line"
        labels={improvement.data.map((item) => item.week_label)}
        datasets={[
          {
            label: 'Improvement %',
            data: improvement.data.map((item) => item.improvement_pct)
          }
        ]}
      />
    </div>
  {:else if activeTab === 'history'}
    <Card class="mt-5" title="Waste history">
      {#if history.items.length === 0}
        <EmptyState title="No history" />
      {:else}
        <div class="overflow-auto">
          <table>
            <thead class="bg-elevated"
              ><tr
                ><th class="th">Time</th><th class="th">Meal</th><th class="th"
                  >Weight</th
                ><th class="th">Food</th><th class="th">Severity</th></tr
              ></thead
            >
            <tbody>
              {#each history.items as entry}
                <tr
                  ><td class="td">{dateTime(entry.timestamp)}</td><td class="td"
                    >{titleCase(entry.meal_type)}</td
                  ><td class="td">{grams(entry.weight_grams)}</td><td class="td"
                    >{entry.food_items?.map((item) => item.name).join(', ')}</td
                  ><td class="td"
                    ><StatusBadge value={entry.severity} compact /></td
                  ></tr
                >
              {/each}
            </tbody>
          </table>
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <Button
            size="sm"
            variant="secondary"
            disabled={historyPage <= 1}
            on:click={async () => {
              historyPage -= 1;
              await loadHistory();
            }}>Previous</Button
          >
          <Button
            size="sm"
            variant="secondary"
            disabled={historyPage >= history.pages}
            on:click={async () => {
              historyPage += 1;
              await loadHistory();
            }}>Next</Button
          >
        </div>
      {/if}
    </Card>
  {:else}
    <div class="mt-5 grid gap-5 xl:grid-cols-2">
      <Card title="Warnings">
        {#if warningLog.warnings.length === 0}<EmptyState />{:else}
          <div class="space-y-3">
            {#each warningLog.warnings as warning}<div
                class="rounded-lg border border-border p-3"
              >
                <div class="flex justify-between gap-3">
                  <p class="font-semibold">{warning.reason}</p>
                  <StatusBadge value={String(warning.status)} compact />
                </div>
                <p class="mt-1 text-xs text-muted">
                  {titleCase(String(warning.level))} · {dateTime(
                    String(warning.created_at)
                  )}
                </p>
              </div>{/each}
          </div>
        {/if}
      </Card>
      <Card title="Penalties">
        {#if warningLog.penalties.length === 0}<EmptyState />{:else}
          <div class="space-y-3">
            {#each warningLog.penalties as penalty}<div
                class="rounded-lg border border-border p-3"
              >
                <div class="flex justify-between gap-3">
                  <p class="font-semibold">{penalty.reason}</p>
                  <StatusBadge value={String(penalty.status)} compact />
                </div>
                <p class="mt-1 text-xs text-muted">
                  {number(penalty.points as number)} points · {dateTime(
                    String(penalty.created_at)
                  )}
                </p>
              </div>{/each}
          </div>
        {/if}
      </Card>
    </div>
  {/if}
{/if}

<Modal
  open={warningOpen}
  title="Issue warning"
  on:close={() => (warningOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={issueWarning}>
    <label
      ><span class="label">Level</span><select
        class="select-field mt-2 w-full"
        bind:value={warningForm.level}
        ><option value="level_1">Level 1</option><option value="level_2"
          >Level 2</option
        ><option value="level_3">Level 3</option></select
      ></label
    >
    <label
      ><span class="label">Reason</span><textarea
        class="textarea-field mt-2 min-h-28 w-full py-3"
        bind:value={warningForm.reason}
        required
      ></textarea></label
    >
    <label class="flex items-center gap-2 text-sm"
      ><input type="checkbox" bind:checked={warningForm.send_email} /> Send email</label
    >
    <div class="flex justify-end gap-2">
      <Button
        variant="secondary"
        type="button"
        on:click={() => (warningOpen = false)}>Cancel</Button
      ><Button type="submit">Issue warning</Button>
    </div>
  </form>
</Modal>

<Modal
  open={penaltyOpen}
  title="Apply penalty"
  on:close={() => (penaltyOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={issuePenalty}>
    <label
      ><span class="label">Points</span><input
        class="input-field mt-2 w-full"
        type="number"
        min="1"
        max="100"
        bind:value={penaltyForm.points}
      /></label
    >
    <label
      ><span class="label">Reason</span><textarea
        class="textarea-field mt-2 min-h-28 w-full py-3"
        bind:value={penaltyForm.reason}
        required
      ></textarea></label
    >
    <label class="flex items-center gap-2 text-sm"
      ><input type="checkbox" bind:checked={penaltyForm.send_email} /> Send email</label
    >
    <div class="flex justify-end gap-2">
      <Button
        variant="secondary"
        type="button"
        on:click={() => (penaltyOpen = false)}>Cancel</Button
      ><Button type="submit">Apply penalty</Button>
    </div>
  </form>
</Modal>

<Modal
  open={notifyOpen}
  title="Send notification"
  on:close={() => (notifyOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={sendNotification}>
    <label
      ><span class="label">Subject</span><input
        class="input-field mt-2 w-full"
        bind:value={notificationForm.subject}
        required
      /></label
    >
    <label
      ><span class="label">Channel</span><select
        class="select-field mt-2 w-full"
        bind:value={notificationForm.channel}
        ><option value="dashboard">Dashboard</option><option value="email"
          >Email</option
        ><option value="both">Both</option></select
      ></label
    >
    <label
      ><span class="label">Body</span><textarea
        class="textarea-field mt-2 min-h-28 w-full py-3"
        bind:value={notificationForm.body}
        required
      ></textarea></label
    >
    <div class="flex justify-end gap-2">
      <Button
        variant="secondary"
        type="button"
        on:click={() => (notifyOpen = false)}>Cancel</Button
      ><Button type="submit">Send</Button>
    </div>
  </form>
</Modal>
