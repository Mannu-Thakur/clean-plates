<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import {
    AlertTriangle,
    Download,
    FileUp,
    RefreshCw,
    UserPlus
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, Student } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import DataTable, {
    type TableColumn
  } from '$lib/components/ui/DataTable.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import FilterBar, {
    type FilterConfig
  } from '$lib/components/ui/FilterBar.svelte';
  import FormField from '$lib/components/ui/FormField.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import SearchInput from '$lib/components/ui/SearchInput.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { grams, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';
  import { STUDENT_STATUSES, WARNING_LEVELS } from '$lib/utils/constants';

  type StudentFilters = {
    status: string;
    branch: string;
    hostel: string;
    year: string;
  };
  type WarningForm = {
    level: string;
    reason: string;
    send_email: boolean;
  };

  const filterConfig: FilterConfig[] = [
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: '', label: 'All statuses' },
        ...STUDENT_STATUSES.map((s) => ({ value: s, label: titleCase(s) }))
      ]
    },
    { key: 'branch', label: 'Branch', type: 'text', placeholder: 'CSE' },
    { key: 'hostel', label: 'Hostel', type: 'text', placeholder: 'A Block' },
    {
      key: 'year',
      label: 'Year',
      type: 'select',
      options: [
        { value: '', label: 'All years' },
        { value: '1', label: 'Year 1' },
        { value: '2', label: 'Year 2' },
        { value: '3', label: 'Year 3' },
        { value: '4', label: 'Year 4' }
      ]
    }
  ];

  const columns: TableColumn[] = [
    { key: 'select', label: '', width: '48px' },
    { key: 'status', label: 'Status', sortable: true },
    { key: 'device_id', label: 'Device ID' },
    { key: 'name', label: 'Student', sortable: true },
    { key: 'branch', label: 'Branch', sortable: true },
    { key: 'warning_count', label: 'Warnings', sortable: true, align: 'right' },
    {
      key: 'avg_waste_grams',
      label: 'Avg waste',
      sortable: true,
      align: 'right'
    }
  ];

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
  let filters: StudentFilters = defaultFilters();
  let searchTerm = '';
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
  let importOpen = false;
  let importFile: File | null = null;
  let quickWarnStudent: Student | null = null;
  let quickWarning: WarningForm = defaultWarningForm();
  let bulkWarnOpen = false;
  let bulkWarning: WarningForm = defaultWarningForm();

  $: filterRecord = filters as unknown as Record<string, unknown>;
  $: visibleStudents = response.items.filter(matchesSearch);
  $: tableRows = visibleStudents as unknown as Record<string, unknown>[];
  $: totalMapped = response.items.filter((student) => student.mapping).length;
  $: warningCount = response.items.filter(
    (student) => student.warning_count > 0
  ).length;
  $: penaltyCount = response.items.filter(
    (student) => student.penalty_count > 0
  ).length;
  $: visibleSelected =
    visibleStudents.length > 0 &&
    visibleStudents.every((student) => selected.has(student.id));
  $: canBulkWarn = selected.size > 0 && !loading;
  $: canSubmitBulkWarning =
    selected.size > 0 && bulkWarning.reason.trim().length > 0;

  function defaultFilters(): StudentFilters {
    return { status: '', branch: '', hostel: '', year: '' };
  }

  function defaultWarningForm(): WarningForm {
    return { level: 'level_1', reason: '', send_email: true };
  }

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

  function mappingOf(row: Record<string, unknown>) {
    return (row.mapping ?? null) as Student['mapping'];
  }

  function studentOf(row: Record<string, unknown>) {
    return row as unknown as Student;
  }

  function matchesSearch(student: Student) {
    const needle = searchTerm.trim().toLowerCase();
    if (!needle) return true;
    const haystack = [
      student.device_id,
      student.mapping?.name,
      student.mapping?.roll_number,
      student.mapping?.branch,
      student.mapping?.hostel,
      student.mapping?.email
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(needle);
  }

  async function loadStudents() {
    loading = true;
    error = '';
    try {
      response = await api.get<Paginated<Student>>('/students/', query());
      selected = new Set(
        Array.from(selected).filter((id) =>
          response.items.some((student) => student.id === id)
        )
      );
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load students';
    } finally {
      loading = false;
    }
  }

  function applyFilters(values: Record<string, unknown>) {
    filters = {
      status: String(values.status ?? ''),
      branch: String(values.branch ?? ''),
      hostel: String(values.hostel ?? ''),
      year: String(values.year ?? '')
    };
    page = 1;
    loadStudents();
  }

  function resetFilters() {
    filters = defaultFilters();
    page = 1;
    loadStudents();
  }

  function toggleSort(key: string) {
    if (sort === key) {
      order = order === 'asc' ? 'desc' : 'asc';
    } else {
      sort = key;
      order = 'desc';
    }
    page = 1;
    loadStudents();
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadStudents();
  }

  function toggleSelected(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selected = next;
  }

  function toggleVisibleSelection() {
    const next = new Set(selected);
    if (visibleSelected) {
      visibleStudents.forEach((student) => next.delete(student.id));
    } else {
      visibleStudents.forEach((student) => next.add(student.id));
    }
    selected = next;
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
      notify('Choose a CSV file first.', 'warning');
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
        result.failed ? 'warning' : 'success'
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

  function openQuickWarning(student: Student) {
    quickWarnStudent = student;
    quickWarning = defaultWarningForm();
  }

  async function issueQuickWarning() {
    if (!quickWarnStudent) return;
    try {
      await api.post(`/students/${quickWarnStudent.id}/warnings`, quickWarning);
      notify('Warning issued.', 'success');
      quickWarnStudent = null;
      quickWarning = defaultWarningForm();
      await loadStudents();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not issue warning.',
        'error'
      );
    }
  }

  function openBulkWarning() {
    if (!canBulkWarn) {
      notify('Choose at least one student.', 'warning');
      return;
    }
    bulkWarning = defaultWarningForm();
    bulkWarnOpen = true;
  }

  async function issueBulkWarning() {
    const ids = Array.from(selected);
    if (ids.length === 0 || !bulkWarning.reason.trim()) return;
    try {
      await api.post('/students/bulk/warn', {
        student_ids: ids,
        ...bulkWarning,
        reason: bulkWarning.reason.trim()
      });
      notify('Bulk warnings issued.', 'success');
      selected = new Set();
      bulkWarnOpen = false;
      bulkWarning = defaultWarningForm();
      await loadStudents();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not issue bulk warning.',
        'error'
      );
    }
  }

  onMount(loadStudents);
