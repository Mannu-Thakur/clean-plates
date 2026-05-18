<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Activity,
    Copy,
    Cpu,
    Grid2X2,
    HardDrive,
    List,
    Plus,
    RefreshCw,
    RotateCcw,
    Save,
    Thermometer,
    Wifi
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Device, DeviceHealthSnapshot, Paginated } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type DeviceHistoryResponse = {
    data?: DeviceHealthSnapshot[];
  };
  type RegisteredDevice = Device & { api_key?: string };

  let viewMode: 'grid' | 'list' = 'grid';
  let loading = true;
  let error = '';
  let statusFilter = '';
  let devices: Paginated<Device> = {
    items: [],
    total: 0,
    page: 1,
    size: 50,
    pages: 1
  };
  let selected: Device | null = null;
  let detail: Device | null = null;
  let health: DeviceHealthSnapshot | null = null;
  let history: {
    data: DeviceHealthSnapshot[];
  } = { data: [] };
  let addOpen = false;
  let registeredApiKey = '';
  let form = defaultForm();

  $: online = devices.items.filter(
    (device) => device.status === 'online'
  ).length;
  $: offline = devices.items.filter(
    (device) => device.status === 'offline'
  ).length;
  $: warning = devices.items.filter(
    (device) => device.status === 'warning'
  ).length;
  $: storagePercent = health?.storage_percent ?? health?.disk_percent ?? null;
  $: recentHistory = history.data.slice(0, 6);

  function metricLabel(value: number | null | undefined, suffix = '%') {
    if (value === null || value === undefined) return 'n/a';
    return `${number(Math.round(value))}${suffix}`;
  }

  function metricTone(value: number | null | undefined) {
    if (value === null || value === undefined) return 'text-muted';
    if (value >= 85) return 'text-down';
    if (value >= 70) return 'text-primary';
    return 'text-up';
  }

  function defaultForm() {
    return {
      device_serial: '',
      edge_node_name: '',
      institution_name: 'CleanPlates Institution',
      institution_code: 'CP',
      campus_name: 'Main Campus',
      mess_name: '',
      mess_id: '',
      hostel_name: '',
      hostel_block: '',
      floor_number: 0,
      wing_section: '',
      capacity: 0,
      meal_capacity_per_day: 0,
      managed_by: '',
      admin_contact: ''
    };
  }

  function openRegister() {
    form = defaultForm();
    registeredApiKey = '';
    addOpen = true;
  }

  async function loadDevices() {
    loading = true;
    error = '';
    try {
      devices = await api.get<Paginated<Device>>('/devices', {
        status: statusFilter,
        size: 100
      });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load devices';
    } finally {
      loading = false;
    }
  }

  async function openDetail(device: Device) {
    selected = device;
    detail = null;
    health = null;
    history = { data: [] };
    try {
      const [deviceDetail, healthData, historyData] = await Promise.all([
        api.get<Device>(`/devices/${device.id}`),
        api
          .get<DeviceHealthSnapshot>(`/devices/${device.id}/health`)
          .catch(() => null),
        api
          .get<DeviceHistoryResponse>(`/devices/${device.id}/health/history`)
          .catch(() => ({ data: [] }))
      ]);
      detail = deviceDetail;
      selected = deviceDetail;
      health = healthData;
      history = { data: historyData.data ?? [] };
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load device details.',
        'error'
      );
      selected = null;
    }
  }

  async function registerDevice() {
    try {
      const created = await api.post<RegisteredDevice>('/devices', form);
      notify('Device registered.', 'success');
      registeredApiKey = created.api_key ?? '';
      form = defaultForm();
      await loadDevices();
      if (!registeredApiKey) addOpen = false;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not register device.',
        'error'
      );
    }
  }

  async function copyRegisteredApiKey() {
    if (!registeredApiKey) return;
    try {
      await navigator.clipboard.writeText(registeredApiKey);
      notify('API key copied.', 'success');
    } catch {
      notify('Could not copy API key.', 'error');
    }
  }

  async function restart(device: Device) {
    await api.post(`/devices/${device.id}/restart`);
    notify('Restart command queued.', 'success');
  }

  async function sync(device: Device) {
    const result = await api.post<{ pending_count: number }>(
      `/devices/${device.id}/sync`
    );
    notify(
      `Sync queued with ${number(result.pending_count)} pending entries.`,
      'success'
    );
  }

  async function decommission(device: Device) {
    if (!window.confirm(`Decommission ${device.edge_node_name}?`)) return;
    await api.post(`/devices/${device.id}/decommission`);
    notify('Device decommissioned.', 'success');
    selected = null;
    await loadDevices();
  }

  async function syncSelected() {
    if (detail) await sync(detail);
  }

  async function restartSelected() {
    if (detail) await restart(detail);
  }

  async function decommissionSelected() {
    if (detail) await decommission(detail);
  }

  async function updateSelected() {
    if (!detail) return;
    const updated = await api.patch<Device>(`/devices/${detail.id}`, {
      edge_node_name: detail.edge_node_name,
      mess_name: detail.mess_name,
      hostel_name: detail.hostel_name
    });
    detail = updated;
    selected = updated;
    notify('Device updated.', 'success');
    await loadDevices();
  }

  onMount(loadDevices);
