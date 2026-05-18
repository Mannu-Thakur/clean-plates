<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Bell,
    CheckCheck,
    Eye,
    Mail,
    RefreshCw,
    Settings,
    SlidersHorizontal,
    Trash2
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type {
    NotificationDelivery,
    NotificationItem,
    NotificationPreference,
    NotificationStats,
    Paginated
  } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import Pagination from '$lib/components/ui/Pagination.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs, { type TabItem } from '$lib/components/ui/Tabs.svelte';
  import Toggle from '$lib/components/ui/Toggle.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type NotificationTab = 'all' | 'inbox' | 'pending' | 'failed' | 'scheduled';
  type NotificationDetail = NotificationItem & {
    body?: string;
    recipient_ids?: string[];
    retry_count?: number;
  };
  type PreferencePayload =
    | NotificationPreference[]
    | { items?: NotificationPreference[] };

  const PREFERENCES_KEY = 'cleanplates.notification.preferences';
  const tabs: TabItem[] = [
    { id: 'all', label: 'All', icon: Bell },
    { id: 'inbox', label: 'Unread Inbox', icon: Mail },
    { id: 'pending', label: 'Pending' },
    { id: 'failed', label: 'Failed' },
    { id: 'scheduled', label: 'Scheduled' }
  ];
  const notificationTypes = ['warning', 'penalty', 'alert', 'system', 'custom'];
  const channels = ['dashboard', 'email', 'both'];
  const statuses = ['sent', 'partial', 'pending', 'failed'];

  let activeTab: NotificationTab = 'inbox';
  let loading = true;
  let detailLoading = false;
  let preferencesLoading = false;
  let preferencesDirty = false;
  let error = '';
  let page = 1;
  let size = 20;
  let filters = {
    type: '',
    channel: '',
    status: '',
    is_read: ''
  };
  let notifications: Paginated<NotificationItem> = emptyPage();
  let stats: NotificationStats = {
    unread: 0,
    sent_today: 0,
    failed: 0,
    pending: 0
  };
  let selected: NotificationDetail | null = null;
  let delivery: NotificationDelivery | null = null;
  let preferences: NotificationPreference[] = defaultPreferences();

  $: visibleItems = notifications.items.filter(matchesLocalFilters);
  $: unreadVisible = notifications.items.filter((item) => !item.is_read).length;

  function emptyPage(): Paginated<NotificationItem> {
    return { items: [], total: 0, page: 1, size, pages: 1 };
  }

  function defaultPreferences(): NotificationPreference[] {
    return notificationTypes.map((type) => ({
      type,
      dashboard: true,
      email: type !== 'system'
    }));
  }

  function normalizePreferences(
    data: PreferencePayload
  ): NotificationPreference[] {
    const rows = Array.isArray(data) ? data : data.items;
    if (!rows?.length) return defaultPreferences();
    const byType = new Map(rows.map((row) => [row.type, row]));
    return defaultPreferences().map((fallback) => ({
      ...fallback,
      ...byType.get(fallback.type)
    }));
  }

  function matchesLocalFilters(item: NotificationItem) {
    if (filters.type && item.type !== filters.type) return false;
    if (filters.channel && item.channel !== filters.channel) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (filters.is_read !== '' && String(item.is_read) !== filters.is_read)
      return false;
    return true;
  }

  function listQuery() {
    return {
      tab: activeTab === 'all' ? undefined : activeTab,
      type: filters.type,
      channel: filters.channel,
      status: filters.status,
      is_read: filters.is_read,
      page,
      size
    };
  }

  function resetFilters() {
    filters = { type: '', channel: '', status: '', is_read: '' };
    page = 1;
    loadNotifications();
  }

  function setTab(id: string) {
    activeTab = id as NotificationTab;
    page = 1;
    loadNotifications();
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadNotifications();
  }

  function emitNotificationRefresh() {
    window.dispatchEvent(new CustomEvent('cleanplates:notifications-refresh'));
  }

  async function loadNotifications(showLoading = true) {
    if (showLoading) loading = true;
    error = '';
    try {
      const [listData, statData] = await Promise.all([
        api.get<Paginated<NotificationItem>>('/notifications', listQuery()),
        api.get<NotificationStats>('/notifications/stats')
      ]);
      notifications = listData;
      stats = statData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load notifications';
    } finally {
      loading = false;
    }
  }

  async function loadPreferences() {
    preferencesLoading = true;
    try {
      const data = await api.get<PreferencePayload>(
        '/notifications/preferences'
      );
      preferences = normalizePreferences(data);
    } catch {
      const stored = window.localStorage.getItem(PREFERENCES_KEY);
      if (stored) {
        try {
          preferences = normalizePreferences(JSON.parse(stored));
        } catch {
          preferences = defaultPreferences();
        }
      } else {
        preferences = defaultPreferences();
      }
    } finally {
      preferencesLoading = false;
      preferencesDirty = false;
    }
  }

  async function openDetail(item: NotificationItem) {
    selected = item;
    delivery = null;
    detailLoading = true;
    try {
      const [detail, deliveryData] = await Promise.all([
        api.get<NotificationDetail>(`/notifications/${item.id}`),
        api
          .get<NotificationDelivery>(`/notifications/${item.id}/delivery`)
          .catch(() => null)
      ]);
      selected = detail;
      delivery = deliveryData;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load notification.',
        'error'
      );
    } finally {
      detailLoading = false;
    }
  }

  async function markRead(item: NotificationItem) {
    if (item.is_read) return;
    try {
      await api.patch(`/notifications/${item.id}/read`);
      notify('Notification marked read.', 'success');
      if (selected?.id === item.id) selected = { ...selected, is_read: true };
      await loadNotifications(false);
      emitNotificationRefresh();
    } catch (err) {
      notify(
        err instanceof Error
          ? err.message
          : 'Could not mark notification read.',
        'error'
      );
    }
  }

  async function markAllRead() {
    try {
      await api.post('/notifications/mark-all-read');
      notify('All notifications marked read.', 'success');
      await loadNotifications(false);
      emitNotificationRefresh();
    } catch (err) {
      notify(
        err instanceof Error
          ? err.message
          : 'Could not mark notifications read.',
        'error'
      );
    }
  }

  async function deleteNotification(item: NotificationItem) {
    if (!window.confirm(`Delete "${item.subject}"?`)) return;
    try {
      await api.delete(`/notifications/${item.id}`);
      notify('Notification deleted.', 'success');
      if (selected?.id === item.id) selected = null;
      await loadNotifications(false);
      emitNotificationRefresh();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not delete notification.',
        'error'
      );
    }
  }

  async function retry(item: NotificationItem) {
    try {
      await api.post(`/notifications/${item.id}/retry`);
      notify('Retry queued.', 'success');
      await loadNotifications(false);
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not retry.', 'error');
    }
  }

  function updatePreference(
    type: string,
    key: 'dashboard' | 'email',
    value: boolean
  ) {
    preferences = preferences.map((row) =>
      row.type === type ? { ...row, [key]: value } : row
    );
    preferencesDirty = true;
  }

  async function savePreferences() {
    try {
      await api.put('/notifications/preferences', preferences);
      notify('Notification preferences saved.', 'success');
    } catch {
      window.localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
      notify('Notification preferences saved locally.', 'warning');
    } finally {
      preferencesDirty = false;
    }
  }

  onMount(() => {
    loadNotifications();
    loadPreferences();
  });
