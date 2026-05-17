<script lang="ts">
  import { onMount } from 'svelte';
  import { Download, FileUp, RefreshCw, UserPlus } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, Student } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { grams, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  let loading = true;
  let error = '';
  let response: Paginated<Student> = {
    items: [],
    total: 0,
    page: 1,
    size: 25,
    pages: 1
  };
  let selected = new Set<string>();
  let page = 1;
  let size = 25;
  let sort = 'created_at';
  let order: 'asc' | 'desc' = 'desc';
  let filters = { status: '', hostel: '', branch: '', year: '' };
  let mappingStudent: Student | null = null;
  let mapping = {
    name: '',
    roll_number: '',
    branch: '',
    year: 1,
    hostel: '',
    room_number: '',
    email: ''
  };
  let importFile: File | null = null;
  let importOpen = false;

  $: totalMapped = response.items.filter((student) => student.mapping).length;
  $: warningCount = response.items.filter(
    (student) => student.warning_count > 0
  ).length;
  $: penaltyCount = response.items.filter(
    (student) => student.penalty_count > 0
  ).length;

  function query() {
    return {
      page,
      size,
      sort,
      order,
      status: filters.status,
      hostel: filters.hostel,
      branch: filters.branch,
      year: filters.year ? Number(filters.year) : undefined
    };
  }

  async function loadStudents() {
    loading = true;
    error = '';
    try {
      response = await api.get<Paginated<Student>>('/students', query());
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load students';
    } finally {
      loading = false;
    }
  }

  function openMapping(student: Student) {
    mappingStudent = student;
    mapping = {
      name: student.mapping?.name ?? '',
      roll_number: student.mapping?.roll_number ?? '',
      branch: student.mapping?.branch ?? '',
      year: student.mapping?.year ?? 1,
      hostel: student.mapping?.hostel ?? '',
      room_number: student.mapping?.room_number ?? '',
      email: student.mapping?.email ?? ''
    };
  }

  async function saveMapping() {
    if (!mappingStudent) return;
    try {
      const body = {
        ...mapping,
        hostel: mapping.hostel || null,
        room_number: mapping.room_number || null,
        email: mapping.email || null
      };
      if (mappingStudent.mapping)
        await api.patch(`/students/${mappingStudent.id}/map`, body);
      else await api.post(`/students/${mappingStudent.id}/map`, body);
      notify('Student mapping saved.', 'success');
      mappingStudent = null;
      await loadStudents();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save mapping.',
        'error'
      );
    }
  }

  async function importCsv() {
    if (!importFile) {
      notify('Choose a CSV file first.', 'error');
      return;
    }
    try {
      const result = await api.upload<{
        total_rows: number;
        successful: number;
        failed: number;
      }>('/students/import-mapping', 'csv_file', importFile);
      notify(
        `Imported ${result.successful}/${result.total_rows} rows.`,
        result.failed ? 'info' : 'success'
      );
      importOpen = false;
      importFile = null;
      await loadStudents();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not import CSV.',
        'error'
      );
    }
  }

  async function exportStudents(format = 'csv') {
    try {
      await api.download(
        '/students/export',
        `students.${format === 'excel' ? 'xlsx' : 'csv'}`,
        { ...query(), format }
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export students.',
        'error'
      );
    }
  }

  async function bulkWarn() {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    const reason = window.prompt('Reason for bulk warning');
    if (!reason) return;
    try {
      await api.post('/students/bulk/warn', {
        student_ids: ids,
        reason,
        level: 'level_1',
        send_email: true
      });
      notify('Bulk warnings issued.', 'success');
      selected = new Set();
      await loadStudents();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not issue bulk warning.',
        'error'
      );
    }
  }

  function toggleSort(column: string) {
    if (sort === column) order = order === 'asc' ? 'desc' : 'asc';
    else {
      sort = column;
      order = 'asc';
    }
    loadStudents();
  }

  function toggleSelected(id: string) {
    selected = new Set(selected);
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
  }

  function selectAll() {
    selected =
      selected.size === response.items.length
        ? new Set()
        : new Set(response.items.map((student) => student.id));
  }

  onMount(loadStudents);
