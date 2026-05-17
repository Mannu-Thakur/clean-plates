<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Cpu,
    Grid2X2,
    List,
    Plus,
    RefreshCw,
    RotateCcw,
    Save,
    Wifi
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Device, Paginated } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ChartCard from '$lib/components/charts/ChartCard.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

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
  let health: {
    cpu_percent?: number;
    ram_percent?: number;
    temperature?: number | null;
  } | null = null;
  let history: {
    data: Array<{
      recorded_at: string;
      cpu_percent: number;
      ram_percent: number;
      temperature?: number | null;
    }>;
  } = { data: [] };
  let addOpen = false;
  let form = {
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

  $: online = devices.items.filter(
    (device) => device.status === 'online'
  ).length;
  $: offline = devices.items.filter(
    (device) => device.status === 'offline'
  ).length;
  $: warning = devices.items.filter(
    (device) => device.status === 'warning'
  ).length;

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
    try {
      const [deviceDetail, healthData, historyData] = await Promise.all([
        api.get<Device>(`/devices/${device.id}`),
        api
          .get<typeof health>(`/devices/${device.id}/health`)
          .catch(() => null),
        api
          .get<
            typeof history
          >(`/devices/${device.id}/health/history`, { period: '24h' })
          .catch(() => ({ data: [] }))
      ]);
      detail = deviceDetail;
      health = healthData;
      history = historyData;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load device detail.',
        'error'
      );
    }
  }

  async function registerDevice() {
    try {
      await api.post('/devices', form);
      notify('Device registered.', 'success');
      addOpen = false;
      await loadDevices();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not register device.',
        'error'
      );
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
    await api.patch(`/devices/${detail.id}`, {
      edge_node_name: detail.edge_node_name,
      mess_name: detail.mess_name,
      hostel_name: detail.hostel_name
    });
    notify('Device updated.', 'success');
    await loadDevices();
  }

  onMount(loadDevices);
</script>

<svelte:head><title>Devices | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Devices</p>
    <h2 class="mt-1 text-2xl font-semibold text-body">
      Raspberry Pi identity and health
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button
      variant="secondary"
      on:click={() => (viewMode = viewMode === 'grid' ? 'list' : 'grid')}
      >{#if viewMode === 'grid'}<List size={16} />{:else}<Grid2X2
          size={16}
        />{/if}</Button
    ><Button variant="secondary" on:click={loadDevices} id="btn-refresh-health"
      ><RefreshCw size={16} />Refresh</Button
    ><Button on:click={() => (addOpen = true)} id="btn-add-device"
      ><Plus size={16} />Add device</Button
    >
  </div>
</div>

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
        ><option>warning</option><option>inactive</option></select
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
  {#if detail}
    <div class="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
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
          <div class="rounded-lg bg-elevated p-3">
            <span class="label">CPU</span>
            <p class="mt-1 font-semibold">{number(health?.cpu_percent)}%</p>
          </div>
          <div class="rounded-lg bg-elevated p-3">
            <span class="label">RAM</span>
            <p class="mt-1 font-semibold">{number(health?.ram_percent)}%</p>
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
      <ChartCard
        title="Health History"
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
          }
        ]}
      />
    </div>
  {/if}
</Modal>

<Modal
  open={addOpen}
  title="Register device"
  on:close={() => (addOpen = false)}
  wide
>
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
