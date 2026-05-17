<script lang="ts">
  import { onMount } from 'svelte';
  import { Download, RefreshCw, Search, ShieldCheck } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, number, shortDate, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type AuditEvent = {
    id: string;
    event_type: string;
    action: string;
    resource_type: string;
    resource_id?: string | null;
    user_name?: string | null;
    user_role?: string | null;
    ip_address?: string | null;
    summary: string;
    created_at: string;
  };

  let activeTab: 'table' | 'timeline' = 'table';
  let loading = true;
  let error = '';
  let stats = {
    total_today: 0,
    login_events: 0,
    config_changes: 0,
    rule_changes: 0,
    warning_events: 0
  };
  let events: Paginated<AuditEvent> = {
    items: [],
    total: 0,
    page: 1,
    size: 25,
    pages: 1
  };
  let timeline: {
    groups: Array<{ user_name: string; date: string; events: AuditEvent[] }>;
  } = { groups: [] };
  let detail:
    | (AuditEvent & {
        user_agent?: string | null;
        before_state?: Record<string, unknown> | null;
        after_state?: Record<string, unknown> | null;
        metadata?: Record<string, unknown> | null;
      })
    | null = null;
  let filters = {
    user_id: '',
    event_type: '',
    resource_type: '',
    date_from: '',
    date_to: '',
    q: '',
    sort: 'created_at',
    order: 'desc',
    page: 1,
    size: 25
  };

  function query() {
    return { ...filters, page: filters.page, size: filters.size };
  }

  async function loadAudit() {
    loading = true;
    error = '';
    try {
      const [eventData, statData, timelineData] = await Promise.all([
        api.get<Paginated<AuditEvent>>('/audit', query()),
        api.get<typeof stats>('/audit/stats'),
        api.get<typeof timeline>('/audit/timeline', query())
      ]);
      events = eventData;
      stats = statData;
      timeline = timelineData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load audit log';
    } finally {
      loading = false;
    }
  }

  async function openDetail(event: AuditEvent) {
    detail = event;
    try {
      detail = await api.get(`/audit/${event.id}`);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load event detail.',
        'error'
      );
    }
  }

  async function exportAudit() {
    try {
      await api.download('/audit/export', 'audit-log.csv', {
        ...query(),
        format: 'csv'
      });
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export audit log.',
        'error'
      );
    }
  }

  function sortBy(column: string) {
    if (filters.sort === column)
      filters.order = filters.order === 'asc' ? 'desc' : 'asc';
    else {
      filters.sort = column;
      filters.order = 'asc';
    }
    loadAudit();
  }

  onMount(loadAudit);
</script>

<svelte:head><title>Audit Log | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Audit log</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      System activity and change trail
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadAudit} id="btn-refresh-audit"
      ><RefreshCw size={16} />Refresh</Button
    ><Button on:click={exportAudit} id="btn-export-audit"
      ><Download size={16} />Export</Button
    >
  </div>
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
  <StatCard
    title="Events Today"
    value={number(stats.total_today)}
    helper="All audited events"
    ><svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Logins"
    value={number(stats.login_events)}
    helper="Auth activity"
    ><svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Config Changes"
    value={number(stats.config_changes)}
    helper="Settings edits"
    ><svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Rule Changes"
    value={number(stats.rule_changes)}
    helper="Automation edits"
    ><svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Warnings"
    value={number(stats.warning_events)}
    helper="Student events"
    ><svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment
    ></StatCard
  >
</div>

<Card class="mt-5" title="Filters">
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
    <label
      ><span class="label">User ID</span><input
        class="field mt-2 w-full"
        bind:value={filters.user_id}
        id="select-audit-user"
      /></label
    >
    <label
      ><span class="label">Event type</span><input
        class="field mt-2 w-full"
        bind:value={filters.event_type}
        id="select-audit-type"
        placeholder="config.updated"
      /></label
    >
    <label
      ><span class="label">Resource</span><input
        class="field mt-2 w-full"
        bind:value={filters.resource_type}
        id="select-audit-resource"
        placeholder="config"
      /></label
    >
    <label
      ><span class="label">From</span><input
        class="field mt-2 w-full"
        type="date"
        bind:value={filters.date_from}
      /></label
    >
    <label
      ><span class="label">To</span><input
        class="field mt-2 w-full"
        type="date"
        bind:value={filters.date_to}
      /></label
    >
    <label
      ><span class="label">Search</span><span
        class="mt-2 flex items-center gap-2 rounded-md border border-line bg-field px-3"
        ><Search size={15} class="text-muted" /><input
          class="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
          bind:value={filters.q}
          id="input-audit-search"
        /></span
      ></label
    >
  </div>
  <div class="mt-3 flex justify-end">
    <Button
      on:click={() => {
        filters.page = 1;
        loadAudit();
      }}>Apply</Button
    >
  </div>
</Card>

