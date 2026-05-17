<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    Activity,
    AlertTriangle,
    BellRing,
    Clock,
    Cpu,
    Maximize2,
    Pause,
    Play,
    RefreshCw,
    Volume2,
    VolumeX
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type {
    DeviceHealthSnapshot,
    DeviceStatus,
    LiveWasteEntry,
    MealSession,
    MonitoringAlert
  } from '$lib/api/types';
  import { ReconnectingSocket } from '$lib/api/ws';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Gauge from '$lib/components/charts/Gauge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { auth } from '$lib/stores/auth';
  import { notify } from '$lib/stores/toast';
  import { dateTime, grams, number, titleCase } from '$lib/utils/format';

  type ListPayload<T> = T[] | { items?: T[]; data?: T[] };
  type DeviceHealthResponse = Partial<DeviceStatus> & {
    current?: Partial<DeviceStatus>;
    metrics?: Partial<DeviceStatus>;
    data?: DeviceHealthSnapshot[];
    history?: DeviceHealthSnapshot[];
  };

  const sessionTimeline = [
    { meal: 'breakfast', label: 'Breakfast', window: '7:00-9:30' },
    { meal: 'lunch', label: 'Lunch', window: '12:00-14:30' },
    { meal: 'dinner', label: 'Dinner', window: '19:00-21:30' }
  ];

  let loading = true;
  let error = '';
  let paused = false;
  let pendingEntries: LiveWasteEntry[] = [];
  let soundEnabled = false;
  let mealFilter = '';
  let wsStatus = 'closed';
  let session: MealSession | null = null;
  let entries: LiveWasteEntry[] = [];
  let alerts: MonitoringAlert[] = [];
  let devices: DeviceStatus[] = [];
  let selectedDevice: DeviceStatus | null = null;
  let deviceHealth: DeviceHealthResponse | null = null;
  let selectedEntry: LiveWasteEntry | null = null;
  let socket: ReconnectingSocket | null = null;

  $: visibleEntries = mealFilter
    ? entries.filter((entry) => entry.meal_type === mealFilter)
    : entries;
  $: entryCount =
    session?.entry_count_today ?? session?.entry_count ?? entries.length;
  $: totalWaste =
    session?.total_waste_today_grams ??
    entries.reduce((sum, entry) => sum + Number(entry.weight_grams ?? 0), 0);
  $: activeDevices = devices.filter(
    (device) => device.status?.toLowerCase() === 'online'
  ).length;
  $: unacknowledgedAlerts = alerts.filter(
    (alert) => !alert.acknowledged
  ).length;
  $: wasteRate = currentWasteRate(entries);
  $: meals = Array.from(
    new Set([
      'breakfast',
      'lunch',
      'dinner',
      ...entries.map((entry) => entry.meal_type).filter(Boolean)
    ])
  );
  $: selectedDeviceMetrics = {
    ...(selectedDevice ?? {}),
    ...(deviceHealth?.current ?? {}),
    ...(deviceHealth?.metrics ?? {}),
    ...(deviceHealth ?? {})
  };
  $: healthPoints = deviceHealth?.history ?? deviceHealth?.data ?? [];
  $: canAcknowledge = $auth.user?.role !== 'analytics_viewer';

  function listOf<T>(payload: ListPayload<T>): T[] {
    if (Array.isArray(payload)) return payload;
    return payload.items ?? payload.data ?? [];
  }

  function normalizeEntry(entry: Partial<LiveWasteEntry>): LiveWasteEntry {
    return {
      id: String(entry.id ?? crypto.randomUUID()),
      student_id: entry.student_id ?? null,
      student_name: entry.student_name ?? null,
      student_roll_number: entry.student_roll_number ?? null,
      student_device_id: entry.student_device_id ?? null,
      device_id: String(entry.device_id ?? ''),
      weight_grams: Number(entry.weight_grams ?? 0),
      meal_type: String(entry.meal_type ?? 'unknown'),
      food_items: entry.food_items ?? [],
      severity: String(
        entry.severity ?? severityFromWeight(entry.weight_grams)
      ),
      plate_image_path: entry.plate_image_path ?? null,
      timestamp: String(entry.timestamp ?? new Date().toISOString())
    };
  }

  function normalizeDevice(device: Partial<DeviceStatus>): DeviceStatus {
    return {
      id: String(device.id ?? device.name ?? crypto.randomUUID()),
      name: device.name ?? device.edge_node_name ?? 'Unnamed device',
      edge_node_name: device.edge_node_name ?? device.name ?? 'Unnamed device',
      mess_name: device.mess_name ?? null,
      status: String(device.status ?? 'offline'),
      cpu_percent: device.cpu_percent ?? null,
      ram_percent: device.ram_percent ?? null,
      temperature: device.temperature ?? null,
      last_heartbeat: device.last_heartbeat ?? null,
      ip_address: device.ip_address ?? null,
      firmware_version: device.firmware_version ?? null,
      uptime_seconds: device.uptime_seconds ?? null
    };
  }

  function severityFromWeight(value: number | null | undefined) {
    const weight = Number(value ?? 0);
    if (weight > 200) return 'high';
    if (weight >= 100) return 'medium';
    return 'low';
  }

  function severityBorder(entry: LiveWasteEntry) {
    const severity = String(
      entry.severity ?? severityFromWeight(entry.weight_grams)
    );
    if (severity === 'high') return 'border-l-down';
    if (severity === 'medium') return 'border-l-primary';
    return 'border-l-up';
  }

  function dotForStatus(status: string | null | undefined) {
    const normalized = String(status ?? '').toLowerCase();
    if (normalized === 'online') return 'dot-up';
    if (normalized === 'warning') return 'dot-warn';
    if (normalized === 'offline' || normalized === 'decommissioned')
      return 'dot-down';
    return 'dot-muted';
  }

  function priorityClass(alert: MonitoringAlert) {
    const priority = String(
      alert.priority ?? alert.alert_type ?? alert.type ?? ''
    ).toLowerCase();
    if (priority === 'critical') return 'badge-down';
    if (priority === 'high') return 'badge-primary';
    if (priority === 'medium') return 'badge-info';
    return 'badge-muted';
  }

  function studentLabel(entry: LiveWasteEntry) {
    return (
      entry.student_name ??
      entry.student_roll_number ??
      entry.student_device_id ??
      entry.student_id ??
      'Unknown student'
    );
  }

  function foodLabels(entry: LiveWasteEntry) {
    return (entry.food_items ?? [])
      .map((item) => (typeof item === 'string' ? item : item.name))
      .filter(Boolean);
  }

  function plateImagePath(path: string | null | undefined) {
    if (!path) return '';
    if (path.startsWith('http') || path.startsWith('/')) return path;
    return `/static/uploads/${path}`;
  }

  function relativeTime(value: string | null | undefined) {
    if (!value) return 'Just now';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Just now';
    const seconds = Math.max(
      0,
      Math.round((Date.now() - date.getTime()) / 1000)
    );
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return dateTime(value);
  }

  function currentWasteRate(source: LiveWasteEntry[]) {
    const recent = source.slice(0, 5);
    if (recent.length === 0) return 0;
    if (recent.length === 1) return Number(recent[0].weight_grams ?? 0);

    const newest = new Date(recent[0].timestamp).getTime();
    const oldest = new Date(recent[recent.length - 1].timestamp).getTime();
    const spanMinutes = Math.max(1, Math.abs(newest - oldest) / 60000);
    const gramsTotal = recent.reduce(
      (sum, entry) => sum + Number(entry.weight_grams ?? 0),
      0
    );
    return gramsTotal / spanMinutes;
  }

  function mealEntryCount(meal: string) {
    return entries.filter((entry) => entry.meal_type === meal).length;
  }

  function barStyle(value: number | null | undefined) {
    const clamped = Math.max(0, Math.min(100, Number(value ?? 0)));
    return `width:${clamped}%`;
  }

  function addEntry(entry: LiveWasteEntry) {
    entries = [entry, ...entries].slice(0, 100);
    if (session) {
      session = {
        ...session,
        entry_count: (session.entry_count ?? 0) + 1,
        entry_count_today:
          (session.entry_count_today ?? session.entry_count ?? 0) + 1,
        total_waste_today_grams:
          Number(session.total_waste_today_grams ?? 0) +
          Number(entry.weight_grams ?? 0)
      };
    }
  }

  function handleMessage(message: Record<string, unknown>) {
    const type = String(message.type ?? '');
    const payload = (message.data ?? message) as Record<string, unknown>;

    if (type === 'waste_entry') {
      const entry = normalizeEntry(payload as Partial<LiveWasteEntry>);
      if (paused) pendingEntries = [entry, ...pendingEntries].slice(0, 100);
      else addEntry(entry);
      return;
    }

    if (type === 'alert') {
      const alert = payload as MonitoringAlert;
      alerts = [alert, ...alerts].slice(0, 50);
      if (soundEnabled) playBeep();
      return;
    }

    if (type === 'device_status') {
      const device = normalizeDevice(payload as Partial<DeviceStatus>);
      const exists = devices.some((item) => item.id === device.id);
      devices = exists
        ? devices.map((item) =>
            item.id === device.id ? { ...item, ...device } : item
          )
        : [device, ...devices];
      return;
    }

    if (type === 'session_change') {
      session = payload as unknown as MealSession;
    }
  }

  async function loadMonitoring() {
    loading = true;
    error = '';
    try {
      const [sessionData, entryData, deviceData] = await Promise.all([
        api.get<MealSession>('/monitoring/current-session'),
        api.get<ListPayload<LiveWasteEntry>>('/monitoring/recent-entries', {
          limit: 50
        }),
        api.get<ListPayload<DeviceStatus>>('/monitoring/device-statuses')
      ]);
      session = sessionData;
      entries = listOf(entryData).map(normalizeEntry).slice(0, 100);
      devices = listOf(deviceData).map(normalizeDevice);
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load monitoring data';
    } finally {
      loading = false;
    }
  }

  function togglePause() {
    paused = !paused;
    if (!paused && pendingEntries.length > 0) {
      pendingEntries.forEach(addEntry);
      pendingEntries = [];
    }
  }

  async function acknowledge(alert: MonitoringAlert) {
    const id = alert.notification_id ?? alert.id;
    if (!id) {
      notify('This alert has no notification id to acknowledge.', 'error');
      return;
    }
    try {
      await api.post(`/monitoring/alerts/${id}/acknowledge`);
      alerts = alerts.map((item) =>
        item === alert ? { ...item, acknowledged: true } : item
      );
      notify('Alert acknowledged.', 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not acknowledge alert.',
        'error'
      );
    }
  }

  async function openDevice(device: DeviceStatus) {
    selectedDevice = device;
    deviceHealth = null;
    try {
      deviceHealth = await api.get<DeviceHealthResponse>(
        `/devices/${device.id}/health`
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load device health.',
        'error'
      );
    }
  }

  async function openEntry(entry: LiveWasteEntry) {
    selectedEntry = entry;
    try {
      selectedEntry = normalizeEntry(
        await api.get<Partial<LiveWasteEntry>>(`/waste/entries/${entry.id}`)
      );
    } catch {
      selectedEntry = entry;
    }
  }

  function playBeep() {
    const AudioCtor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!AudioCtor) return;
    const ctx = new AudioCtor();
    const oscillator = ctx.createOscillator();
    oscillator.frequency.value = 660;
    oscillator.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.12);
  }

  async function fullscreen() {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not toggle fullscreen.',
        'error'
      );
    }
  }

  onMount(() => {
    loadMonitoring();
    socket = new ReconnectingSocket(
      '/monitoring',
      handleMessage,
      (status) => (wsStatus = status)
    );
    socket.connect();
  });

  onDestroy(() => socket?.close());