</script>

<svelte:head>
  <title>Students | CleanPlates</title>
</svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Student mapping</p>
    <h2 class="mt-1 text-2xl font-semibold text-body">
      Device IDs and student profiles
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadStudents}
      ><RefreshCw size={16} />Refresh</Button
    >
    <Button
      variant="secondary"
      on:click={() => (importOpen = true)}
      id="btn-import-csv"><FileUp size={16} />Import</Button
    >
    <Button on:click={() => exportStudents('csv')} id="btn-export-students"
      ><Download size={16} />Export</Button
    >
  </div>
</div>

<Card title="Search and filters">
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
    <label
      ><span class="label">Status</span><select
        class="select-field mt-2 w-full"
        bind:value={filters.status}
        id="select-filter-status"
        ><option value="">All</option><option>green</option><option
          >yellow</option
        ><option>orange</option><option>red</option></select
      ></label
    >
    <label
      ><span class="label">Hostel</span><input
        class="input-field mt-2 w-full"
        bind:value={filters.hostel}
        id="select-filter-hostel"
      /></label
    >
    <label
      ><span class="label">Branch</span><input
        class="input-field mt-2 w-full"
        bind:value={filters.branch}
      /></label
    >
    <label
      ><span class="label">Year</span><select
        class="select-field mt-2 w-full"
        bind:value={filters.year}
        ><option value="">All</option><option>1</option><option>2</option
        ><option>3</option><option>4</option></select
      ></label
    >
    <div class="flex items-end">
      <Button
        class="w-full"
        on:click={() => {
          page = 1;
          loadStudents();
        }}>Apply</Button
      >
    </div>
  </div>
</Card>

<div class="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
  <StatCard title="Total" value={number(response.total)} helper="All device IDs"
    ><svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Mapped On Page"
    value={number(totalMapped)}
    helper={`${number(response.items.length)} visible`}
    tone="good"
    ><svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Warnings"
    value={number(warningCount)}
    helper="Current page"
    tone="warn"
    ><svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Penalties"
    value={number(penaltyCount)}
    helper="Current page"
    tone="bad"
    ><svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard title="Selected" value={number(selected.size)} helper="Bulk actions"
    ><svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment
    ></StatCard
  >
</div>

<Card
  class="mt-5"
  title="Students table"
  description="Mapping calls use the student UUID, not the card device ID."
>
  {#if error}
    <div class="rounded-md border border-down/30 bg-down/10 p-3 text-down">
      {error}
    </div>
  {:else if loading}
    <div class="h-96 animate-pulse rounded-lg bg-elevated"></div>
  {:else if response.items.length === 0}
    <EmptyState
      title="No students"
      message="Register devices or import student mappings to populate this table."
    />
  {:else}
    <div class="overflow-auto">
      <table>
        <thead class="bg-elevated">
          <tr>
            <th class="th"
              ><input
                id="chk-select-all"
                type="checkbox"
                checked={selected.size === response.items.length}
                on:change={selectAll}
              /></th
            >
            <th class="th"
              ><button on:click={() => toggleSort('status')}>Status</button></th
            >
            <th class="th"
              ><button on:click={() => toggleSort('device_id')}
                >Device ID</button
              ></th
            >
            <th class="th">Mapped Name</th>
            <th class="th"
              ><button on:click={() => toggleSort('warning_count')}
                >Warnings</button
              ></th
            >
            <th class="th">Avg Waste</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each response.items as student (student.id)}
            <tr>
              <td class="td"
                ><input
                  type="checkbox"
                  checked={selected.has(student.id)}
                  on:change={() => toggleSelected(student.id)}
                /></td
              >
              <td class="td"><StatusBadge value={student.status} compact /></td>
              <td class="td font-mono text-xs">{student.device_id}</td>
              <td class="td">
                {#if student.mapping}
                  <a
                    class="font-semibold text-primary"
                    href={`/dashboard/students/${student.id}`}
                    >{student.mapping.name}</a
                  >
                  <p class="text-xs text-muted">
                    {student.mapping.roll_number} · {student.mapping.branch} · Year
                    {student.mapping.year}
                  </p>
                {:else}
                  <StatusBadge value="unmapped" compact />
                {/if}
              </td>
              <td class="td"
                >{number(student.warning_count)} warnings · {number(
                  student.penalty_count
                )} penalties</td
              >
              <td class="td">{grams(student.avg_waste_grams)}</td>
              <td class="td">
                <div class="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => openMapping(student)}
                    id={`btn-map-${student.device_id}`}
                    >{student.mapping ? 'Edit' : 'Map'}</Button
                  >
                  <a
                    class="inline-flex h-9 items-center rounded-md border border-border px-3 text-xs font-semibold hover:border-primary"
                    href={`/dashboard/students/${student.id}`}>Open</a
                  >
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          on:click={bulkWarn}
          disabled={selected.size === 0}
          id="btn-bulk-warn">Bulk warn</Button
        >
        <Button
          variant="secondary"
          size="sm"
          on:click={() => exportStudents('excel')}
          disabled={selected.size === 0}
          id="btn-bulk-export">Bulk export</Button
        >
      </div>
      <div class="flex items-center gap-2" id="nav-pagination">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          on:click={() => {
            page -= 1;
            loadStudents();
          }}>Previous</Button
        >
        <span class="text-sm text-muted"
          >Page {response.page} of {response.pages}</span
        >
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= response.pages}
          on:click={() => {
            page += 1;
            loadStudents();
          }}>Next</Button
        >
        <select
          class="select-field"
          bind:value={size}
          on:change={() => {
            page = 1;
            loadStudents();
          }}
          id="select-page-size"
        >
          <option value={10}>10</option><option value={25}>25</option><option
            value={50}>50</option
          ><option value={100}>100</option>
        </select>
      </div>
    </div>
  {/if}