</script>

<svelte:head><title>Devices | CleanPlates</title></svelte:head>

<PageHeader
  label="Device health"
  title="Raspberry Pi fleet identity, status, and telemetry"
  description="Monitor online/offline state, inspect health metrics, review heartbeat history, and update device metadata."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={() => (viewMode = viewMode === 'grid' ? 'list' : 'grid')}
    >
      {#if viewMode === 'grid'}
        <List size={16} />
      {:else}
        <Grid2X2 size={16} />
      {/if}
      {titleCase(viewMode === 'grid' ? 'list' : 'grid')}
    </Button>
    <Button variant="secondary" on:click={loadDevices} id="btn-refresh-health">
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button on:click={openRegister} id="btn-add-device">
      <Plus size={16} />
      Add device
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Total"
    value={number(devices.total)}
    helper="Registered devices"
    ><svelte:fragment slot="icon"><Cpu size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Online"
    value={number(online)}
    helper="Heartbeat healthy"
    tone="good"
    ><svelte:fragment slot="icon"><Wifi size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Offline"
    value={number(offline)}
    helper="No recent heartbeat"
    tone="bad"
    ><svelte:fragment slot="icon"><Wifi size={19} /></svelte:fragment></StatCard
  >
  <StatCard
    title="Warning"
    value={number(warning)}
    helper="Needs attention"
    tone="warn"
    ><svelte:fragment slot="icon"><Cpu size={19} /></svelte:fragment></StatCard
  >
</div>

<Card class="mt-5" title="Device filters">
  <div class="flex flex-wrap items-end gap-3">
    <label
      ><span class="label">Status</span><select
        class="select-field mt-2"
        bind:value={statusFilter}
        id="select-device-status"
        ><option value="">All</option><option>online</option><option
          >offline</option
        ><option>warning</option><option>decommissioned</option></select
      ></label
    ><Button on:click={loadDevices}>Apply</Button>
  </div>
</Card>

<Card class="mt-5" title={viewMode === 'grid' ? 'Device grid' : 'Device list'}>
  {#if error}<div
      class="rounded-md border border-down/30 bg-down/10 p-3 text-down"
    >
      {error}
    </div>
  {:else if loading}<div
      class="h-96 animate-pulse rounded-lg bg-elevated"
    ></div>
  {:else if devices.items.length === 0}<EmptyState title="No devices" />
  {:else if viewMode === 'grid'}
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {#each devices.items as device}
        <button
          class="rounded-lg border border-border bg-card p-4 text-left transition hover:border-primary"
          on:click={() => openDetail(device)}
          id={`card-device-${device.id}`}
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold">{device.edge_node_name}</p>
              <p class="mt-1 text-sm text-muted">{device.mess_name}</p>
            </div>
            <StatusBadge value={device.status} />
          </div>
          <div class="mt-4 grid grid-cols-2 gap-2 text-sm text-muted">
            <span>IP {device.ip_address ?? 'unknown'}</span><span
              >FW {device.firmware_version ?? 'n/a'}</span
            ><span>Heartbeat {dateTime(device.last_heartbeat)}</span><span
              >Sync {dateTime(device.last_sync)}</span
            >
          </div>
        </button>
      {/each}
    </div>
  {:else}
    <div class="overflow-auto">
      <table>
        <thead class="bg-elevated"
          ><tr
            ><th class="th">Name</th><th class="th">Mess</th><th class="th"
              >Status</th
            ><th class="th">Last heartbeat</th><th class="th">Actions</th></tr
          ></thead
        ><tbody
          >{#each devices.items as device}<tr
              ><td class="td">{device.edge_node_name}</td><td class="td"
                >{device.mess_name}</td
              ><td class="td"><StatusBadge value={device.status} compact /></td
              ><td class="td">{dateTime(device.last_heartbeat)}</td><td
                class="td"
                ><Button
                  size="sm"
                  variant="secondary"
                  on:click={() => openDetail(device)}>Open</Button
                ></td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
  {/if}
</Card>

<Modal
  open={!!selected}
  title={detail?.edge_node_name ?? selected?.edge_node_name ?? 'Device'}
  description={detail?.mess_name ?? selected?.mess_name ?? ''}
  wide
  on:close={() => (selected = null)}
>
  {#if !detail}
    <div class="skeleton h-96"></div>
  {:else}
    <div class="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
      <div class="space-y-4">
        <label
          ><span class="label">Name</span><input
            class="input-field mt-2 w-full"
            bind:value={detail.edge_node_name}
          /></label
        >
        <label
          ><span class="label">Mess</span><input
            class="input-field mt-2 w-full"
            bind:value={detail.mess_name}
          /></label
        >
        <label
          ><span class="label">Hostel</span><input
            class="input-field mt-2 w-full"
            bind:value={detail.hostel_name}
          /></label
        >

        <div class="grid grid-cols-2 gap-3 text-sm">
          <div class="rounded-lg border border-border bg-elevated/60 p-3">
            <div class="flex items-center gap-2 text-muted">
              <Cpu size={15} />
              <span class="label">CPU</span>
            </div>
            <p
              class={`mt-2 text-xl font-semibold ${metricTone(
                health?.cpu_percent
              )}`}
            >
              {metricLabel(health?.cpu_percent)}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated/60 p-3">
            <div class="flex items-center gap-2 text-muted">
              <Activity size={15} />
              <span class="label">RAM</span>
            </div>
            <p
              class={`mt-2 text-xl font-semibold ${metricTone(
                health?.ram_percent
              )}`}
            >
              {metricLabel(health?.ram_percent)}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated/60 p-3">
            <div class="flex items-center gap-2 text-muted">
              <Thermometer size={15} />
              <span class="label">Temp</span>
            </div>
            <p
              class={`mt-2 text-xl font-semibold ${metricTone(
                health?.temperature
              )}`}
            >
              {metricLabel(health?.temperature, ' C')}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated/60 p-3">
            <div class="flex items-center gap-2 text-muted">
              <HardDrive size={15} />
              <span class="label">Storage</span>
            </div>
            <p
              class={`mt-2 text-xl font-semibold ${metricTone(storagePercent)}`}
            >
              {metricLabel(storagePercent)}
            </p>
          </div>
        </div>

        <div class="rounded-lg border border-border bg-elevated/40 p-4 text-sm">
          <p class="label">Device identity</p>
          <div class="mt-3 grid gap-3">
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">Status</span>
              <StatusBadge value={detail.status} compact />
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">Connectivity</span>
              <StatusBadge
                value={health?.connectivity === undefined
                  ? 'unknown'
                  : health.connectivity
                    ? 'connected'
                    : 'offline'}
                compact
              />
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">IP address</span>
              <span class="font-mono text-body"
                >{detail.ip_address ?? 'n/a'}</span
              >
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">Firmware</span>
              <span class="font-mono text-body">
                {detail.firmware_version ?? 'n/a'}
              </span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">Last heartbeat</span>
              <span class="text-body">{dateTime(detail.last_heartbeat)}</span>
            </div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-muted">Last sync</span>
              <span class="text-body">{dateTime(detail.last_sync)}</span>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            on:click={updateSelected}
            id={`btn-edit-device-${detail.id}`}><Save size={16} />Save</Button
          ><Button
            variant="secondary"
            on:click={syncSelected}
            id={`btn-sync-${detail.id}`}>Sync</Button
          ><Button
            variant="secondary"
            on:click={restartSelected}
            id={`btn-restart-${detail.id}`}
            ><RotateCcw size={16} />Restart</Button
          ><Button
            variant="danger"
            on:click={decommissionSelected}
            id={`btn-decommission-${detail.id}`}>Decommission</Button
          >
        </div>
      </div>
      <div class="space-y-5">
        <ChartCard
          title="Health History"
          description="CPU, RAM, temperature, and storage samples from recent heartbeats."
          chartType="line"
          labels={history.data.map((point) => dateTime(point.recorded_at))}
          datasets={[
            {
              label: 'CPU %',
              data: history.data.map((point) => point.cpu_percent)
            },
            {
              label: 'RAM %',
              data: history.data.map((point) => point.ram_percent)
            },
            {
              label: 'Temp C',
              data: history.data.map((point) => point.temperature ?? 0)
            },
            {
              label: 'Storage %',
              data: history.data.map(
                (point) => point.storage_percent ?? point.disk_percent ?? 0
              )
            }
          ]}
        />

        <Card title="Device history timeline">
          {#if recentHistory.length === 0}
            <EmptyState title="No health history" />
          {:else}
            <div class="space-y-3">
              {#each recentHistory as point}
                <div
                  class="rounded-lg border border-border bg-elevated/40 p-3 text-sm"
                >
                  <div class="flex items-start gap-3">
                    <span
                      class={point.connectivity === false
                        ? 'dot-down mt-1'
                        : 'dot-up mt-1'}
                    ></span>
                    <div class="min-w-0 flex-1">
                      <div
                        class="flex flex-wrap items-center justify-between gap-2"
                      >
                        <p class="font-semibold text-body">
                          {dateTime(point.recorded_at)}
                        </p>
                        <StatusBadge
                          value={point.connectivity === false
                            ? 'offline'
                            : 'healthy'}
                          compact
                        />
                      </div>
                      <p class="mt-2 text-muted">
                        CPU {metricLabel(point.cpu_percent)} / RAM {metricLabel(
                          point.ram_percent
                        )} / Temp {metricLabel(point.temperature, ' C')}
                      </p>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </Card>
      </div>
    </div>
  {/if}
</Modal>

<Modal
  open={addOpen}
  title="Register device"
  on:close={() => (addOpen = false)}
  wide
>
  {#if registeredApiKey}
    <div class="mb-4 rounded-lg border border-primary/30 bg-primary/10 p-4">
      <p class="font-semibold text-body">Device registered</p>
      <p class="mt-1 text-sm text-muted">
        API key is shown once. Copy it before closing this dialog.
      </p>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <input
          class="input-field min-w-0 flex-1 font-mono"
          readonly
          value={registeredApiKey}
        />
        <Button
          type="button"
          variant="secondary"
          on:click={copyRegisteredApiKey}
        >
          <Copy size={16} />
          Copy
        </Button>
      </div>
    </div>
  {/if}
  <form
    class="grid gap-3 md:grid-cols-2"
    on:submit|preventDefault={registerDevice}
  >
    <label
      ><span class="label">Device serial</span><input
        class="input-field mt-2 w-full"
        bind:value={form.device_serial}
        required
      /></label
    >
    <label
      ><span class="label">Edge node name</span><input
        class="input-field mt-2 w-full"
        bind:value={form.edge_node_name}
        required
      /></label
    >
    <label
      ><span class="label">Institution</span><input
        class="input-field mt-2 w-full"
        bind:value={form.institution_name}
        required
      /></label
    >
    <label
      ><span class="label">Institution code</span><input
        class="input-field mt-2 w-full"
        bind:value={form.institution_code}
        required
      /></label
    >
    <label
      ><span class="label">Campus</span><input
        class="input-field mt-2 w-full"
        bind:value={form.campus_name}
        required
      /></label
    >
    <label
      ><span class="label">Mess name</span><input
        class="input-field mt-2 w-full"
        bind:value={form.mess_name}
        required
      /></label
    >
    <label
      ><span class="label">Mess ID</span><input
        class="input-field mt-2 w-full"
        bind:value={form.mess_id}
        required
      /></label
    >
    <label
      ><span class="label">Hostel</span><input
        class="input-field mt-2 w-full"
        bind:value={form.hostel_name}
      /></label
    >
    <label
      ><span class="label">Hostel block</span><input
        class="input-field mt-2 w-full"
        bind:value={form.hostel_block}
      /></label
    >
    <label
      ><span class="label">Floor</span><input
        class="input-field mt-2 w-full"
        type="number"
        bind:value={form.floor_number}
      /></label
    >
    <label
      ><span class="label">Wing</span><input
        class="input-field mt-2 w-full"
        bind:value={form.wing_section}
      /></label
    >
    <label
      ><span class="label">Capacity</span><input
        class="input-field mt-2 w-full"
        type="number"
        bind:value={form.capacity}
      /></label
    >
    <label
      ><span class="label">Meal capacity/day</span><input
        class="input-field mt-2 w-full"
        type="number"
        bind:value={form.meal_capacity_per_day}
      /></label
    >
    <label
      ><span class="label">Managed by</span><input
        class="input-field mt-2 w-full"
        bind:value={form.managed_by}
      /></label
    >
    <label
      ><span class="label">Admin contact</span><input
        class="input-field mt-2 w-full"
        bind:value={form.admin_contact}
      /></label
    >
    <div class="flex justify-end gap-2 md:col-span-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (addOpen = false)}>Cancel</Button
      ><Button type="submit">Register</Button>
    </div>
  </form>
</Modal>