</script>

<svelte:head>
  <title>Live Monitoring | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Live monitoring"
  title="Waste entries, devices, and alerts"
  description="Real-time feed, current meal session health, and connected edge devices."
>
  <svelte:fragment slot="actions">
    <StatusBadge value={wsStatus} />
    <select
      class="select-field"
      bind:value={mealFilter}
      id="select-feed-meal-filter"
    >
      <option value="">All meals</option>
      {#each meals as meal}
        <option value={meal}>{titleCase(meal)}</option>
      {/each}
    </select>
    <Button
      variant="secondary"
      on:click={togglePause}
      id="btn-toggle-feed-pause"
    >
      {#if paused}<Play size={16} />Resume{:else}<Pause size={16} />Pause{/if}
    </Button>
    <Button
      variant="secondary"
      on:click={() => (soundEnabled = !soundEnabled)}
      id="btn-toggle-sound"
      title="Toggle alert sound"
    >
      {#if soundEnabled}<Volume2 size={16} />{:else}<VolumeX size={16} />{/if}
    </Button>
    <Button
      variant="secondary"
      on:click={fullscreen}
      id="btn-fullscreen-monitoring"
      title="Toggle fullscreen"
    >
      <Maximize2 size={16} />
    </Button>
    <Button variant="secondary" on:click={loadMonitoring}>
      <RefreshCw size={16} />
      Refresh
    </Button>
  </svelte:fragment>
</PageHeader>

{#if error}
  <Card title="Monitoring unavailable" description={error}>
    <Button on:click={loadMonitoring}>Retry</Button>
  </Card>
{:else}
  <div
    class="mb-4 flex flex-wrap items-center gap-3 rounded-md bg-elevated/50 px-4 py-2 text-sm text-muted"
  >
    <span class={dotForStatus(wsStatus)}></span>
    <span class="font-medium text-body">{titleCase(wsStatus)}</span>
    {#if wsStatus === 'reconnecting' || wsStatus === 'connecting'}
      <span class="skeleton h-2 w-24"></span>
    {:else if paused}
      <span>{pendingEntries.length} queued while paused</span>
    {:else}
      <span>Live stream active</span>
    {/if}
  </div>

  <div class="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
    <StatCard
      title="Waste Today"
      value={grams(totalWaste)}
      helper="Across monitored meals"
    >
      <svelte:fragment slot="icon"><Activity size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Active Devices"
      value={`${number(activeDevices)} / ${number(devices.length)}`}
      helper="Online edge nodes"
      tone={activeDevices > 0 ? 'good' : 'bad'}
    >
      <svelte:fragment slot="icon"><Cpu size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Alerts"
      value={number(alerts.length)}
      helper={`${number(unacknowledgedAlerts)} unacknowledged`}
      tone={unacknowledgedAlerts > 0 ? 'hot' : 'neutral'}
    >
      <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Current Meal"
      value={titleCase(session?.meal_type ?? 'none')}
      helper={session?.is_active ? 'Open now' : 'Outside meal time'}
      tone={session?.is_active ? 'good' : 'neutral'}
    >
      <svelte:fragment slot="icon"><Clock size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Entries Today"
      value={number(entryCount)}
      helper={session?.session_name ?? 'Current session'}
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
  </div>

  <div class="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.85fr_1fr]">
    <Card
      title="Real-Time Feed"
      description={paused
        ? 'Paused for inspection'
        : 'Newest waste entries first'}
    >
      {#if loading && entries.length === 0}
        <div class="skeleton h-80"></div>
      {:else if visibleEntries.length === 0}
        <EmptyState
          title="No entries in feed"
          message="Matching waste entries will stream here."
        />
      {:else}
        <div class="max-h-[620px] space-y-3 overflow-auto pr-1">
          {#each visibleEntries as entry (entry.id)}
            <button
              class={`w-full rounded-lg border border-l-4 border-border bg-card p-3 text-left transition hover:border-primary ${severityBorder(entry)}`}
              on:click={() => openEntry(entry)}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-body">
                    {studentLabel(entry)}
                  </p>
                  <p class="mt-1 text-xs text-muted">
                    {entry.student_roll_number ??
                      entry.student_device_id ??
                      'No roll number'}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-mono text-sm font-semibold text-primary">
                    {grams(entry.weight_grams)}
                  </p>
                  <p class="mt-1 text-xs text-muted">
                    {relativeTime(entry.timestamp)}
                  </p>
                </div>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <span class="badge-primary">{titleCase(entry.meal_type)}</span>
                {#each foodLabels(entry).slice(0, 3) as item}
                  <span class="badge-muted">{item}</span>
                {/each}
                {#if foodLabels(entry).length === 0}
                  <span class="badge-muted">No food labels</span>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </Card>

    <div class="space-y-5">
      <Card title="Active Session" description="Current meal window">
        {#if session?.is_active}
          <p class="text-2xl font-bold text-primary">
            {titleCase(session.meal_type)}
          </p>
          <p class="mt-2 text-sm text-muted">
            {session.start_time} - {session.end_time}
          </p>
          <div class="mt-5 grid grid-cols-2 gap-3">
            <div class="rounded-md bg-elevated p-3">
              <p class="label">Entries</p>
              <p class="mt-1 font-mono text-3xl font-bold text-body">
                {number(entryCount)}
              </p>
            </div>
            <div class="rounded-md bg-elevated p-3">
              <p class="label">Average</p>
              <p class="mt-1 font-mono text-3xl font-bold text-body">
                {grams(totalWaste / Math.max(entryCount, 1))}
              </p>
            </div>
          </div>
        {:else}
          <EmptyState
            title="No active session"
            message="The next meal window will appear here when it opens."
          />
        {/if}
      </Card>

      <Card title="Live Waste Gauge" description="Current feed rate">
        <Gauge
          value={wasteRate}
          max={500}
          unit="g/min"
          label="Recent waste velocity"
        />
      </Card>
    </div>

    <Card title="Device Status" description="Online and offline edge nodes">
      {#if devices.length === 0}
        <EmptyState
          title="No devices"
          message="Registered device health will appear here."
        />
      {:else}
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          {#each devices as device (device.id)}
            <button
              class="rounded-lg border border-border bg-card p-3 text-left transition hover:border-primary"
              on:click={() => openDevice(device)}
              id={`btn-device-detail-${device.id}`}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-body">
                    {device.edge_node_name ?? device.name}
                  </p>
                  <p class="truncate text-xs text-muted">
                    {device.mess_name ?? 'Unassigned mess'}
                  </p>
                </div>
                <span
                  class="flex shrink-0 items-center gap-1 text-xs font-semibold text-muted"
                >
                  <span class={dotForStatus(device.status)}></span>
                  {titleCase(device.status)}
                </span>
              </div>
              <div class="mt-3 space-y-2">
                <div>
                  <div class="mb-1 flex justify-between text-xs text-muted">
                    <span>CPU</span><span>{number(device.cpu_percent)}%</span>
                  </div>
                  <div class="h-1.5 rounded-full bg-elevated">
                    <div
                      class="h-full rounded-full bg-primary"
                      style={barStyle(device.cpu_percent)}
                    ></div>
                  </div>
                </div>
                <div>
                  <div class="mb-1 flex justify-between text-xs text-muted">
                    <span>RAM</span><span>{number(device.ram_percent)}%</span>
                  </div>
                  <div class="h-1.5 rounded-full bg-elevated">
                    <div
                      class="h-full rounded-full bg-primary"
                      style={barStyle(device.ram_percent)}
                    ></div>
                  </div>
                </div>
              </div>
              <p class="mt-3 text-xs text-muted">
                Last seen {relativeTime(device.last_heartbeat)}
              </p>
            </button>
          {/each}
        </div>
      {/if}
    </Card>
  </div>

  <div class="mt-5 grid gap-5 xl:grid-cols-[1fr_1.35fr]">
    <Card
      title="Alert Feed"
      description={`${number(unacknowledgedAlerts)} waiting for acknowledgement`}
    >
      {#if alerts.length === 0}
        <EmptyState
          title="No live alerts"
          message="Critical events will appear here immediately."
        />
      {:else}
        <div class="max-h-[420px] space-y-3 overflow-auto pr-1">
          {#each alerts as alert, index}
            <div
              class={`rounded-lg border border-border bg-card p-3 ${alert.acknowledged ? 'opacity-50' : ''}`}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <span class={priorityClass(alert)}>
                    {titleCase(
                      alert.priority ?? alert.alert_type ?? alert.type ?? 'low'
                    )}
                  </span>
                  <p class="mt-2 truncate text-sm font-semibold text-body">
                    {alert.subject ??
                      titleCase(alert.alert_type ?? alert.type ?? 'alert')}
                  </p>
                  <p class="mt-1 text-xs text-muted">
                    {alert.message ?? alert.reason ?? 'No message supplied'}
                  </p>
                  {#if alert.rule_name}
                    <p class="mt-1 text-xs text-muted">{alert.rule_name}</p>
                  {/if}
                </div>
                <p class="shrink-0 text-xs text-muted">
                  {relativeTime(alert.timestamp)}
                </p>
              </div>
              <div class="mt-3 flex items-center justify-between gap-3">
                <StatusBadge
                  value={alert.acknowledged ? 'acknowledged' : 'active'}
                  compact
                />
                {#if canAcknowledge && !alert.acknowledged}
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => acknowledge(alert)}
                    id={`btn-ack-alert-${alert.id ?? index}`}
                  >
                    Acknowledge
                  </Button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </Card>

    <Card title="Session Timeline" description="Today's meal windows">
      <div class="grid gap-4 md:grid-cols-3">
        {#each sessionTimeline as item}
          {@const isCurrent =
            session?.meal_type === item.meal && session?.is_active}
          <div class="rounded-lg border border-border bg-card p-4">
            <div class="mb-3 flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-body">{item.label}</p>
                <p class="text-xs text-muted">{item.window}</p>
              </div>
              <span class={isCurrent ? 'dot-up' : 'dot-muted'}></span>
            </div>
            <div class="h-2 rounded-full bg-elevated">
              <div
                class={`h-full rounded-full ${
                  isCurrent
                    ? 'bg-primary'
                    : mealEntryCount(item.meal) > 0
                      ? 'bg-primary/30'
                      : 'bg-elevated'
                }`}
                style={barStyle(
                  isCurrent ? 100 : mealEntryCount(item.meal) > 0 ? 45 : 0
                )}
              ></div>
            </div>
            <p class="mt-3 text-xs text-muted">
              {number(mealEntryCount(item.meal))} entries
            </p>
          </div>
        {/each}
      </div>
    </Card>
  </div>
{/if}

<Modal
  open={!!selectedDevice}
  title={selectedDevice?.edge_node_name ?? selectedDevice?.name ?? 'Device'}
  description={selectedDevice?.mess_name ?? ''}
  wide
  on:close={() => (selectedDevice = null)}
>
  {#if selectedDevice}
    <div class="grid gap-5 lg:grid-cols-[0.75fr_1.25fr]">
      <div class="space-y-3 text-sm">
        <div class="rounded-md bg-elevated p-3">
          <span class="label">Status</span>
          <div class="mt-2"><StatusBadge value={selectedDevice.status} /></div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-md bg-elevated p-3">
            <span class="label">CPU</span>
            <p class="mt-1 font-mono text-xl text-body">
              {number(selectedDeviceMetrics.cpu_percent)}%
            </p>
          </div>
          <div class="rounded-md bg-elevated p-3">
            <span class="label">RAM</span>
            <p class="mt-1 font-mono text-xl text-body">
              {number(selectedDeviceMetrics.ram_percent)}%
            </p>
          </div>
          <div class="rounded-md bg-elevated p-3">
            <span class="label">Temp</span>
            <p class="mt-1 font-mono text-xl text-body">
              {number(selectedDeviceMetrics.temperature)}C
            </p>
          </div>
          <div class="rounded-md bg-elevated p-3">
            <span class="label">Firmware</span>
            <p class="mt-1 truncate text-body">
              {selectedDeviceMetrics.firmware_version ?? 'Unknown'}
            </p>
          </div>
        </div>
        <p>
          <span class="label">Last heartbeat</span><br />{dateTime(
            selectedDeviceMetrics.last_heartbeat
          )}
        </p>
        <p>
          <span class="label">IP</span><br
          />{selectedDeviceMetrics.ip_address ?? 'Unknown'}
        </p>
      </div>
      <ChartCard
        title="24h Health"
        chartType="line"
        height={340}
        labels={healthPoints.map((point) => dateTime(point.recorded_at))}
        datasets={[
          {
            label: 'CPU %',
            data: healthPoints.map((point) => point.cpu_percent)
          },
          {
            label: 'RAM %',
            data: healthPoints.map((point) => point.ram_percent)
          },
          {
            label: 'Temp C',
            data: healthPoints.map((point) => point.temperature ?? 0)
          }
        ]}
      />
    </div>
  {/if}
</Modal>

<Modal
  open={!!selectedEntry}
  title="Waste entry detail"
  description={selectedEntry ? dateTime(selectedEntry.timestamp) : ''}
  on:close={() => (selectedEntry = null)}
>
  {#if selectedEntry}
    <div class="space-y-4 text-sm">
      <div class="grid grid-cols-2 gap-3">
        <div class="rounded-md bg-elevated p-3">
          <span class="label">Student</span>
          <p class="mt-1 font-semibold text-body">
            {studentLabel(selectedEntry)}
          </p>
        </div>
        <div class="rounded-md bg-elevated p-3">
          <span class="label">Weight</span>
          <p class="mt-1 font-semibold text-body">
            {grams(selectedEntry.weight_grams)}
          </p>
        </div>
      </div>
      <p>
        <span class="label">Meal</span><br />{titleCase(
          selectedEntry.meal_type
        )}
      </p>
      <p>
        <span class="label">Food items</span><br />{foodLabels(
          selectedEntry
        ).join(', ') || 'None'}
      </p>
      {#if selectedEntry.plate_image_path}
        <img
          class="max-h-72 w-full rounded-lg object-cover"
          src={plateImagePath(selectedEntry.plate_image_path)}
          alt="Plate waste"
        />
      {/if}
    </div>
  {/if}
</Modal>
