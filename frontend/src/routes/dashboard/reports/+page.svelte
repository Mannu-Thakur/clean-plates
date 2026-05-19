<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    Calendar,
    Clock,
    Download,
    FileText,
    Plus,
    RefreshCw
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, ReportItem, ReportSchedule } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import DataTable, {
    type TableColumn
  } from '$lib/components/ui/DataTable.svelte';
  import DateRangePicker from '$lib/components/ui/DateRangePicker.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FormField from '$lib/components/ui/FormField.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, fileSize, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type DateRange = { start: string | null; end: string | null };
  type ReportFilters = {
    type: string;
    date: DateRange;
  };

  const reportTypes = ['overview', 'students', 'warnings', 'devices'];
  const reportFormats = [
    { value: 'pdf', label: 'PDF' },
    { value: 'xlsx', label: 'XLSX' },
    { value: 'csv', label: 'CSV' }
  ];
  const reportColumns: TableColumn[] = [
    { key: 'type', label: 'Report', sortable: true },
    { key: 'format', label: 'Format', width: '110px' },
    { key: 'status', label: 'Status', width: '130px' },
    { key: 'file_size', label: 'Size', align: 'right', width: '110px' },
    { key: 'created_at', label: 'Created', sortable: true, width: '180px' },
    { key: 'generated_at', label: 'Generated', width: '180px' }
  ];

  let loading = true;
  let error = '';
  let page = 1;
  let size = 20;
  let reports: Paginated<ReportItem> = emptyPage();
  let schedules: ReportSchedule[] = [];
  let generateOpen = false;
  let submitting = false;
  let downloadingReports = new Set<string>();
  let filters: ReportFilters = defaultFilters();
  let form = defaultForm();
  let pollHandle: ReturnType<typeof setInterval> | null = null;

  $: reportRows = reports.items as unknown as Record<string, unknown>[];
  $: readyCount = reports.items.filter(canDownload).length;
  $: pendingCount = reports.items.filter(isPending).length;
  $: failedCount = reports.items.filter(
    (report) => report.status === 'failed'
  ).length;

  function emptyPage(): Paginated<ReportItem> {
    return { items: [], total: 0, page: 1, size, pages: 1 };
  }

  function defaultFilters(): ReportFilters {
    return {
      type: '',
      date: { start: null, end: null }
    };
  }

  function defaultForm() {
    return {
      type: 'overview',
      format: 'pdf',
      date: { start: null, end: null } as DateRange
    };
  }

  function listQuery() {
    return {
      type: filters.type,
      date_from: filters.date.start ?? undefined,
      date_to: filters.date.end ?? undefined,
      page,
      size
    };
  }

  function statusKey(report: ReportItem) {
    return String(report.status ?? '').toLowerCase();
  }

  function canDownload(report: ReportItem) {
    return ['ready', 'completed', 'complete'].includes(statusKey(report));
  }

  function isPending(report: ReportItem) {
    return ['pending', 'queued', 'generating'].includes(statusKey(report));
  }

  function reportOf(row: Record<string, unknown>) {
    return row as unknown as ReportItem;
  }

  function formatLabel(format: string) {
    return format === 'excel' || format === 'xlsx'
      ? 'XLSX'
      : format.toUpperCase();
  }

  function reportFilename(report: ReportItem) {
    const ext =
      report.format === 'excel' || report.format === 'xlsx'
        ? 'xlsx'
        : report.format;
    return `${report.type}-${report.id}.${ext}`;
  }

  function resetFilters() {
    filters = defaultFilters();
    page = 1;
    loadReports();
  }

  function setFilterDate(start: string | null, end: string | null) {
    filters = { ...filters, date: { start, end } };
    page = 1;
    loadReports();
  }

  function setFormDate(start: string | null, end: string | null) {
    form = { ...form, date: { start, end } };
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadReports();
  }

  function applyTypeFilter() {
    page = 1;
    loadReports();
  }

  function openGenerate() {
    form = defaultForm();
    generateOpen = true;
  }

  function stopPolling() {
    if (!pollHandle) return;
    clearInterval(pollHandle);
    pollHandle = null;
  }

  function refreshPolling() {
    if (reports.items.some(isPending)) {
      if (!pollHandle) {
        pollHandle = setInterval(() => loadReports(false), 12000);
      }
    } else {
      stopPolling();
    }
  }

  async function loadReports(showLoading = true) {
    if (showLoading) loading = true;
    error = '';
    try {
      const [reportData, scheduleData] = await Promise.all([
        api.get<Paginated<ReportItem>>('/reports', listQuery()),
        api.get<ReportSchedule[]>('/reports/schedules').catch(() => [])
      ]);
      reports = reportData;
      schedules = scheduleData;
      refreshPolling();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load reports';
      stopPolling();
    } finally {
      loading = false;
    }
  }

  async function generateReport() {
    submitting = true;
    try {
      await api.post<ReportItem>('/reports/generate', {
        type: form.type,
        format: form.format,
        date_from: form.date.start,
        date_to: form.date.end,
        filters: {}
      });
      notify(`${titleCase(form.type)} report queued.`, 'success');
      generateOpen = false;
      await loadReports(false);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not queue report.',
        'error'
      );
    } finally {
      submitting = false;
    }
  }

  async function downloadReport(report: ReportItem) {
    if (!canDownload(report) || downloadingReports.has(report.id)) return;
    downloadingReports = new Set(downloadingReports).add(report.id);
    try {
      await api.download(
        `/reports/${report.id}/download`,
        reportFilename(report)
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not download report.',
        'error'
      );
    } finally {
      const next = new Set(downloadingReports);
      next.delete(report.id);
      downloadingReports = next;
    }
  }

  onMount(() => loadReports());
  onDestroy(stopPolling);
