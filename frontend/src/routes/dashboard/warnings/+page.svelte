<script lang="ts">
  import { onMount } from 'svelte';
  import { Download, RefreshCw, ShieldAlert } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type Warning = {
    id: string;
    student_id: string;
    student_name?: string | null;
    level: string;
    reason: string;
    status: string;
    created_at: string;
  };
  type Penalty = {
    id: string;
    student_id: string;
    student_name?: string | null;
    points: number;
    reason: string;
    status: string;
    created_at: string;
  };
  type Escalation = {
    id: string;
    warning_id: string;
    student_id: string;
    reason: string;
    escalated_to_role: string;
    status: string;
    created_at: string;
  };

  let activeTab: 'warnings' | 'escalations' | 'penalties' = 'warnings';
  let loading = true;
  let error = '';
  let stats = {
    total_warnings: 0,
    active_warnings: 0,
    pending_escalations: 0,
    total_penalties: 0
  };
  let warnings: Paginated<Warning> = {
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 1
  };
  let penalties: Paginated<Penalty> = {
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 1
  };
  let escalations: Escalation[] = [];
  let filters = { status: 'active', level: '', date_from: '', date_to: '' };
  let selected = new Set<string>();

  async function loadWarnings() {
    loading = true;
    error = '';
    try {
      const [statData, warningData, penaltyData, escalationData] =
        await Promise.all([
          api.get<typeof stats>('/warnings/stats'),
          api.get<Paginated<Warning>>('/warnings', filters),
          api.get<Paginated<Penalty>>('/penalties', { status: filters.status }),
          api.get<Escalation[]>('/escalations', {
            status: activeTab === 'escalations' ? filters.status : 'pending'
          })
        ]);
      stats = statData;
      warnings = warningData;
      penalties = penaltyData;
      escalations = escalationData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load warnings';
    } finally {
      loading = false;
    }
  }

  async function resolveWarning(id: string) {
    const resolution_note = window.prompt('Resolution note');
    if (!resolution_note) return;
    try {
      await api.patch(`/warnings/${id}/resolve`, { resolution_note });
      notify('Warning resolved.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not resolve warning.',
        'error'
      );
    }
  }

  async function escalateWarning(id: string) {
    const reason = window.prompt('Escalation reason');
    if (!reason) return;
    try {
      await api.post(`/warnings/${id}/escalate`, {
        escalated_to_role: 'institution_admin',
        reason
      });
      notify('Warning escalated.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not escalate warning.',
        'error'
      );
    }
  }

  async function applyPenalty(id: string) {
    if (!window.confirm('Apply penalty for this warning?')) return;
    try {
      await api.post(`/warnings/${id}/apply-penalty`);
      notify('Penalty applied.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not apply penalty.',
        'error'
      );
    }
  }

  async function revokePenalty(id: string) {
    const reason = window.prompt('Reason for revoking penalty');
    if (!reason) return;
    try {
      await api.patch(`/penalties/${id}/revoke`, { reason });
      notify('Penalty revoked.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not revoke penalty.',
        'error'
      );
    }
  }

  async function reviewEscalation(
    id: string,
    decision: 'approved' | 'rejected'
  ) {
    const review_note = window.prompt(`${titleCase(decision)} note`) ?? '';
    try {
      await api.post(`/escalations/${id}/review`, { decision, review_note });
      notify('Escalation reviewed.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not review escalation.',
        'error'
      );
    }
  }

  async function bulkResolve() {
    const warning_ids = Array.from(selected);
    if (warning_ids.length === 0) return;
    const resolution_note = window.prompt(
      'Resolution note for selected warnings'
    );
    if (!resolution_note) return;
    try {
      await api.patch('/warnings/bulk/resolve', {
        warning_ids,
        resolution_note
      });
      selected = new Set();
      notify('Selected warnings resolved.', 'success');
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Bulk resolve failed.',
        'error'
      );
    }
  }

  async function exportWarnings() {
    try {
      await api.download('/warnings/export', 'warnings.csv', {
        format: 'csv',
        ...filters
      });
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export warnings.',
        'error'
      );
    }
  }

  function toggle(id: string) {
    selected = new Set(selected);
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
  }

  onMount(loadWarnings);