</script>

<svelte:head>
  <title>Students | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Student intelligence"
  title="Student profiles, mappings, and warnings"
  description="Filter by supported server fields, search the visible page locally, and open full Phase 3 student profiles."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={loadStudents}
      id="btn-refresh-students"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={() => (importOpen = true)}
      id="btn-import-csv"
    >
      <FileUp size={16} />
      Import
    </Button>
    <Button on:click={() => exportStudents('csv')} id="btn-export-students">
      <Download size={16} />
      Export
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="mb-5 grid gap-3 xl:grid-cols-[320px_1fr]">
  <div class="card p-4">
    <span class="form-label">Search current page</span>
    <SearchInput
      value={searchTerm}
      placeholder="Name, roll number, device ID"
      onSearch={(value) => (searchTerm = value)}
      onClear={() => (searchTerm = '')}
      id="input-student-search"
    />
    <p class="mt-2 text-xs text-muted">
      Search is client-side only and is not sent to the students API.
    </p>
  </div>

  <FilterBar
    filters={filterConfig}
    values={filterRecord}
    onFilter={applyFilters}
    onReset={resetFilters}
  />
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
  <StatCard
    title="Total"
    value={number(response.total)}
    helper="All matching students"
  >
    <svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Mapped On Page"
    value={number(totalMapped)}
    helper={`${number(response.items.length)} visible from server`}
    tone="good"
  >
    <svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Warnings"
    value={number(warningCount)}
    helper="Current page"
    tone="warn"
  >
    <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Penalties"
    value={number(penaltyCount)}
    helper="Current page"
    tone="bad"
  >
    <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Selected"
    value={number(selected.size)}
    helper="Bulk warning queue"
  >
    <svelte:fragment slot="icon"><UserPlus size={19} /></svelte:fragment>
  </StatCard>