</Card>

<Modal
  open={!!mappingStudent}
  title={mappingStudent?.mapping ? 'Edit student mapping' : 'Map student ID'}
  description={mappingStudent?.device_id ?? ''}
  on:close={() => (mappingStudent = null)}
>
  <form
    class="grid gap-3 sm:grid-cols-2"
    on:submit|preventDefault={saveMapping}
  >
    <label
      ><span class="label">Full name</span><input
        class="input-field mt-2 w-full"
        bind:value={mapping.name}
        required
      /></label
    >
    <label
      ><span class="label">Roll number</span><input
        class="input-field mt-2 w-full"
        bind:value={mapping.roll_number}
        required
      /></label
    >
    <label
      ><span class="label">Branch</span><input
        class="input-field mt-2 w-full"
        bind:value={mapping.branch}
        required
      /></label
    >
    <label
      ><span class="label">Year</span><input
        class="input-field mt-2 w-full"
        type="number"
        min="1"
        max="4"
        bind:value={mapping.year}
        required
      /></label
    >
    <label
      ><span class="label">Hostel</span><input
        class="input-field mt-2 w-full"
        bind:value={mapping.hostel}
      /></label
    >
    <label
      ><span class="label">Room</span><input
        class="input-field mt-2 w-full"
        bind:value={mapping.room_number}
      /></label
    >
    <label class="sm:col-span-2"
      ><span class="label">Email</span><input
        class="input-field mt-2 w-full"
        type="email"
        bind:value={mapping.email}
      /></label
    >
    <div class="sm:col-span-2 flex justify-end gap-2 pt-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (mappingStudent = null)}>Cancel</Button
      >
      <Button type="submit">Save mapping</Button>
    </div>
  </form>
</Modal>

<Modal
  open={importOpen}
  title="Import student mappings"
  description="CSV columns: device_id,name,roll_number,year,branch,hostel,room_number,email"
  on:close={() => (importOpen = false)}
>
  <div class="space-y-4">
    <input
      class="input-field w-full py-2"
      type="file"
      accept=".csv,text/csv"
      on:change={(event) =>
        (importFile = event.currentTarget.files?.[0] ?? null)}
    />
    <div class="flex justify-end gap-2">
      <Button variant="secondary" on:click={() => (importOpen = false)}
        >Cancel</Button
      >
      <Button on:click={importCsv}>Import CSV</Button>
    </div>
  </div>
</Modal>