</script>

<svelte:head><title>Warnings | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Warnings and penalties</p>
    <h2 class="mt-1 text-2xl font-semibold text-body">
      Enforcement management
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadWarnings}
      ><RefreshCw size={16} />Refresh</Button
    >
    <Button on:click={exportWarnings} id="btn-export-warnings"
      ><Download size={16} />Export</Button
    >
  </div>
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Total Warnings"
    value={number(stats.total_warnings)}
    helper="All time"
    ><svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Active Warnings"
    value={number(stats.active_warnings)}
    helper="Open cases"
    tone="warn"
    ><svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Escalations"
    value={number(stats.pending_escalations)}
    helper="Pending review"
    tone="hot"
    ><svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Penalties"
    value={number(stats.total_penalties)}
    helper="Total active/revoked"
    tone="bad"
    ><svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment
    ></StatCard
  >
</div>

<Card class="mt-5" title="Filters">
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
    <label
      ><span class="label">Status</span><select
        class="select-field mt-2 w-full"
        bind:value={filters.status}
        id="select-warning-status"
        ><option value="">All</option><option>active</option><option
          >resolved</option
        ><option>escalated</option><option>converted_to_penalty</option></select
      ></label
    >
    <label
      ><span class="label">Priority</span><select
        class="select-field mt-2 w-full"
        bind:value={filters.level}
        id="select-warning-priority"
        ><option value="">All</option><option value="level_1">Level 1</option
        ><option value="level_2">Level 2</option><option value="level_3"
          >Level 3</option
        ></select
      ></label
    >
    <label
      ><span class="label">From</span><input
        class="input-field mt-2 w-full"
        type="date"
        bind:value={filters.date_from}
      /></label
    >
    <label
      ><span class="label">To</span><input
        class="input-field mt-2 w-full"
        type="date"
        bind:value={filters.date_to}
      /></label
    >
    <div class="flex items-end">
      <Button class="w-full" on:click={loadWarnings}>Apply</Button>
    </div>
  </div>
</Card>