</div>

<div class="mt-5 flex flex-wrap items-center justify-between gap-3">
  <div class="flex flex-wrap gap-2">
    <Button
      variant="secondary"
      size="sm"
      on:click={toggleVisibleSelection}
      disabled={visibleStudents.length === 0}
      id="btn-select-visible"
    >
      {visibleSelected ? 'Clear visible' : 'Select visible'}
    </Button>
    <Button
      variant="secondary"
      size="sm"
      on:click={openBulkWarning}
      disabled={!canBulkWarn}
      id="btn-bulk-warn"
    >
      Bulk warn
    </Button>
  </div>

  <select
    class="select-field w-28"
    bind:value={size}
    on:change={() => {
      page = 1;
      loadStudents();
    }}
    id="select-page-size"
  >
    <option value={10}>10</option>
    <option value={25}>25</option>
    <option value={50}>50</option>
    <option value={100}>100</option>
  </select>
</div>

<div class="mt-4">
  {#if error}
    <Card title="Students unavailable" description={error}>
      <Button on:click={loadStudents}>Retry</Button>
    </Card>
  {:else}
    <DataTable
      {columns}
      rows={tableRows}
      {loading}
      {page}
      total={response.total}
      pageSize={size}
      sortKey={sort}
      sortDirection={order}
      onSort={toggleSort}
      onPageChange={goToPage}
      onRowClick={(row) => goto(`/dashboard/students/${studentOf(row).id}`)}
    >
      <svelte:fragment slot="cell" let:row let:column let:value>
        {#if column.key === 'select'}
          <input
            type="checkbox"
            checked={selected.has(studentOf(row).id)}
            on:click|stopPropagation
            on:change={() => toggleSelected(studentOf(row).id)}
            aria-label={`Select ${studentOf(row).device_id}`}
          />
        {:else if column.key === 'status'}
          <StatusBadge value={String(value)} compact />
        {:else if column.key === 'device_id'}
          <span class="font-mono text-xs text-muted-strong">
            {studentOf(row).device_id}
          </span>
        {:else if column.key === 'name'}
          {#if mappingOf(row)}
            <div>
              <p class="font-semibold text-body">{mappingOf(row)?.name}</p>
              <p class="mt-1 text-xs text-muted">
                {mappingOf(row)?.roll_number} / {mappingOf(row)?.branch} / Year
                {mappingOf(row)?.year}
              </p>
            </div>
          {:else}
            <StatusBadge value="unmapped" compact />
          {/if}
        {:else if column.key === 'branch'}
          {#if mappingOf(row)}
            <div>
              <p>{mappingOf(row)?.branch}</p>
              <p class="mt-1 text-xs text-muted">
                {mappingOf(row)?.hostel ?? 'No hostel'}
              </p>
            </div>
          {:else}
            <span class="text-muted">-</span>
          {/if}
        {:else if column.key === 'warning_count'}
          <span>
            {number(studentOf(row).warning_count)} / {number(
              studentOf(row).penalty_count
            )}
          </span>
        {:else if column.key === 'avg_waste_grams'}
          {grams(studentOf(row).avg_waste_grams)}
        {:else}
          {value ?? '-'}
        {/if}
      </svelte:fragment>

      <svelte:fragment slot="row-actions" let:row>
        <div class="flex flex-wrap justify-end gap-2">
          <Button
            size="sm"
            variant="secondary"
            on:click={() => openMapping(studentOf(row))}
            id={`btn-map-${studentOf(row).device_id}`}
          >
            {studentOf(row).mapping ? 'Edit' : 'Map'}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            on:click={() => openQuickWarning(studentOf(row))}
            id={`btn-warn-${studentOf(row).device_id}`}
          >
            Warn
          </Button>
        </div>
      </svelte:fragment>

      <svelte:fragment slot="empty">
        <EmptyState
          title="No students"
          message="Adjust the filters, clear local search, or import student mappings."
        />
      </svelte:fragment>
    </DataTable>
  {/if}
</div>

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
    <FormField label="Full name" required>
      <input class="input-field" bind:value={mapping.name} required />
    </FormField>
    <FormField label="Roll number" required>
      <input class="input-field" bind:value={mapping.roll_number} required />
    </FormField>
    <FormField label="Branch" required>
      <input class="input-field" bind:value={mapping.branch} required />
    </FormField>
    <FormField label="Year" required>
      <input
        class="input-field"
        type="number"
        min="1"
        max="4"
        bind:value={mapping.year}
        required
      />
    </FormField>
    <FormField label="Hostel">
      <input class="input-field" bind:value={mapping.hostel} />
    </FormField>
    <FormField label="Room">
      <input class="input-field" bind:value={mapping.room_number} />
    </FormField>
    <div class="sm:col-span-2">
      <FormField label="Email">
        <input class="input-field" type="email" bind:value={mapping.email} />
      </FormField>
    </div>
    <div class="flex justify-end gap-2 pt-2 sm:col-span-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (mappingStudent = null)}
      >
        Cancel
      </Button>
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
    <FileUpload
      accept=".csv,text/csv"
      maxSizeMb={5}
      label="Upload mapping CSV"
      onSelect={(file) => (importFile = file)}
    />
    <div class="flex justify-end gap-2">
      <Button variant="secondary" on:click={() => (importOpen = false)}>
        Cancel
      </Button>
      <Button on:click={importCsv}>Import CSV</Button>
    </div>
  </div>
</Modal>

<Modal
  open={!!quickWarnStudent}
  title="Issue warning"
  description={quickWarnStudent?.mapping?.name ??
    quickWarnStudent?.device_id ??
    ''}
  on:close={() => (quickWarnStudent = null)}
>
  <form class="space-y-3" on:submit|preventDefault={issueQuickWarning}>
    <FormField label="Level" required>
      <select class="select-field" bind:value={quickWarning.level}>
        {#each WARNING_LEVELS as level, i}
          <option value={level}>Level {i + 1}</option>
        {/each}
      </select>
    </FormField>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={quickWarning.reason} required
      ></textarea>
    </FormField>
    <label class="flex items-center gap-2 text-sm text-muted-strong">
      <input type="checkbox" bind:checked={quickWarning.send_email} />
      Send email
    </label>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (quickWarnStudent = null)}
      >
        Cancel
      </Button>
      <Button type="submit">Issue warning</Button>
    </div>
  </form>
</Modal>

<Modal
  open={bulkWarnOpen}
  title="Bulk warning"
  description={`${number(selected.size)} selected students`}
  on:close={() => (bulkWarnOpen = false)}
>
  <form class="space-y-3" on:submit|preventDefault={issueBulkWarning}>
    <FormField label="Level" required>
      <select class="select-field" bind:value={bulkWarning.level}>
        {#each WARNING_LEVELS as level, i}
          <option value={level}>Level {i + 1}</option>
        {/each}
      </select>
    </FormField>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={bulkWarning.reason} required
      ></textarea>
    </FormField>
    <label class="flex items-center gap-2 text-sm text-muted-strong">
      <input type="checkbox" bind:checked={bulkWarning.send_email} />
      Send email
    </label>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (bulkWarnOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" disabled={!canSubmitBulkWarning}>
        Warn selected
      </Button>
    </div>
  </form>
</Modal>
