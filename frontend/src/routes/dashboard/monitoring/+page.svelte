<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    BellRing,
    Maximize2,
    Pause,
    Play,
    RefreshCw,
    Volume2,
    VolumeX
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Device, WasteEntry } from '$lib/api/types';
  import { ReconnectingSocket } from '$lib/api/ws';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Gauge from '$lib/components/charts/Gauge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { dateTime, grams, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type SessionSummary = {
    session_name: string;
    meal_type: string;
    start_time: string;
    end_time: string;
    entry_count_today: number;
    total_waste_today_grams: number;
    is_active: boolean;
  };

  type AlertMessage = {
    id?: string;
    notification_id?: string;
    subject?: string;
    message?: string;
    reason?: string;
    type?: string;
    alert_type?: string;
    timestamp?: string;
    acknowledged?: boolean;
  };

  let loading = true;
  let error = '';
  let paused = false;
  let soundEnabled = false;
  let mealFilter = '';
  let wsStatus = 'closed';
  let session: SessionSummary | null = null;
  let entries: WasteEntry[] = [];
  let alerts: AlertMessage[] = [];
  let devices: Device[] = [];
  let selectedDevice: Device | null = null;
  let healthHistory: {
    data: Array<{
      recorded_at: string;
      cpu_percent: number;
      ram_percent: number;
      temperature?: number | null;
    }>;
  } | null = null;
  let selectedEntry: WasteEntry | null = null;
  let socket: ReconnectingSocket | null = null;

  $: visibleEntries = mealFilter
    ? entries.filter((entry) => entry.meal_type === mealFilter)
    : entries;
  $: activeSessions = session?.is_active ? 1 : 0;
  $: wasteRate = session
    ? session.total_waste_today_grams / Math.max(session.entry_count_today, 1)
    : 0;
  $: meals = Array.from(
    new Set(entries.map((entry) => entry.meal_type).filter(Boolean))
  );

  async function loadMonitoring() {
    loading = true;
    error = '';
    try {
      const [sessionData, entryData, deviceData] = await Promise.all([
        api.get<SessionSummary>('/monitoring/current-session'),
        api.get<WasteEntry[]>('/monitoring/recent-entries', { limit: 50 }),
        api.get<Device[]>('/monitoring/device-statuses')
      ]);
      session = sessionData;
      entries = entryData;
      devices = deviceData;
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load monitoring data';
    } finally {
      loading = false;
    }
  }

  function handleMessage(message: Record<string, unknown>) {
    const type = String(message.type ?? '');
    if (type === 'waste_entry') {
      const entry = (message.data ?? message) as WasteEntry;
      entries = [entry, ...entries].slice(0, 100);
      session = session
        ? {
            ...session,
            entry_count_today: session.entry_count_today + 1,
            total_waste_today_grams:
              session.total_waste_today_grams + Number(entry.weight_grams ?? 0)
          }
        : session;
    }
    if (type === 'alert') {
      const alert = (message.data ?? message) as AlertMessage;
      alerts = [alert, ...alerts].slice(0, 50);
      if (soundEnabled) playBeep();
    }
    if (type === 'device_status') {
      const device = (message.data ?? message) as Device;
      devices = devices.map((item) =>
        item.id === device.id ? { ...item, ...device } : item
      );
    }
  }

  function togglePause() {
    paused = !paused;
    if (paused) socket?.pause();
    else socket?.resume();
  }

  function applyMealFilter() {
    socket?.filter(mealFilter ? { meal_type: mealFilter } : {});
  }

  async function acknowledge(alert: AlertMessage) {
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

  async function openDevice(device: Device) {
    selectedDevice = device;
    healthHistory = null;
    try {
      healthHistory = await api.get(`/devices/${device.id}/health/history`, {
        period: '24h'
      });
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load device health.',
        'error'
      );
    }
  }

  async function openEntry(entry: WasteEntry) {
    selectedEntry = entry;
    try {
      selectedEntry = await api.get<WasteEntry>(`/waste/entries/${entry.id}`);
    } catch {
      selectedEntry = entry;
    }
  }

  function playBeep() {
    const ctx = new AudioContext();
    const oscillator = ctx.createOscillator();
    oscillator.frequency.value = 660;
    oscillator.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.12);
  }

  async function fullscreen() {
    if (!document.fullscreenElement)
      await document.documentElement.requestFullscreen();
    else await document.exitFullscreen();
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

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Live monitoring</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      Waste entries, devices, and alerts
    </h2>
  </div>
  <div class="flex flex-wrap items-center gap-2">
    <StatusBadge value={wsStatus} />
    <select
      class="field"
      bind:value={mealFilter}
      on:change={applyMealFilter}
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
    >
      {#if soundEnabled}<Volume2 size={16} />{:else}<VolumeX size={16} />{/if}
    </Button>
    <Button
      variant="secondary"
      on:click={fullscreen}
      id="btn-fullscreen-monitoring"
    >
      <Maximize2 size={16} />
    </Button>
    <Button on:click={loadMonitoring}>
      <RefreshCw size={16} />
      Refresh
    </Button>
  </div>
</div>

{#if error}
  <Card title="Monitoring unavailable" description={error}>
    <Button on:click={loadMonitoring}>Retry</Button>
  </Card>
{:else}
  <div class="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
    <StatCard
      title="Entries Today"
      value={number(session?.entry_count_today)}
      helper={session?.session_name ?? 'No session'}
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Active Sessions"
      value={activeSessions}
      helper={session?.is_active
        ? `${session.start_time}-${session.end_time}`
        : 'Closed'}
      tone={session?.is_active ? 'good' : 'neutral'}
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Current Meal"
      value={titleCase(session?.meal_type ?? 'none')}
      helper={session?.is_active ? 'Open now' : 'Outside meal time'}
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Total Waste"
      value={grams(session?.total_waste_today_grams)}
      helper="Today"
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
    <StatCard
      title="Alerts"
      value={alerts.length}
      helper={`${alerts.filter((item) => !item.acknowledged).length} unacknowledged`}
      tone="hot"
    >
      <svelte:fragment slot="icon"><BellRing size={19} /></svelte:fragment>
    </StatCard>
  </div>

  <div class="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.95fr_0.85fr]">
    <Card
      title="Real-Time Feed"
      description={paused
        ? 'Paused for inspection'
        : 'Newest waste entries first'}
    >
      {#if loading && entries.length === 0}
        <div class="h-80 animate-pulse rounded-lg bg-slate-100"></div>
      {:else if visibleEntries.length === 0}
        <EmptyState
          title="No entries in feed"
          message="Matching waste entries will stream here."
        />
      {:else}
        <div class="max-h-[620px] space-y-3 overflow-auto pr-1">
          {#each visibleEntries as entry (entry.id)}
            <button
              class="w-full rounded-lg border border-line bg-white p-3 text-left transition hover:border-fresh"
              on:click={() => openEntry(entry)}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-ink">
                    {entry.student_name ?? entry.student_device_id}
                  </p>
                  <p class="mt-1 text-xs text-muted">
                    {titleCase(entry.meal_type)} · {dateTime(entry.timestamp)}
                  </p>
                </div>
                <StatusBadge value={entry.severity} compact />
              </div>
              <div class="mt-3 flex items-center justify-between gap-3 text-sm">
                <span class="font-semibold text-ink"
                  >{grams(entry.weight_grams)}</span
                >
                <span class="truncate text-muted"
                  >{entry.food_items?.map((item) => item.name).join(', ') ||
                    'No food labels'}</span
                >
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </Card>

    <div class="space-y-5">
      <Card
        title="Live Waste Gauge"
        description="Average grams per entry in the current session"
      >
        <Gauge
          value={wasteRate}
          max={200}
          unit="g/entry"
          label="Current waste rate"
        />
      </Card>
      <Card title="Alert Feed" description="Rule engine and device events">
        {#if alerts.length === 0}
          <EmptyState
            title="No live alerts"
            message="Critical events will appear here immediately."
          />
        {:else}
          <div class="space-y-3">
            {#each alerts as alert, index}
              <div class="rounded-lg border border-line bg-slate-50 p-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-ink">
                      {alert.subject ??
                        titleCase(alert.alert_type ?? alert.type ?? 'alert')}
                    </p>
                    <p class="mt-1 text-xs text-muted">
                      {alert.message ?? alert.reason ?? 'No message supplied'}
                    </p>
                  </div>
                  <StatusBadge
                    value={alert.acknowledged ? 'resolved' : 'active'}
                    compact
                  />
                </div>
                <Button
                  class="mt-3"
                  size="sm"
                  variant="secondary"
                  on:click={() => acknowledge(alert)}
                  id={`btn-ack-alert-${alert.id ?? index}`}>Acknowledge</Button
                >
              </div>
            {/each}
          </div>
        {/if}
      </Card>
    </div>

    <Card title="Device Status" description="Raspberry Pi health indicators">
      {#if devices.length === 0}
        <EmptyState
          title="No devices"
          message="Registered device health will appear here."
        />
      {:else}
        <div class="grid gap-3">
          {#each devices as device (device.id)}
            <button
              class="rounded-lg border border-line bg-white p-3 text-left transition hover:border-fresh"
              on:click={() => openDevice(device)}
              id={`btn-device-detail-${device.id}`}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-ink">
                    {device.edge_node_name}
                  </p>
                  <p class="truncate text-xs text-muted">{device.mess_name}</p>
                </div>
                <StatusBadge value={device.status} compact />
              </div>
              <div class="mt-3 grid grid-cols-3 gap-2 text-xs text-muted">
                <span>CPU {number(device.cpu_percent)}%</span>
                <span>RAM {number(device.ram_percent)}%</span>
                <span>{number(device.temperature)}C</span>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </Card>
  </div>
{/if}

<Modal
  open={!!selectedDevice}
  title={selectedDevice?.edge_node_name ?? 'Device'}
  description={selectedDevice?.mess_name ?? ''}
  wide
  on:close={() => (selectedDevice = null)}
>
  {#if selectedDevice}
    <div class="grid gap-5 lg:grid-cols-[0.7fr_1.3fr]">
      <div class="space-y-3 text-sm">
        <p>
          <span class="label">Status</span><br /><StatusBadge
            value={selectedDevice.status}
          />
        </p>
        <p>
          <span class="label">Last heartbeat</span><br />{dateTime(
            selectedDevice.last_heartbeat
          )}
        </p>
        <p>
          <span class="label">Last sync</span><br />{dateTime(
            selectedDevice.last_sync
          )}
        </p>
        <p>
          <span class="label">IP</span><br />{selectedDevice.ip_address ??
            'Unknown'}
        </p>
      </div>
      <ChartCard
        title="24h Health"
        chartType="line"
        labels={(healthHistory?.data ?? []).map((point) =>
          dateTime(point.recorded_at)
        )}
        datasets={[
          {
            label: 'CPU %',
            data: (healthHistory?.data ?? []).map((point) => point.cpu_percent)
          },
          {
            label: 'RAM %',
            data: (healthHistory?.data ?? []).map((point) => point.ram_percent)
          },
          {
            label: 'Temp C',
            data: (healthHistory?.data ?? []).map(
              (point) => point.temperature ?? 0
            )
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
        <div class="rounded-md bg-slate-50 p-3">
          <span class="label">Student</span>
          <p class="mt-1 font-semibold">
            {selectedEntry.student_name ?? selectedEntry.student_device_id}
          </p>
        </div>
        <div class="rounded-md bg-slate-50 p-3">
          <span class="label">Weight</span>
          <p class="mt-1 font-semibold">{grams(selectedEntry.weight_grams)}</p>
        </div>
      </div>
      <p>
        <span class="label">Food items</span><br />{selectedEntry.food_items
          ?.map((item) => item.name)
          .join(', ') || 'None'}
      </p>
      {#if selectedEntry.plate_image_path}
        <img
          class="max-h-72 w-full rounded-lg object-cover"
          src={selectedEntry.plate_image_path}
          alt="Plate waste"
        />
      {/if}
    </div>
  {/if}
</Modal>