</script>

<svelte:head>
  <title>Reports | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Report generator"
  title="Generate, download, and review recurring reports"
  description="Queue overview, student, warning, and device reports as PDF, XLSX, or CSV files."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={() => loadReports()}
      id="btn-refresh-reports"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button on:click={openGenerate} id="btn-generate-report">
      <Plus size={16} />
      Generate report
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Reports"
    value={number(reports.total)}
    helper="Matching history"
  >
    <svelte:fragment slot="icon"><FileText size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Ready"
    value={number(readyCount)}
    helper="Downloadable on this page"
    tone="good"
  >
    <svelte:fragment slot="icon"><Download size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Pending"
    value={number(pendingCount)}
    helper="Auto-refreshing"
    tone="warn"
  >
    <svelte:fragment slot="icon"><Clock size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Schedules"
    value={number(schedules.length)}
    helper="Recurring reports"
    tone={failedCount > 0 ? 'bad' : 'neutral'}
  >
    <svelte:fragment slot="icon"><Calendar size={19} /></svelte:fragment>
  </StatCard>
</div>

<Card class="mt-5" title="Report filters">
  <div class="grid gap-4 lg:grid-cols-[220px_1fr_auto]">
    <label>
      <span class="label">Report type</span>
      <select
        class="select-field mt-2"
        bind:value={filters.type}
        on:change={applyTypeFilter}
        id="select-report-type-filter"
      >
        <option value="">All reports</option>
        {#each reportTypes as type}
          <option value={type}>{titleCase(type)}</option>
        {/each}
      </select>
    </label>
    <div>
      <span class="label">Created date range</span>
      <div class="mt-2">
        <DateRangePicker
          start={filters.date.start}
          end={filters.date.end}
          onChange={setFilterDate}
        />
      </div>
    </div>
    <div class="flex items-end">
      <Button variant="secondary" on:click={resetFilters}>Reset</Button>
    </div>
  </div>
</Card>

<div class="mt-5 grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
  <section class="space-y-3">
    <div>
      <h2 class="text-base font-semibold text-body">Report history</h2>
      <p class="mt-1 text-sm text-muted">
        Past generated reports with status and download actions.
      </p>
    </div>
    {#if error}
      <div
        class="rounded-md border border-down/30 bg-down/10 p-3 text-sm text-down"
      >
        {error}
      </div>
    {:else}
      <DataTable
        columns={reportColumns}
        rows={reportRows}
        {loading}
        {page}
        total={reports.total}
        pageSize={size}
        onPageChange={goToPage}
      >
        <svelte:fragment slot="cell" let:row let:column let:value>
          {@const report = reportOf(row)}
          {#if column.key === 'type'}
            <div>
              <p class="font-semibold text-body">{titleCase(report.type)}</p>
              <p class="mt-1 font-mono text-xs text-muted">{report.id}</p>
            </div>
          {:else if column.key === 'format'}
            <span class="badge-info">{formatLabel(report.format)}</span>
          {:else if column.key === 'status'}
            <StatusBadge value={report.status} compact />
          {:else if column.key === 'file_size'}
            {fileSize(report.file_size)}
          {:else if column.key === 'created_at'}
            {dateTime(report.created_at)}
          {:else if column.key === 'generated_at'}
            {dateTime(report.generated_at)}
          {:else}
            {value ?? '-'}
          {/if}
        </svelte:fragment>

        <svelte:fragment slot="row-actions" let:row>
          {@const report = reportOf(row)}
          <Button
            size="sm"
            variant="secondary"
            disabled={!canDownload(report) || downloadingReports.has(report.id)}
            on:click={() => downloadReport(report)}
            id={`btn-download-report-${report.id}`}
          >
            <Download size={14} />
            {downloadingReports.has(report.id) ? 'Downloading...' : 'Download'}
          </Button>
        </svelte:fragment>

        <svelte:fragment slot="empty">
          <EmptyState
            title="No reports"
            message="Generated reports for the selected filters will appear here."
          />
        </svelte:fragment>
      </DataTable>
    {/if}
  </section>

  <Card title="Recurring schedules">
    {#if loading}
      <div class="space-y-3">
        {#each Array.from({ length: 4 }) as _}
          <div class="skeleton h-20"></div>
        {/each}
      </div>
    {:else if schedules.length === 0}
      <EmptyState
        title="No schedules"
        message="Recurring report schedules created by admins appear here."
      />
    {:else}
      <div class="space-y-3">
        {#each schedules as schedule}
          <div class="rounded-lg border border-border bg-elevated/40 p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="font-semibold text-body">
                  {titleCase(schedule.report_type)}
                </p>
                <p class="mt-1 text-sm text-muted">
                  {titleCase(schedule.frequency)}
                  {schedule.day_of_week ? ` / ${titleCase(schedule.day_of_week)}` : ''}
                  / {schedule.time_of_day}
                </p>
              </div>
              <StatusBadge value={schedule.active} compact />
            </div>
            <div class="mt-3 grid gap-2 text-sm text-muted">
              <p>Format {formatLabel(schedule.format)}</p>
              <p>Next run {dateTime(schedule.next_run)}</p>
              <p>Last run {dateTime(schedule.last_run)}</p>
              {#if schedule.auto_email}
                <p>
                  Email recipients {number(schedule.email_recipients.length)}
                </p>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </Card>
</div>

<Modal
  open={generateOpen}
  title="Generate report"
  description="Queue a report for the selected type, format, and date window."
  on:close={() => (generateOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={generateReport}>
    <div class="grid gap-3 sm:grid-cols-2">
      <FormField label="Report type" required>
        <select class="select-field" bind:value={form.type} required>
          {#each reportTypes as type}
            <option value={type}>{titleCase(type)}</option>
          {/each}
        </select>
      </FormField>
      <FormField label="Format" required>
        <select class="select-field" bind:value={form.format} required>
          {#each reportFormats as format}
            <option value={format.value}>{format.label}</option>
          {/each}
        </select>
      </FormField>
    </div>

    <FormField label="Date range">
      <DateRangePicker
        start={form.date.start}
        end={form.date.end}
        onChange={setFormDate}
      />
    </FormField>

    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (generateOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" disabled={submitting} id="btn-submit-report">
        {submitting ? 'Queueing...' : 'Queue report'}
      </Button>
    </div>
  </form>
</Modal>
