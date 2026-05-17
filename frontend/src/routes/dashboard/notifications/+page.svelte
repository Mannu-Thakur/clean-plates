<script lang="ts">
  import { onMount } from 'svelte';
  import { Bell, Edit3, RefreshCw, Send } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { NotificationItem, Paginated } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type Template = {
    id: string;
    name: string;
    subject: string;
    body_html: string;
    variables: string[];
  };
  type Delivery = {
    total_recipients: number;
    delivered: number;
    failed: number;
    pending: number;
    deliveries: Array<Record<string, unknown>>;
  };

  let activeTab: 'inbox' | 'sent' | 'scheduled' | 'broadcast' = 'inbox';
  let loading = true;
  let error = '';
  let notifications: Paginated<NotificationItem> = {
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 1
  };
  let stats = { unread: 0, sent_today: 0, failed: 0, pending: 0 };
  let templates: Template[] = [];
  let filters = { type: '', channel: '' };
  let composeOpen = false;
  let detailOpen = false;
  let selected:
    | (NotificationItem & { body?: string; recipient_ids?: string[] })
    | null = null;
  let delivery: Delivery | null = null;
  let form = {
    subject: '',
    body: '',
    type: 'custom',
    channel: 'dashboard',
    recipient_type: 'all',
    recipient_ids: '',
    template_id: '',
    scheduled_at: ''
  };

  async function loadNotifications() {
    loading = true;
    error = '';
    try {
      const [listData, statData, templateData] = await Promise.all([
        api.get<Paginated<NotificationItem>>('/notifications', {
          tab: activeTab,
          ...filters
        }),
        api.get<typeof stats>('/notifications/stats'),
        api.get<Template[]>('/templates')
      ]);
      notifications = listData;
      stats = statData;
      templates = templateData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load notifications';
    } finally {
      loading = false;
    }
  }

  function useTemplate() {
    const template = templates.find((item) => item.id === form.template_id);
    if (!template) return;
    form.subject = template.subject;
    form.body = template.body_html.replace(/<[^>]*>/g, ' ');
  }

  async function submitNotification(schedule = false, broadcast = false) {
    try {
      const recipient_ids = form.recipient_ids
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      if (broadcast) {
        await api.post('/notifications/broadcast', {
          subject: form.subject,
          body: form.body,
          channel: form.channel,
          recipient_type: form.recipient_type,
          recipient_filter: {},
          template_id: form.template_id || null
        });
      } else if (schedule) {
        await api.post('/notifications/schedule', {
          type: form.type,
          channel: form.channel,
          subject: form.subject,
          body: form.body,
          recipient_type: form.recipient_type,
          recipient_ids,
          template_id: form.template_id || null,
          scheduled_at: form.scheduled_at
        });
      } else {
        await api.post('/notifications', {
          type: form.type,
          channel: form.channel,
          subject: form.subject,
          body: form.body,
          recipient_type: form.recipient_type,
          recipient_ids,
          template_id: form.template_id || null
        });
      }
      notify(
        broadcast
          ? 'Broadcast queued.'
          : schedule
            ? 'Notification scheduled.'
            : 'Notification sent.',
        'success'
      );
      composeOpen = false;
      await loadNotifications();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not submit notification.',
        'error'
      );
    }
  }

  async function openDetail(notification: NotificationItem) {
    detailOpen = true;
    selected = notification;
    delivery = null;
    try {
      selected = await api.get(`/notifications/${notification.id}`);
      delivery = await api.get<Delivery>(
        `/notifications/${notification.id}/delivery`
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load delivery detail.',
        'error'
      );
    }
  }

  async function markRead(id: string) {
    await api.patch(`/notifications/${id}/read`);
    await loadNotifications();
  }

  async function markAllRead() {
    await api.post('/notifications/mark-all-read');
    notify('All notifications marked read.', 'success');
    await loadNotifications();
  }

  async function deleteNotification(id: string) {
    if (!window.confirm('Delete this notification?')) return;
    await api.delete(`/notifications/${id}`);
    notify('Notification deleted.', 'success');
    await loadNotifications();
  }

  async function retry(id: string) {
    await api.post(`/notifications/${id}/retry`);
    notify('Retry queued.', 'success');
    await loadNotifications();
  }

  onMount(loadNotifications);