</script>

<svelte:head>
  <title>Notifications | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Notification center"
  title="Inbox, delivery status, and channel preferences"
  description="Review dashboard alerts, mark read notifications, and tune channel preferences by notification type."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={() => loadNotifications()}
      id="btn-refresh-notifications"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={markAllRead}
      id="btn-mark-all-read"
      disabled={stats.unread === 0}
    >
      <CheckCheck size={16} />
      Mark all read
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard title="Unread" value={number(stats.unread)} helper="Inbox count">
    <svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Sent Today"
    value={number(stats.sent_today)}
    helper="Delivered or partial"
    tone="good"
  >
    <svelte:fragment slot="icon"><Mail size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Failed"
    value={number(stats.failed)}
    helper="Retry required"
    tone="bad"
  >
    <svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Pending"
    value={number(stats.pending)}
    helper="Queued or scheduled"
    tone="warn"
  >
    <svelte:fragment slot="icon"><Bell size={19} /></svelte:fragment>
  </StatCard>
</div>

<div class="mt-5">
  <Tabs {tabs} active={activeTab} onChange={setTab} />
</div>

<div class="mt-5 grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
  <div class="space-y-5">
    <Card title="Inbox filters">
      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <label>
          <span class="label">Type</span>
          <select
            class="select-field mt-2"
            bind:value={filters.type}
            on:change={() => {
              page = 1;
              loadNotifications();
            }}
            id="select-notification-type"
          >
            <option value="">All types</option>
            {#each notificationTypes as type}
              <option value={type}>{titleCase(type)}</option>
            {/each}
          </select>
        </label>
        <label>
          <span class="label">Channel</span>
          <select
            class="select-field mt-2"
            bind:value={filters.channel}
            on:change={() => {
              page = 1;
              loadNotifications();
            }}
            id="select-notification-channel"
          >
            <option value="">All channels</option>
            {#each channels as channel}
              <option value={channel}>{titleCase(channel)}</option>
            {/each}
          </select>
        </label>
        <label>
          <span class="label">Status</span>
          <select
            class="select-field mt-2"
            bind:value={filters.status}
            on:change={() => {
              page = 1;
              loadNotifications();
            }}
            id="select-notification-status"
          >
            <option value="">All statuses</option>
            {#each statuses as status}
              <option value={status}>{titleCase(status)}</option>
            {/each}
          </select>
        </label>
        <label>
          <span class="label">Read state</span>
          <select
            class="select-field mt-2"
            bind:value={filters.is_read}
            on:change={() => {
              page = 1;
              loadNotifications();
            }}
            id="select-notification-read"
          >
            <option value="">All</option>
            <option value="false">Unread</option>
            <option value="true">Read</option>
          </select>
        </label>
        <div class="flex items-end">
          <Button variant="secondary" on:click={resetFilters}>Reset</Button>
        </div>
      </div>
    </Card>

    <Card
      title="Notification inbox"
      description={`${number(unreadVisible)} unread on this page`}
    >
      {#if error}
        <div
          class="rounded-md border border-down/30 bg-down/10 p-3 text-sm text-down"
        >
          {error}
        </div>
      {:else if loading}
        <div class="space-y-3">
          {#each Array.from({ length: 5 }) as _}
            <div class="skeleton h-24"></div>
          {/each}
        </div>
      {:else if visibleItems.length === 0}
        <EmptyState
          title="No notifications"
          message="Adjust filters or wait for alerts, report events, and warning messages."
        />
      {:else}
        <div class="space-y-3">
          {#each visibleItems as item}
            <article
              class={`rounded-lg border p-4 transition-colors ${
                item.is_read
                  ? 'border-border bg-card'
                  : 'border-primary/40 bg-primary/5'
              }`}
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <button
                  class="min-w-0 flex-1 text-left"
                  type="button"
                  on:click={() => openDetail(item)}
                >
                  <div class="flex flex-wrap items-center gap-2">
                    {#if !item.is_read}
                      <span class="dot-warn" aria-label="Unread"></span>
                    {/if}
                    <p class="truncate font-semibold text-body">
                      {item.subject}
                    </p>
                  </div>
                  <p class="mt-2 text-sm text-muted">
                    {titleCase(item.type)} / {titleCase(item.channel)} / {dateTime(
                      item.created_at
                    )}
                  </p>
                </button>
                <div class="flex flex-wrap items-center justify-end gap-2">
                  <StatusBadge value={item.status} compact />
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => openDetail(item)}
                    id={`btn-view-notification-${item.id}`}
                  >
                    <Eye size={14} />
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => markRead(item)}
                    disabled={item.is_read}
                    id={`btn-mark-read-${item.id}`}
                  >
                    Read
                  </Button>
                  {#if item.status === 'failed' || item.status === 'partial'}
                    <Button
                      size="sm"
                      variant="secondary"
                      on:click={() => retry(item)}
                      id={`btn-retry-notification-${item.id}`}
                    >
                      Retry
                    </Button>
                  {/if}
                  <Button
                    size="sm"
                    variant="danger"
                    on:click={() => deleteNotification(item)}
                    id={`btn-delete-notification-${item.id}`}
                  >
                    <Trash2 size={14} />
                    Delete
                  </Button>
                </div>
              </div>
            </article>
          {/each}
        </div>

        <Pagination
          {page}
          total={notifications.total}
          pageSize={size}
          onChange={goToPage}
        />
      {/if}
    </Card>
  </div>

  <Card title="Channel preferences">
    <svelte:fragment slot="actions">
      <Settings size={16} class="text-muted" />
    </svelte:fragment>
    {#if preferencesLoading}
      <div class="space-y-3">
        {#each Array.from({ length: 5 }) as _}
          <div class="skeleton h-14"></div>
        {/each}
      </div>
    {:else}
      <div class="space-y-3">
        {#each preferences as pref}
          <div class="rounded-lg border border-border bg-elevated/40 p-3">
            <div class="mb-3 flex items-center gap-2">
              <SlidersHorizontal size={15} class="text-primary" />
              <p class="font-semibold text-body">{titleCase(pref.type)}</p>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <Toggle
                value={pref.dashboard}
                label="Dashboard"
                onChange={(value) =>
                  updatePreference(pref.type, 'dashboard', value)}
              />
              <Toggle
                value={pref.email}
                label="Email"
                onChange={(value) =>
                  updatePreference(pref.type, 'email', value)}
              />
            </div>
          </div>
        {/each}
      </div>
      <div class="mt-4 flex justify-end">
        <Button
          on:click={savePreferences}
          disabled={!preferencesDirty}
          id="btn-save-notification-preferences"
        >
          Save preferences
        </Button>
      </div>
    {/if}
  </Card>
</div>

<Modal
  open={!!selected}
  title={selected?.subject ?? 'Notification'}
  description={selected ? dateTime(selected.created_at) : ''}
  wide
  on:close={() => (selected = null)}
>
  {#if selected}
    {#if detailLoading}
      <div class="skeleton h-72"></div>
    {:else}
      <div class="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
        <div class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <StatusBadge value={selected.status} compact />
            <StatusBadge value={selected.is_read ? 'read' : 'unread'} compact />
            <span class="badge-info">{titleCase(selected.channel)}</span>
            <span class="badge-muted">{titleCase(selected.type)}</span>
          </div>
          <div class="rounded-lg border border-border bg-elevated/40 p-4">
            <p class="label">Message</p>
            <p class="mt-3 whitespace-pre-wrap text-sm leading-6 text-body">
              {selected.body ?? 'No body available.'}
            </p>
          </div>
          {#if selected.recipient_ids?.length}
            <div class="rounded-lg border border-border bg-elevated/40 p-4">
              <p class="label">Recipients</p>
              <p class="mt-2 text-sm text-body">
                {selected.recipient_ids.join(', ')}
              </p>
            </div>
          {/if}
          <div class="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              on:click={() => markRead(selected as NotificationItem)}
              disabled={selected.is_read}
            >
              <CheckCheck size={16} />
              Mark read
            </Button>
            {#if selected.status === 'failed' || selected.status === 'partial'}
              <Button
                variant="secondary"
                on:click={() => retry(selected as NotificationItem)}
              >
                Retry delivery
              </Button>
            {/if}
            <Button
              variant="danger"
              on:click={() => deleteNotification(selected as NotificationItem)}
            >
              <Trash2 size={16} />
              Delete
            </Button>
          </div>
        </div>

        <div class="space-y-4">
          <div class="grid grid-cols-3 gap-2 text-center text-sm">
            <div class="rounded-lg bg-elevated p-3">
              <p class="font-semibold text-body">
                {number(delivery?.delivered)}
              </p>
              <p class="mt-1 text-xs text-muted">Delivered</p>
            </div>
            <div class="rounded-lg bg-elevated p-3">
              <p class="font-semibold text-body">{number(delivery?.failed)}</p>
              <p class="mt-1 text-xs text-muted">Failed</p>
            </div>
            <div class="rounded-lg bg-elevated p-3">
              <p class="font-semibold text-body">{number(delivery?.pending)}</p>
              <p class="mt-1 text-xs text-muted">Pending</p>
            </div>
          </div>

          <div class="max-h-80 overflow-auto rounded-lg border border-border">
            {#if !delivery?.deliveries?.length}
              <div class="p-4">
                <EmptyState title="No delivery rows" />
              </div>
            {:else}
              {#each delivery.deliveries as item}
                <div class="border-b border-border p-3 text-sm last:border-0">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate font-semibold text-body">
                        {item.recipient_email ?? item.recipient_id}
                      </p>
                      <p class="mt-1 text-xs text-muted">
                        {titleCase(item.channel)} / {dateTime(
                          item.delivered_at
                        )}
                      </p>
                      {#if item.error}
                        <p class="mt-1 text-xs text-down">{item.error}</p>
                      {/if}
                    </div>
                    <StatusBadge value={item.status} compact />
                  </div>
                </div>
              {/each}
            {/if}
          </div>
        </div>
      </div>
    {/if}
  {/if}
</Modal>