<div class="mt-5 flex flex-wrap gap-2">
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'warnings' ? 'bg-primary text-ink' : 'bg-card text-muted'}`}
    on:click={() => (activeTab = 'warnings')}
    id="tab-active-warnings">Active Warnings</button
  >
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'escalations' ? 'bg-primary text-ink' : 'bg-card text-muted'}`}
    on:click={() => (activeTab = 'escalations')}
    id="tab-escalations">Escalations</button
  >
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'penalties' ? 'bg-primary text-ink' : 'bg-card text-muted'}`}
    on:click={() => (activeTab = 'penalties')}>Penalties</button
  >
</div>

<Card
  class="mt-5"
  title={activeTab === 'warnings'
    ? 'Warnings table'
    : activeTab === 'escalations'
      ? 'Escalation queue'
      : 'Penalties table'}
>
  {#if error}
    <div class="rounded-md border border-down/30 bg-down/10 p-3 text-down">
      {error}
    </div>
  {:else if loading}
    <div class="h-96 animate-pulse rounded-lg bg-elevated"></div>
  {:else if activeTab === 'warnings'}
    {#if warnings.items.length === 0}<EmptyState />{:else}
      <div class="overflow-auto">
        <table>
          <thead class="bg-elevated"
            ><tr
              ><th class="th"></th><th class="th">Student</th><th class="th"
                >Level</th
              ><th class="th">Reason</th><th class="th">Status</th><th
                class="th">Created</th
              ><th class="th">Actions</th></tr
            ></thead
          >
          <tbody
            >{#each warnings.items as warning}<tr
                ><td class="td"
                  ><input
                    type="checkbox"
                    checked={selected.has(warning.id)}
                    on:change={() => toggle(warning.id)}
                  /></td
                ><td class="td"
                  ><a
                    class="font-semibold text-primary"
                    href={`/dashboard/students/${warning.student_id}`}
                    >{warning.student_name ?? warning.student_id}</a
                  ></td
                ><td class="td">{titleCase(warning.level)}</td><td class="td"
                  >{warning.reason}</td
                ><td class="td"
                  ><StatusBadge value={warning.status} compact /></td
                ><td class="td">{dateTime(warning.created_at)}</td><td
                  class="td"
                  ><div class="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      on:click={() => resolveWarning(warning.id)}
                      id={`btn-resolve-${warning.id}`}>Resolve</Button
                    ><Button
                      size="sm"
                      variant="secondary"
                      on:click={() => escalateWarning(warning.id)}
                      id={`btn-escalate-${warning.id}`}>Escalate</Button
                    ><Button
                      size="sm"
                      variant="secondary"
                      on:click={() => applyPenalty(warning.id)}
                      id={`btn-apply-penalty-${warning.id}`}>Penalty</Button
                    >
                  </div></td
                ></tr
              >{/each}</tbody
          >
        </table>
      </div>
      <div class="mt-4 flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          on:click={bulkResolve}
          disabled={selected.size === 0}
          id="btn-bulk-resolve">Bulk resolve</Button
        ><Button
          variant="secondary"
          size="sm"
          disabled={selected.size === 0}
          id="btn-bulk-escalate"
          on:click={() =>
            notify('Use row escalation to choose a target role.', 'info')}
          >Bulk escalate</Button
        >
      </div>
    {/if}
  {:else if activeTab === 'escalations'}
    {#if escalations.length === 0}<EmptyState title="No escalations" />{:else}
      <div class="space-y-3">
        {#each escalations as escalation}<div
            class="rounded-lg border border-border p-4"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="font-semibold">{escalation.reason}</p>
                <p class="mt-1 text-sm text-muted">
                  To {titleCase(escalation.escalated_to_role)} · {dateTime(
                    escalation.created_at
                  )}
                </p>
              </div>
              <StatusBadge value={escalation.status} />
            </div>
            <div class="mt-3 flex gap-2">
              <Button
                size="sm"
                on:click={() => reviewEscalation(escalation.id, 'approved')}
                >Approve</Button
              ><Button
                size="sm"
                variant="secondary"
                on:click={() => reviewEscalation(escalation.id, 'rejected')}
                >Reject</Button
              >
            </div>
          </div>{/each}
      </div>
    {/if}
  {:else if penalties.items.length === 0}<EmptyState
      title="No penalties"
    />{:else}
    <div class="overflow-auto">
      <table>
        <thead class="bg-elevated"
          ><tr
            ><th class="th">Student</th><th class="th">Points</th><th class="th"
              >Reason</th
            ><th class="th">Status</th><th class="th">Created</th><th class="th"
              >Actions</th
            ></tr
          ></thead
        ><tbody
          >{#each penalties.items as penalty}<tr
              ><td class="td"
                ><a
                  class="font-semibold text-primary"
                  href={`/dashboard/students/${penalty.student_id}`}
                  >{penalty.student_name ?? penalty.student_id}</a
                ></td
              ><td class="td">{number(penalty.points)}</td><td class="td"
                >{penalty.reason}</td
              ><td class="td"><StatusBadge value={penalty.status} compact /></td
              ><td class="td">{dateTime(penalty.created_at)}</td><td class="td"
                ><Button
                  size="sm"
                  variant="secondary"
                  on:click={() => revokePenalty(penalty.id)}
                  id={`btn-revoke-penalty-${penalty.id}`}>Revoke</Button
                ></td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
  {/if}
</Card>