</script>

<svelte:head><title>Notifications | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Notification center</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      Inbox, broadcasts, and scheduled messages
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadNotifications}
      ><RefreshCw size={16} />Refresh</Button
    ><Button variant="secondary" on:click={markAllRead} id="btn-mark-all-read"
      >Mark all read</Button
    ><Button on:click={() => (composeOpen = true)} id="btn-compose-notification"
      ><Edit3 size={16} />Compose</Button
    >
  </div>
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard title="Unread" value={number(stats.unread)} helper="Inbox"
    ><svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Sent Today"
    value={number(stats.sent_today)}
    helper="Dispatched"
    tone="good"
    ><svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Failed"
    value={number(stats.failed)}
    helper="Needs retry"
    tone="bad"
    ><svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Pending"
    value={number(stats.pending)}
    helper="Scheduled or queued"
    tone="warn"
    ><svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment></StatCard
  >
</div>

<Card class="mt-5" title="Filters">
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
    <label
      ><span class="label">Type</span><select
        class="field mt-2 w-full"
        bind:value={filters.type}
        id="select-notif-type"
        ><option value="">All</option><option>warning</option><option
          >penalty</option
        ><option>alert</option><option>system</option><option>custom</option
        ></select
      ></label
    >
    <label
      ><span class="label">Channel</span><select
        class="field mt-2 w-full"
        bind:value={filters.channel}
        id="select-notif-channel"
        ><option value="">All</option><option>email</option><option
          >dashboard</option
        ><option>both</option></select
      ></label
    >
    <div class="flex items-end">
      <Button on:click={loadNotifications}>Apply</Button>
    </div>
  </div>
</Card>

