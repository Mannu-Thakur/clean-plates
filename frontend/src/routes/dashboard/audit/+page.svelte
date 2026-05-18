<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Download,
    Eye,
    RefreshCw,
    Search,
    ShieldCheck
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, User } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import Pagination from '$lib/components/ui/Pagination.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { notify } from '$lib/stores/toast';
  import { dateTime, number, titleCase } from '$lib/utils/format';

  type AuditEvent = {
    id: string;
    event_type: string;
    action: string;
    resource_type: string;
    resource_id?: string | null;
    user_id?: string | null;
    user_name?: string | null;
    user_role?: string | null;
    ip_address?: string | null;
    summary: string;
    created_at: string;
  };
  type AuditDetail = AuditEvent & {
    user_agent?: string | null;
    before_state?: Record<string, unknown> | null;
    after_state?: Record<string, unknown> | null;
    metadata?: Record<string, unknown> | null;
  };
  type AuditStats = {
    total_today?: number;
    login_events?: number;
    config_changes?: number;
    rule_changes?: number;
    warning_events?: number;
    total_events?: number;
    events_today?: number;
    failed_events?: number;
    unique_users?: number;
  };

  const actionOptions = [
    'append',
    'classify',
    'create',
    'create_audit_log',
    'decommission',
    'delete',
    'duplicate',
    'escalate',
    'execute',
    'export',
    'import',
    'login',
    'logout',
    'reset',
    'restart',
    'restore',
    'retry',
    'review',
    'revoke',
    'resolve',
    'send_email',
    'skip',
    'sync',
    'toggle',
    'update'
  ];
  const resourceOptions = [
    'audit',
    'backup',
    'cache',
    'config',
    'database',
    'device',
    'escalation',
    'filter_preset',
    'notification',
    'penalty',
    'report',
    'report_schedule',
    'role',
    'rule',
    'student',
    'student_mapping',
    'template',
    'user',
    'warning'
  ];

  let loading = true;
  let error = '';
  let users: User[] = [];
  let stats: AuditStats = {};
  let events: Paginated<AuditEvent> = {
    items: [],
    total: 0,
    page: 1,
    size: 25,
    pages: 1
  };
  let filters = {
    user_id: '',
    action: '',
    resource_type: '',
    date_from: '',
    date_to: '',
    q: '',
    sort: 'created_at',
    order: 'desc',
    page: 1,
    size: 25
  };
  let detail: AuditDetail | null = null;
  let diffEvent: AuditDetail | null = null;

  $: statCards = [
    {
      title: 'Events Today',
      value: stats.events_today ?? stats.total_today ?? 0,
      helper: 'Audited today'
    },
    {
      title: 'Logins',
      value: stats.login_events ?? 0,
      helper: 'Auth activity'
    },
    {
      title: 'Config Changes',
      value: stats.config_changes ?? 0,
      helper: 'Configuration edits'
    },
    {
      title: 'Rule Changes',
      value: stats.rule_changes ?? 0,
      helper: 'Automation edits'
    },
    {
      title: 'Warnings',
      value: stats.warning_events ?? stats.failed_events ?? 0,
      helper: 'Warning events'
    }
  ];
  $: diffKeys = Array.from(
    new Set([
      ...Object.keys(diffEvent?.before_state ?? {}),
      ...Object.keys(diffEvent?.after_state ?? {})
    ])
  ).sort();

  function query() {
    return {
      user_id: filters.user_id,
      action: filters.action,
      resource_type: filters.resource_type,
      date_from: filters.date_from,
      date_to: filters.date_to,
      q: filters.q,
      sort: filters.sort,
      order: filters.order,
      page: filters.page,
      size: filters.size
    };
  }

  async function loadAudit() {
    loading = true;
    error = '';
    try {
      const [eventData, statData, userData] = await Promise.all([
        api.get<Paginated<AuditEvent>>('/audit/', query()),
        api.get<AuditStats>('/audit/stats'),
        api.get<User[]>('/settings/users').catch(() => [])
      ]);
      events = eventData;
      stats = statData;
      users = userData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load audit log.';
    } finally {
      loading = false;
    }
  }

  async function openDetail(event: AuditEvent) {
    detail = event as AuditDetail;
    try {
      detail = await api.get<AuditDetail>(`/audit/${event.id}`);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load event detail.',
        'error'
      );
    }
  }

  async function openDiff(event: AuditEvent) {
    try {
      diffEvent = await api.get<AuditDetail>(`/audit/${event.id}`);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load event diff.',
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

  function applyFilters() {
    filters.page = 1;
    loadAudit();
  }

  function resetFilters() {
    filters = {
      user_id: '',
      action: '',
      resource_type: '',
      date_from: '',
      date_to: '',
      q: '',
      sort: 'created_at',
      order: 'desc',
      page: 1,
      size: filters.size
    };
    loadAudit();
  }

  function sortBy(column: string) {
    if (filters.sort === column) {
      filters.order = filters.order === 'asc' ? 'desc' : 'asc';
    } else {
      filters.sort = column;
      filters.order = 'asc';
    }
    loadAudit();
  }

  function pageTo(page: number) {
    filters.page = page;
    loadAudit();
  }

  function eventStatus(event: AuditEvent) {
    const value = `${event.event_type} ${event.action}`.toLowerCase();
    if (value.includes('failed') || value.includes('error')) return 'failed';
    return 'success';
  }

  function actionToneClass(action: string) {
    const normalized = action.toLowerCase();
    if (['create', 'register'].includes(normalized)) return 'badge-up';
    if (['update', 'patch', 'execute'].includes(normalized))
      return 'badge-info';
    if (['delete', 'decommission'].includes(normalized)) return 'badge-down';
    if (['reset', 'export', 'restore'].includes(normalized))
      return 'badge-primary';
    return 'badge-muted';
  }

  function json(value: unknown) {
    return JSON.stringify(value ?? {}, null, 2);
  }

  function changed(key: string) {
    return (
      json(diffEvent?.before_state?.[key]) !==
      json(diffEvent?.after_state?.[key])
    );
  }

  onMount(loadAudit);
</script>

<svelte:head><title>Audit Log | CleanPlates</title></svelte:head>

<PageHeader
  label="Audit log"
  title="System activity trail"
  description="Review administrative actions, configuration changes, and backend maintenance events."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={loadAudit}
      disabled={loading}
      id="btn-refresh-audit"
    >
      <RefreshCw size={16} />Refresh
    </Button>
    <Button on:click={exportAudit} id="btn-export-audit">
      <Download size={16} />Export CSV
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
  {#each statCards as card}
    <StatCard
      title={card.title}
      value={number(card.value)}
      helper={card.helper}
    >
      <svelte:fragment slot="icon"><ShieldCheck size={19} /></svelte:fragment>
    </StatCard>
  {/each}
</div>

<Card class="mt-5" title="Filters">
  <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
    <label>
      <span class="form-label">Search</span>
      <span
        class="flex items-center gap-2 rounded-md border border-border bg-elevated px-3"
      >
        <Search size={15} class="text-muted" />
        <input
          class="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
          bind:value={filters.q}
          id="input-audit-search"
        />
      </span>
    </label>
    <label>
      <span class="form-label">Action</span>
      <select
        class="select-field"
        bind:value={filters.action}
        id="select-audit-type"
      >
        <option value="">All actions</option>
        {#each actionOptions as action}
          <option value={action}>{titleCase(action)}</option>
        {/each}
      </select>
    </label>
    <label>
      <span class="form-label">Resource</span>
      <select
        class="select-field"
        bind:value={filters.resource_type}
        id="select-audit-resource"
      >
        <option value="">All resources</option>
        {#each resourceOptions as resource}
          <option value={resource}>{titleCase(resource)}</option>
        {/each}
      </select>
    </label>
    <label>
      <span class="form-label">User</span>
      <select
        class="select-field"
        bind:value={filters.user_id}
        id="select-audit-user"
      >
        <option value="">All users</option>
        {#each users as user}
          <option value={user.id}>{user.name} ({user.email})</option>
        {/each}
      </select>
    </label>
    <label>
      <span class="form-label">From</span>
      <input class="input-field" type="date" bind:value={filters.date_from} />
    </label>
    <label>
      <span class="form-label">To</span>
      <input class="input-field" type="date" bind:value={filters.date_to} />
    </label>
  </div>
  <div class="mt-4 flex flex-wrap justify-end gap-2">
    <Button variant="ghost" on:click={resetFilters}>Reset</Button>
    <Button on:click={applyFilters}>Apply</Button>
  </div>
</Card>

<Card class="mt-5" title="Audit events">
  {#if error}
    <div
      class="rounded-md border border-down/30 bg-down/10 p-4 text-sm text-down"
    >
      {error}
    </div>
  {:else if loading}
    <div class="h-96 skeleton"></div>
  {:else if events.items.length === 0}
    <EmptyState title="No audit events" />
  {:else}
    <div class="overflow-auto rounded-lg border border-border">
      <table>
        <thead class="bg-elevated">
          <tr>
            <th class="th">
              <button type="button" on:click={() => sortBy('created_at')}
                >Time</button
              >
            </th>
            <th class="th">Actor</th>
            <th class="th">
              <button type="button" on:click={() => sortBy('action')}
                >Action</button
              >
            </th>
            <th class="th">
              <button type="button" on:click={() => sortBy('resource_type')}
                >Resource</button
              >
            </th>
            <th class="th">IP</th>
            <th class="th">Status</th>
            <th class="th text-right">Changes</th>
          </tr>
        </thead>
        <tbody>
          {#each events.items as event}
            <tr class="tr-hover" on:click={() => openDetail(event)}>
              <td class="td whitespace-nowrap">{dateTime(event.created_at)}</td>
              <td class="td">
                <span class="font-semibold">{event.user_name ?? 'System'}</span>
                <span class="mt-1 block text-xs text-muted">
                  {event.user_role ? titleCase(event.user_role) : 'Service'}
                </span>
              </td>
              <td class="td">
                <span class={actionToneClass(event.action)}
                  >{titleCase(event.action)}</span
                >
                <span class="mt-1 block text-xs text-muted"
                  >{event.event_type}</span
                >
              </td>
              <td class="td">
                <span class="font-semibold"
                  >{titleCase(event.resource_type)}</span
                >
                <span class="mt-1 block max-w-44 truncate text-xs text-muted">
                  {event.resource_id ?? 'n/a'}
                </span>
              </td>
              <td class="td">{event.ip_address ?? 'n/a'}</td>
              <td class="td"
                ><StatusBadge value={eventStatus(event)} compact /></td
              >
              <td class="td text-right" on:click|stopPropagation>
                <button
                  class="icon-btn"
                  type="button"
                  aria-label="View change diff"
                  on:click={() => openDiff(event)}
                >
                  <Eye size={16} />
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <Pagination
      page={events.page}
      total={events.total}
      pageSize={events.size}
      onChange={pageTo}
    />
  {/if}
</Card>

<Modal
  open={!!detail}
  title="Audit event details"
  description={detail ? dateTime(detail.created_at) : ''}
  wide
  on:close={() => (detail = null)}
>
  {#if detail}
    <div class="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
      <div class="space-y-3 text-sm">
        <p><span class="label">ID</span><br />{detail.id}</p>
        <p>
          <span class="label">Actor</span><br />{detail.user_name ?? 'System'}
        </p>
        <p>
          <span class="label">Action</span><br />{detail.action} / {detail.event_type}
        </p>
        <p>
          <span class="label">Resource</span><br />{detail.resource_type}
          {detail.resource_id ? `#${detail.resource_id}` : ''}
        </p>
        <p>
          <span class="label">IP address</span><br />{detail.ip_address ??
            'n/a'}
        </p>
        <p>
          <span class="label">User agent</span><br />{detail.user_agent ??
            'n/a'}
        </p>
        <p><span class="label">Summary</span><br />{detail.summary}</p>
      </div>
      <div class="space-y-4">
        <div>
          <p class="label mb-2">Request / metadata</p>
          <pre
            class="max-h-56 overflow-auto rounded-lg bg-canvas p-4 text-xs text-body">{json(
              detail.metadata
            )}</pre>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <p class="label mb-2">Before</p>
            <pre
              class="max-h-80 overflow-auto rounded-lg bg-canvas p-4 text-xs text-body">{json(
                detail.before_state
              )}</pre>
          </div>
          <div>
            <p class="label mb-2">After</p>
            <pre
              class="max-h-80 overflow-auto rounded-lg bg-canvas p-4 text-xs text-body">{json(
                detail.after_state
              )}</pre>
          </div>
        </div>
      </div>
    </div>
  {/if}
</Modal>

<Modal
  open={!!diffEvent}
  title="Change diff"
  description={diffEvent
    ? `${diffEvent.event_type} - ${dateTime(diffEvent.created_at)}`
    : ''}
  wide
  on:close={() => (diffEvent = null)}
>
  {#if diffEvent}
    {#if diffKeys.length === 0}
      <EmptyState title="No state payload" />
    {:else}
      <div class="overflow-auto rounded-lg border border-border">
        <table>
          <thead class="bg-elevated">
            <tr>
              <th class="th">Key</th>
              <th class="th">Before</th>
              <th class="th">After</th>
            </tr>
          </thead>
          <tbody>
            {#each diffKeys as key}
              <tr class={changed(key) ? 'bg-primary/5' : ''}>
                <td class="td font-mono text-xs">{key}</td>
                <td
                  class={`td font-mono text-xs ${changed(key) ? 'text-down' : 'text-muted'}`}
                >
                  <pre>{json(diffEvent.before_state?.[key])}</pre>
                </td>
                <td
                  class={`td font-mono text-xs ${changed(key) ? 'text-up' : 'text-muted'}`}
                >
                  <pre>{json(diffEvent.after_state?.[key])}</pre>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</Modal>