<div class="mt-5 flex gap-2">
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'table' ? 'bg-fresh text-white' : 'bg-white text-muted'}`}
    on:click={() => (activeTab = 'table')}
    id="tab-audit-table">Table</button
  >
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'timeline' ? 'bg-fresh text-white' : 'bg-white text-muted'}`}
    on:click={() => (activeTab = 'timeline')}
    id="tab-audit-timeline">Timeline</button
  >
</div>

<Card
  class="mt-5"
  title={activeTab === 'table' ? 'Audit events' : 'Activity timeline'}
>
  {#if error}<div
      class="rounded-md border border-coral/30 bg-coral/10 p-3 text-coral"
    >
      {error}
    </div>
  {:else if loading}<div
      class="h-96 animate-pulse rounded-lg bg-slate-100"
    ></div>
  {:else if activeTab === 'table'}
    {#if events.items.length === 0}<EmptyState title="No audit events" />{:else}
      <div class="overflow-auto">
        <table>
          <thead class="table-head"
            ><tr
              ><th class="table-cell"
                ><button on:click={() => sortBy('created_at')}>Time</button></th
              ><th class="table-cell">Event</th><th class="table-cell">User</th
              ><th class="table-cell">Resource</th><th class="table-cell"
                >Summary</th
              ><th class="table-cell">IP</th></tr
            ></thead
          ><tbody
            >{#each events.items as event}<tr
                class="cursor-pointer hover:bg-slate-50"
                on:click={() => openDetail(event)}
                ><td class="table-cell">{dateTime(event.created_at)}</td><td
                  class="table-cell"
                  ><StatusBadge value={event.event_type} compact /></td
                ><td class="table-cell"
                  >{event.user_name ?? 'System'}
                  <p class="text-xs text-muted">
                    {event.user_role ? titleCase(event.user_role) : ''}
                  </p></td
                ><td class="table-cell">{titleCase(event.resource_type)}</td><td
                  class="table-cell">{event.summary}</td
                ><td class="table-cell">{event.ip_address ?? 'n/a'}</td></tr
              >{/each}</tbody
          >
        </table>
      </div>
      <div
        class="mt-4 flex flex-wrap items-center justify-end gap-2"
        id="nav-audit-pagination"
      >
        <Button
          size="sm"
          variant="secondary"
          disabled={filters.page <= 1}
          on:click={() => {
            filters.page -= 1;
            loadAudit();
          }}>Previous</Button
        ><span class="text-sm text-muted"
          >Page {events.page} of {events.pages}</span
        ><Button
          size="sm"
          variant="secondary"
          disabled={filters.page >= events.pages}
          on:click={() => {
            filters.page += 1;
            loadAudit();
          }}>Next</Button
        ><select
          class="field"
          bind:value={filters.size}
          on:change={() => {
            filters.page = 1;
            loadAudit();
          }}
          id="select-audit-page-size"
          ><option value={25}>25</option><option value={50}>50</option><option
            value={100}>100</option
          ></select
        >
      </div>
    {/if}
  {:else if timeline.groups.length === 0}<EmptyState
      title="No timeline events"
    />{:else}
    <div class="space-y-4">
      {#each timeline.groups as group}<div
          class="rounded-lg border border-line p-4"
        >
          <p class="font-semibold">
            {group.user_name} · {shortDate(group.date)}
          </p>
          <div class="mt-3 space-y-2">
            {#each group.events as event}<button
                class="flex w-full items-start gap-3 rounded-md bg-slate-50 p-3 text-left"
                on:click={() => openDetail(event)}
                ><span class="mt-1 h-2 w-2 rounded-full bg-fresh"></span><span
                  ><span class="font-semibold">{event.summary}</span><span
                    class="block text-xs text-muted"
                    >{dateTime(event.created_at)} · {titleCase(
                      event.event_type
                    )}</span
                  ></span
                ></button
              >{/each}
          </div>
        </div>{/each}
    </div>
  {/if}
</Card>

<Modal
  open={!!detail}
  title={detail?.event_type ?? 'Audit event'}
  description={detail ? dateTime(detail.created_at) : ''}
  wide
  on:close={() => (detail = null)}
>
  {#if detail}
    <div class="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
      <div class="space-y-3 text-sm">
        <p><span class="label">Summary</span><br />{detail.summary}</p>
        <p><span class="label">Action</span><br />{detail.action}</p>
        <p>
          <span class="label">Resource</span><br />{detail.resource_type}
          {detail.resource_id ?? ''}
        </p>
        <p>
          <span class="label">User</span><br />{detail.user_name ?? 'System'} · {detail.user_role ??
            'n/a'}
        </p>
        <p>
          <span class="label">Agent</span><br />{detail.user_agent ?? 'n/a'}
        </p>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <pre
          class="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(
            detail.before_state ?? {},
            null,
            2
          )}</pre>
        <pre
          class="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(
            detail.after_state ?? detail.metadata ?? {},
            null,
            2
          )}</pre>
      </div>
    </div>
  {/if}
</Modal>