<div class="mt-5 flex flex-wrap gap-2">
  {#each ['inbox', 'sent', 'scheduled', 'broadcast'] as tab}
    <button
      class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === tab ? 'bg-fresh text-white' : 'bg-white text-muted'}`}
      on:click={() => {
        activeTab = tab as typeof activeTab;
        loadNotifications();
      }}>{titleCase(tab)}</button
    >
  {/each}
</div>

<Card class="mt-5" title="Notification list">
  {#if error}<div
      class="rounded-md border border-coral/30 bg-coral/10 p-3 text-coral"
    >
      {error}
    </div>
  {:else if loading}<div
      class="h-96 animate-pulse rounded-lg bg-slate-100"
    ></div>
  {:else if notifications.items.length === 0}<EmptyState
      title="No notifications"
    />
  {:else}
    <div class="space-y-3">
      {#each notifications.items as item}
        <div
          class={`rounded-lg border p-4 ${item.is_read ? 'border-line bg-white' : 'border-fresh/30 bg-fresh/5'}`}
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <button class="min-w-0 text-left" on:click={() => openDetail(item)}>
              <p class="truncate font-semibold text-ink">{item.subject}</p>
              <p class="mt-1 text-sm text-muted">
                {titleCase(item.type)} · {titleCase(item.channel)} · {dateTime(
                  item.created_at
                )}
              </p>
            </button>
            <div class="flex flex-wrap gap-2">
              <StatusBadge value={item.status} compact />
              <Button
                size="sm"
                variant="secondary"
                on:click={() => markRead(item.id)}
                id={`btn-mark-read-${item.id}`}>Read</Button
              >
              {#if item.status === 'failed'}<Button
                  size="sm"
                  variant="secondary"
                  on:click={() => retry(item.id)}
                  id={`btn-retry-${item.id}`}>Retry</Button
                >{/if}
              <Button
                size="sm"
                variant="danger"
                on:click={() => deleteNotification(item.id)}
                id={`btn-delete-notification-${item.id}`}>Delete</Button
              >
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</Card>

<Modal
  open={composeOpen}
  title="Compose notification"
  description="Send now, broadcast to a group, or schedule for later."
  wide
  on:close={() => (composeOpen = false)}
>
  <form
    class="grid gap-4 lg:grid-cols-2"
    on:submit|preventDefault={() => submitNotification(false, false)}
  >
    <label
      ><span class="label">Subject</span><input
        class="field mt-2 w-full"
        bind:value={form.subject}
        required
      /></label
    >
    <label
      ><span class="label">Template</span><select
        class="field mt-2 w-full"
        bind:value={form.template_id}
        on:change={useTemplate}
        ><option value="">None</option>{#each templates as template}<option
            value={template.id}>{template.name}</option
          >{/each}</select
      ></label
    >
    <label
      ><span class="label">Type</span><select
        class="field mt-2 w-full"
        bind:value={form.type}
        ><option>custom</option><option>warning</option><option>penalty</option
        ><option>alert</option><option>system</option></select
      ></label
    >
    <label
      ><span class="label">Channel</span><select
        class="field mt-2 w-full"
        bind:value={form.channel}
        ><option>dashboard</option><option>email</option><option>both</option
        ></select
      ></label
    >
    <label
      ><span class="label">Recipients</span><select
        class="field mt-2 w-full"
        bind:value={form.recipient_type}
        ><option>all</option><option>individual</option><option>branch</option
        ><option>hostel</option><option>year</option></select
      ></label
    >
    <label
      ><span class="label">Recipient IDs</span><input
        class="field mt-2 w-full"
        bind:value={form.recipient_ids}
        placeholder="Comma-separated IDs"
      /></label
    >
    <label
      ><span class="label">Schedule at</span><input
        class="field mt-2 w-full"
        type="datetime-local"
        bind:value={form.scheduled_at}
      /></label
    >
    <label class="lg:col-span-2"
      ><span class="label">Body</span><textarea
        class="field mt-2 min-h-36 w-full py-3"
        bind:value={form.body}
        required
      ></textarea></label
    >
    <div class="flex flex-wrap justify-end gap-2 lg:col-span-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => submitNotification(false, true)}
        id="btn-send-broadcast"><Send size={16} />Broadcast</Button
      >
      <Button
        type="button"
        variant="secondary"
        on:click={() => submitNotification(true, false)}
        id="btn-schedule-notification">Schedule</Button
      >
      <Button type="submit">Send now</Button>
    </div>
  </form>
</Modal>

<Modal
  open={detailOpen}
  title={selected?.subject ?? 'Notification'}
  description={selected ? dateTime(selected.created_at) : ''}
  wide
  on:close={() => (detailOpen = false)}
>
  {#if selected}
    <div class="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
      <div>
        <p class="label">Message</p>
        <div class="mt-2 rounded-lg border border-line bg-slate-50 p-4 text-sm">
          {selected.body ?? 'No body loaded.'}
        </div>
      </div>
      <div class="space-y-3">
        <div class="grid grid-cols-3 gap-2 text-center text-sm">
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="font-semibold">{number(delivery?.delivered)}</p>
            <p class="text-xs text-muted">Delivered</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="font-semibold">{number(delivery?.failed)}</p>
            <p class="text-xs text-muted">Failed</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-3">
            <p class="font-semibold">{number(delivery?.pending)}</p>
            <p class="text-xs text-muted">Pending</p>
          </div>
        </div>
        <div class="max-h-72 overflow-auto rounded-lg border border-line">
          {#each delivery?.deliveries ?? [] as item}
            <div class="border-b border-line p-3 text-sm">
              <div class="flex justify-between gap-3">
                <span>{item.recipient_email ?? item.recipient_id}</span
                ><StatusBadge value={String(item.status)} compact />
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</Modal>
