<script lang="ts">
  import { onMount } from 'svelte';
  import {
    AlertTriangle,
    ArrowUpCircle,
    CheckCircle2,
    Download,
    Eye,
    Plus,
    RefreshCw,
    ShieldAlert
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, Student } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import DataTable, {
    type TableColumn
  } from '$lib/components/ui/DataTable.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FilterBar, {
    type FilterConfig
  } from '$lib/components/ui/FilterBar.svelte';
  import FormField from '$lib/components/ui/FormField.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import SearchInput from '$lib/components/ui/SearchInput.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs, { type TabItem } from '$lib/components/ui/Tabs.svelte';
  import { PENALTY_TYPES, WARNING_LEVELS } from '$lib/utils/constants';
  import { dateTime, itemsOf, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type WarningsTab = 'active' | 'resolved' | 'penalties' | 'escalations';
  type DateRange = { start: string | null; end: string | null };
  type WarningFilters = {
    search: string;
    level: string;
    rule_id: string;
    penalty_type: string;
    status: string;
    date: DateRange;
  };
  type WarningStats = {
    total_warnings?: number;
    active_warnings?: number;
    resolved_today?: number;
    pending_escalations?: number;
    escalated?: number;
    total_penalties?: number;
    active_penalties?: number;
  };
  type Warning = {
    id: string;
    student_id: string;
    student_name?: string | null;
    student_roll_number?: string | null;
    student_roll?: string | null;
    level: string;
    reason: string;
    rule_id?: string | null;
    rule_name?: string | null;
    waste_entry_id?: string | null;
    evidence?: string | null;
    status: string;
    send_email?: boolean;
    created_at: string;
    resolved_at?: string | null;
    resolved_by?: string | null;
    penalties?: Penalty[];
    escalations?: Escalation[];
  };
  type Penalty = {
    id: string;
    warning_id?: string | null;
    student_id: string;
    student_name?: string | null;
    student_roll_number?: string | null;
    penalty_type?: string | null;
    amount?: number | null;
    points?: number | null;
    reason: string;
    status: string;
    created_at: string;
  };
  type Escalation = {
    id: string;
    warning_id: string;
    student_id: string;
    student_name?: string | null;
    original_warning?: string | null;
    level?: string | null;
    escalated_to?: string | null;
    escalated_to_role?: string | null;
    note?: string | null;
    reason?: string | null;
    status: string;
    created_at: string;
  };
  type StudentOption = {
    id: string;
    label: string;
    meta: string;
  };

  const tabs: TabItem[] = [
    { id: 'active', label: 'Active Warnings', icon: ShieldAlert },
    { id: 'resolved', label: 'Resolved', icon: CheckCircle2 },
    { id: 'penalties', label: 'Penalties', icon: AlertTriangle },
    { id: 'escalations', label: 'Escalations', icon: ArrowUpCircle }
  ];
  const warningColumns: TableColumn[] = [
    { key: 'select', label: '', width: '48px' },
    { key: 'student', label: 'Student', sortable: true },
    { key: 'level', label: 'Level', sortable: true, width: '110px' },
    { key: 'reason', label: 'Reason' },
    { key: 'rule_name', label: 'Rule' },
    { key: 'status', label: 'Status', sortable: true, width: '110px' },
    { key: 'created_at', label: 'Date', sortable: true, width: '150px' }
  ];
  const penaltyColumns: TableColumn[] = [
    { key: 'student', label: 'Student', sortable: true },
    { key: 'points', label: 'Points', sortable: true, width: '120px' },
    { key: 'reason', label: 'Reason' },
    { key: 'warning_id', label: 'Warning' },
    { key: 'status', label: 'Status', sortable: true, width: '110px' },
    { key: 'created_at', label: 'Date', sortable: true, width: '150px' }
  ];
  const escalationColumns: TableColumn[] = [
    { key: 'student', label: 'Student' },
    { key: 'warning_id', label: 'Original Warning' },
    { key: 'level', label: 'Level', width: '110px' },
    { key: 'escalated_to', label: 'Escalated To' },
    { key: 'note', label: 'Note' },
    { key: 'status', label: 'Status', width: '110px' },
    { key: 'created_at', label: 'Date', width: '150px' }
  ];

  let activeTab: WarningsTab = 'active';
  let loading = true;
  let error = '';
  let page = 1;
  let size = 25;
  let sort = 'created_at';
  let order: 'asc' | 'desc' = 'desc';
  let stats: WarningStats = {};
  let warnings: Paginated<Warning> = emptyPage<Warning>();
  let penalties: Paginated<Penalty> = emptyPage<Penalty>();
  let escalations: Paginated<Escalation> = emptyPage<Escalation>();
  let filters: WarningFilters = defaultFilters();
  let selected = new Set<string>();
  let ruleOptions = [{ value: '', label: 'All rules' }];

  let detailWarning: Warning | null = null;
  let resolveTarget: Warning | null = null;
  let resolveNote = '';
  let escalateTarget: Warning | null = null;
  let escalationReason = '';
  let escalationRole = 'institution_admin';
  let bulkResolveOpen = false;
  let bulkResolveNote = '';
  let exportOpen = false;
  let exportFormat = 'csv';
  let revokeTarget: Penalty | null = null;
  let revokeReason = '';
  let reviewTarget: Escalation | null = null;
  let reviewResolution = 'approved';
  let reviewNote = '';

  let studentPickerMode: 'warning' | 'penalty' = 'warning';
  let studentSearch = '';
  let studentSearching = false;
  let studentOptions: StudentOption[] = [];
  let manualWarnOpen = false;
  let directPenaltyOpen = false;
  let warningForm = defaultWarningForm();
  let penaltyForm = defaultPenaltyForm();

  $: filterRecord = filters as unknown as Record<string, unknown>;
  $: currentFilterConfig = filtersForTab(activeTab);
  $: warningRows = warnings.items.filter(
    matchesWarningSearch
  ) as unknown as Record<string, unknown>[];
  $: penaltyRows = penalties.items.filter(
    matchesPenaltySearch
  ) as unknown as Record<string, unknown>[];
  $: escalationRows = escalations.items.filter(
    matchesEscalationSearch
  ) as unknown as Record<string, unknown>[];
  $: selectedCount = selected.size;
  $: visibleWarnings = warnings.items.filter(matchesWarningSearch);
  $: visibleSelected =
    visibleWarnings.length > 0 &&
    visibleWarnings.every((warning) => selected.has(warning.id));

  function emptyPage<T>(pageNumber = 1, pageSize = 25): Paginated<T> {
    return { items: [], total: 0, page: pageNumber, size: pageSize, pages: 1 };
  }

  function defaultFilters(): WarningFilters {
    return {
      search: '',
      level: '',
      rule_id: '',
      penalty_type: '',
      status: '',
      date: { start: null, end: null }
    };
  }

  function defaultWarningForm() {
    return {
      student_id: '',
      student_label: '',
      level: WARNING_LEVELS[0],
      reason: '',
      food_items: '',
      send_email: true
    };
  }

  function defaultPenaltyForm() {
    return {
      student_id: '',
      student_label: '',
      amount: '',
      reason: ''
    };
  }

  function asPage<T>(
    payload: Paginated<T> | T[] | null | undefined,
    fallbackPage = page,
    fallbackSize = size
  ): Paginated<T> {
    if (Array.isArray(payload)) {
      return {
        items: payload,
        total: payload.length,
        page: fallbackPage,
        size: fallbackSize,
        pages: 1
      };
    }
    return payload ?? emptyPage<T>(fallbackPage, fallbackSize);
  }

  function normalizeStats(payload: WarningStats | null | undefined) {
    stats = payload ?? {};
  }

  function filtersForTab(tab: WarningsTab): FilterConfig[] {
    const dateFilter: FilterConfig = {
      key: 'date',
      label: 'Date Range',
      type: 'date-range'
    };
    if (tab === 'penalties') {
      return [
        {
          key: 'search',
          label: 'Search',
          type: 'text',
          placeholder: 'Student or reason'
        },
        {
          key: 'penalty_type',
          label: 'Type',
          type: 'select',
          options: [
            { value: '', label: 'All types' },
            ...PENALTY_TYPES.map((type) => ({
              value: type,
              label: titleCase(type)
            }))
          ]
        },
        {
          key: 'status',
          label: 'Status',
          type: 'select',
          options: [
            { value: '', label: 'All statuses' },
            { value: 'active', label: 'Active' },
            { value: 'paid', label: 'Paid' },
            { value: 'waived', label: 'Waived' },
            { value: 'revoked', label: 'Revoked' }
          ]
        },
        dateFilter
      ];
    }
    if (tab === 'escalations') {
      return [
        {
          key: 'search',
          label: 'Search',
          type: 'text',
          placeholder: 'Student, note, warning ID'
        },
        {
          key: 'status',
          label: 'Status',
          type: 'select',
          options: [
            { value: '', label: 'All statuses' },
            { value: 'pending', label: 'Pending' },
            { value: 'resolved', label: 'Resolved' },
            { value: 'dismissed', label: 'Dismissed' }
          ]
        },
        dateFilter
      ];
    }
    return [
      {
        key: 'search',
        label: 'Search',
        type: 'text',
        placeholder: 'Student, roll number, reason'
      },
      {
        key: 'level',
        label: 'Level',
        type: 'select',
        options: [
          { value: '', label: 'All levels' },
          { value: 'level_1', label: 'Yellow' },
          { value: 'level_2', label: 'Orange' },
          { value: 'level_3', label: 'Red' },
          { value: 'yellow', label: 'Yellow legacy' },
          { value: 'orange', label: 'Orange legacy' },
          { value: 'red', label: 'Red legacy' }
        ]
      },
      {
        key: 'rule_id',
        label: 'Rule',
        type: 'select',
        options: ruleOptions
      },
      dateFilter
    ];
  }

  function baseQuery() {
    return {
      page,
      size,
      sort,
      order,
      date_from: filters.date.start ?? undefined,
      date_to: filters.date.end ?? undefined
    };
  }

  function warningQuery() {
    return {
      ...baseQuery(),
      status: activeTab === 'resolved' ? 'resolved' : 'active',
      level: filters.level,
      rule_id: filters.rule_id
    };
  }

  function penaltyQuery() {
    return {
      ...baseQuery(),
      penalty_type: filters.penalty_type,
      status: filters.status
    };
  }

  function escalationQuery() {
    return {
      ...baseQuery(),
      status: filters.status
    };
  }

  function exportQuery() {
    const query = warningQuery();
    return {
      status: query.status,
      level: query.level,
      rule_id: query.rule_id,
      date_from: query.date_from,
      date_to: query.date_to,
      format: exportFormat
    };
  }

  function rowText(values: Array<string | number | null | undefined>) {
    return values
      .filter((value) => value !== null && value !== undefined)
      .join(' ')
      .toLowerCase();
  }

  function matchesWarningSearch(warning: Warning) {
    const needle = filters.search.trim().toLowerCase();
    if (!needle) return true;
    return rowText([
      warning.student_name,
      warning.student_roll_number,
      warning.student_roll,
      warning.reason,
      warning.rule_name,
      warning.id
    ]).includes(needle);
  }

  function matchesPenaltySearch(penalty: Penalty) {
    const needle = filters.search.trim().toLowerCase();
    if (!needle) return true;
    return rowText([
      penalty.student_name,
      penalty.student_roll_number,
      penalty.reason,
      penalty.warning_id,
      penalty.id
    ]).includes(needle);
  }

  function matchesEscalationSearch(escalation: Escalation) {
    const needle = filters.search.trim().toLowerCase();
    if (!needle) return true;
    return rowText([
      escalation.student_name,
      escalation.warning_id,
      escalation.note,
      escalation.reason,
      escalation.escalated_to,
      escalation.escalated_to_role
    ]).includes(needle);
  }

  function warningOf(row: Record<string, unknown>) {
    return row as unknown as Warning;
  }

  function penaltyOf(row: Record<string, unknown>) {
    return row as unknown as Penalty;
  }

  function escalationOf(row: Record<string, unknown>) {
    return row as unknown as Escalation;
  }

  function levelLabel(level: string | null | undefined) {
    const normalized = String(level ?? '').toLowerCase();
    if (normalized === 'level_1' || normalized === 'yellow') return 'Yellow';
    if (normalized === 'level_2' || normalized === 'orange') return 'Orange';
    if (normalized === 'level_3' || normalized === 'red') return 'Red';
    return titleCase(normalized || 'unknown');
  }

  function levelBadgeClass(level: string | null | undefined) {
    const normalized = String(level ?? '').toLowerCase();
    if (normalized === 'level_3' || normalized === 'red') return 'badge-down';
    if (normalized === 'level_2' || normalized === 'orange')
      return 'inline-flex items-center gap-1 rounded-sm bg-orange-400/10 px-2 py-0.5 text-xs font-semibold text-orange-400';
    return 'badge-primary';
  }

  function penaltyTypeClass(type: string | null | undefined) {
    const normalized = String(type ?? '').toLowerCase();
    if (normalized === 'points') return 'badge-info';
    if (normalized === 'monetary') return 'badge-primary';
    if (normalized === 'suspension') return 'badge-down';
    return 'badge-muted';
  }

  function amountLabel(penalty: Penalty) {
    if (penalty.penalty_type === 'monetary' && penalty.amount !== undefined)
      return `INR ${number(penalty.amount)}`;
    return number(penalty.amount ?? penalty.points ?? 0);
  }

  function warningStudent(warning: Warning) {
    return warning.student_name ?? warning.student_id;
  }

  function penaltyStudent(penalty: Penalty) {
    return penalty.student_name ?? penalty.student_id;
  }

  function escalationStudent(escalation: Escalation) {
    return escalation.student_name ?? escalation.student_id;
  }

  function parseDateRange(value: unknown): DateRange {
    if (!value || typeof value !== 'object') return { start: null, end: null };
    const range = value as { start?: unknown; end?: unknown };
    return {
      start: range.start ? String(range.start) : null,
      end: range.end ? String(range.end) : null
    };
  }

  function applyFilters(values: Record<string, unknown>) {
    filters = {
      search: String(values.search ?? ''),
      level: String(values.level ?? ''),
      rule_id: String(values.rule_id ?? ''),
      penalty_type: String(values.penalty_type ?? ''),
      status: String(values.status ?? ''),
      date: parseDateRange(values.date)
    };
    page = 1;
    selected = new Set();
    loadWarnings();
  }

  function resetFilters() {
    filters = defaultFilters();
    page = 1;
    selected = new Set();
    loadWarnings();
  }

  function setTab(tab: string) {
    activeTab = tab as WarningsTab;
    page = 1;
    selected = new Set();
    error = '';
    loadWarnings();
  }

  function sortTable(key: string, direction: 'asc' | 'desc') {
    sort = key;
    order = direction;
    page = 1;
    loadWarnings();
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadWarnings();
  }

  function toggleWarningSelection(id: string) {
    selected = new Set(selected);
    if (selected.has(id)) selected.delete(id);
    else selected.add(id);
  }

  function toggleVisibleSelection() {
    selected = new Set(selected);
    if (visibleSelected) {
      visibleWarnings.forEach((warning) => selected.delete(warning.id));
    } else {
      visibleWarnings.forEach((warning) => selected.add(warning.id));
    }
  }

  async function loadReferenceData() {
    try {
      const data = await api.get<
        | Paginated<{ id: string; name: string }>
        | Array<{
            id: string;
            name: string;
          }>
      >('/rules', { size: 100 });
      ruleOptions = [
        { value: '', label: 'All rules' },
        ...itemsOf(data).map((rule) => ({ value: rule.id, label: rule.name }))
      ];
    } catch {
      ruleOptions = [{ value: '', label: 'All rules' }];
    }
  }

  async function loadStats() {
    try {
      normalizeStats(await api.get<WarningStats>('/warnings/stats'));
    } catch {
      normalizeStats({
        active_warnings: activeTab === 'active' ? warnings.total : undefined,
        resolved_today: activeTab === 'resolved' ? warnings.total : undefined,
        active_penalties: penalties.total,
        pending_escalations: escalations.total
      });
    }
  }

  async function loadWarnings() {
    loading = true;
    error = '';
    try {
      if (activeTab === 'penalties') {
        penalties = asPage(
          await api.get<Paginated<Penalty> | Penalty[]>(
            '/penalties',
            penaltyQuery()
          )
        );
      } else if (activeTab === 'escalations') {
        escalations = asPage(
          await api.get<Paginated<Escalation> | Escalation[]>(
            '/escalations',
            escalationQuery()
          )
        );
      } else {
        warnings = asPage(
          await api.get<Paginated<Warning> | Warning[]>(
            '/warnings',
            warningQuery()
          )
        );
        selected = new Set(
          Array.from(selected).filter((id) =>
            warnings.items.some((warning) => warning.id === id)
          )
        );
      }
      await loadStats();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load warnings';
    } finally {
      loading = false;
    }
  }

  function resetStudentPicker() {
    studentSearch = '';
    studentOptions = [];
    studentSearching = false;
  }

  function openManualWarning() {
    warningForm = defaultWarningForm();
    studentPickerMode = 'warning';
    resetStudentPicker();
    manualWarnOpen = true;
  }

  function openDirectPenalty() {
    penaltyForm = defaultPenaltyForm();
    studentPickerMode = 'penalty';
    resetStudentPicker();
    directPenaltyOpen = true;
  }

  function studentLabel(student: Student) {
    const name = student.mapping?.name ?? student.device_id;
    const roll = student.mapping?.roll_number ?? student.device_id;
    return `${name} (${roll})`;
  }

  function studentMeta(student: Student) {
    return [student.mapping?.branch, student.mapping?.hostel, student.status]
      .filter(Boolean)
      .join(' / ');
  }

  async function searchStudents(value: string) {
    studentSearch = value;
    if (value.trim().length < 2) {
      studentOptions = [];
      return;
    }
    studentSearching = true;
    try {
      const data = await api.get<Paginated<Student> | Student[]>('/students/', {
        search: value,
        size: 8
      });
      studentOptions = itemsOf(data).map((student) => ({
        id: student.id,
        label: studentLabel(student),
        meta: studentMeta(student)
      }));
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not search students.',
        'error'
      );
    } finally {
      studentSearching = false;
    }
  }

  function selectStudent(option: StudentOption) {
    if (studentPickerMode === 'warning') {
      warningForm = {
        ...warningForm,
        student_id: option.id,
        student_label: option.label
      };
    } else {
      penaltyForm = {
        ...penaltyForm,
        student_id: option.id,
        student_label: option.label
      };
    }
    studentSearch = option.label;
    studentOptions = [];
  }

  function foodItems() {
    return warningForm.food_items
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function submitManualWarning() {
    if (!warningForm.student_id) {
      notify('Select a student first.', 'warning');
      return;
    }
    try {
      await api.post(`/students/${warningForm.student_id}/warnings`, {
        level: warningForm.level,
        reason: warningForm.reason,
        send_email: warningForm.send_email,
        food_items: foodItems()
      });
      notify('Warning created.', 'success');
      manualWarnOpen = false;
      warningForm = defaultWarningForm();
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not create warning.',
        'error'
      );
    }
  }

  async function submitDirectPenalty() {
    if (!penaltyForm.student_id) {
      notify('Select a student first.', 'warning');
      return;
    }
    try {
      await api.post(`/students/${penaltyForm.student_id}/penalties`, {
        points: penaltyForm.amount ? Number(penaltyForm.amount) : 1,
        reason: penaltyForm.reason
      });
      notify('Penalty created.', 'success');
      directPenaltyOpen = false;
      penaltyForm = defaultPenaltyForm();
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not create penalty.',
        'error'
      );
    }
  }

  async function submitResolve() {
    if (!resolveTarget) return;
    try {
      await api.patch(`/warnings/${resolveTarget.id}/resolve`, {
        resolution_note: resolveNote
      });
      notify('Warning resolved.', 'success');
      resolveTarget = null;
      resolveNote = '';
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not resolve warning.',
        'error'
      );
    }
  }

  async function submitEscalation() {
    if (!escalateTarget) return;
    try {
      await api.post(`/warnings/${escalateTarget.id}/escalate`, {
        escalated_to_role: escalationRole,
        reason: escalationReason
      });
      notify('Warning escalated.', 'success');
      escalateTarget = null;
      escalationReason = '';
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not escalate warning.',
        'error'
      );
    }
  }

  function openBulkResolve() {
    if (selected.size === 0) {
      notify('Select at least one warning.', 'warning');
      return;
    }
    bulkResolveNote = '';
    bulkResolveOpen = true;
  }

  async function submitBulkResolve() {
    const warning_ids = Array.from(selected);
    if (warning_ids.length === 0) return;
    try {
      await api.patch('/warnings/bulk/resolve', {
        warning_ids,
        resolution_note: bulkResolveNote
      });
      notify('Selected warnings resolved.', 'success');
      bulkResolveOpen = false;
      selected = new Set();
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Bulk resolve failed.',
        'error'
      );
    }
  }

  async function submitRevokePenalty() {
    if (!revokeTarget) return;
    try {
      await api.patch(`/penalties/${revokeTarget.id}/revoke`, {
        reason: revokeReason
      });
      notify('Penalty revoked.', 'success');
      revokeTarget = null;
      revokeReason = '';
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not revoke penalty.',
        'error'
      );
    }
  }

  async function submitEscalationReview() {
    if (!reviewTarget) return;
    try {
      await api.post(`/escalations/${reviewTarget.id}/review`, {
        decision: reviewResolution,
        review_note: reviewNote
      });
      notify('Escalation reviewed.', 'success');
      reviewTarget = null;
      reviewNote = '';
      await loadWarnings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not review escalation.',
        'error'
      );
    }
  }

  async function submitExport() {
    try {
      await api.download(
        '/warnings/export',
        `warnings.${exportFormat === 'excel' ? 'xlsx' : 'csv'}`,
        exportQuery()
      );
      exportOpen = false;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export warnings.',
        'error'
      );
    }
  }

  onMount(async () => {
    await Promise.all([loadReferenceData(), loadWarnings()]);
  });
</script>

<svelte:head>
  <title>Warnings | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Warnings and penalties"
  title="Enforcement management"
  description="Review warning cases, resolve active issues, apply direct penalties, and handle escalation queues."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={loadWarnings}
      id="btn-refresh-warnings"
    >
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button
      variant="secondary"
      on:click={openDirectPenalty}
      id="btn-direct-penalty"
    >
      <Plus size={16} />
      Direct penalty
    </Button>
    <Button on:click={openManualWarning} id="btn-manual-warn">
      <Plus size={16} />
      Manual warn
    </Button>
    <Button
      variant="secondary"
      on:click={() => (exportOpen = true)}
      id="btn-export-warnings"
    >
      <Download size={16} />
      Export
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Active Warnings"
    value={number(
      stats.active_warnings ?? (activeTab === 'active' ? warnings.total : 0)
    )}
    helper="Open cases"
    tone="warn"
  >
    <svelte:fragment slot="icon"><ShieldAlert size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Resolved Today"
    value={number(
      stats.resolved_today ?? (activeTab === 'resolved' ? warnings.total : 0)
    )}
    helper="Closed warning cases"
    tone="good"
  >
    <svelte:fragment slot="icon"><CheckCircle2 size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Escalated"
    value={number(
      stats.escalated ?? stats.pending_escalations ?? escalations.total
    )}
    helper="Needs review"
    tone="bad"
  >
    <svelte:fragment slot="icon"><ArrowUpCircle size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Active Penalties"
    value={number(
      stats.active_penalties ?? stats.total_penalties ?? penalties.total
    )}
    helper="Penalty records"
    tone="bad"
  >
    <svelte:fragment slot="icon"><AlertTriangle size={19} /></svelte:fragment>
  </StatCard>
</div>

<div class="mt-5">
  <Tabs {tabs} active={activeTab} onChange={setTab} />
</div>

<div class="mt-5">
  <FilterBar
    filters={currentFilterConfig}
    values={filterRecord}
    onFilter={applyFilters}
    onReset={resetFilters}
  />
</div>

{#if error}
  <div
    class="mt-5 rounded-md border border-down/30 bg-down/10 p-4 text-sm text-down"
  >
    {error}
  </div>
{:else if activeTab === 'active' || activeTab === 'resolved'}
  <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
    <div class="flex flex-wrap gap-2">
      <Button
        variant="secondary"
        size="sm"
        on:click={toggleVisibleSelection}
        disabled={visibleWarnings.length === 0}
        id="btn-select-visible-warnings"
      >
        {visibleSelected ? 'Clear visible' : 'Select visible'}
      </Button>
      <Button
        variant="secondary"
        size="sm"
        on:click={openBulkResolve}
        disabled={selectedCount === 0 || activeTab !== 'active'}
        id="btn-bulk-resolve"
      >
        Resolve selected
      </Button>
    </div>
    <select
      class="select-field w-28"
      bind:value={size}
      on:change={() => {
        page = 1;
        loadWarnings();
      }}
      id="select-warnings-page-size"
    >
      <option value={10}>10</option>
      <option value={25}>25</option>
      <option value={50}>50</option>
      <option value={100}>100</option>
    </select>
  </div>

  <div class="mt-4">
    <DataTable
      columns={warningColumns}
      rows={warningRows}
      {loading}
      {page}
      total={filters.search ? warningRows.length : warnings.total}
      pageSize={size}
      sortKey={sort}
      sortDirection={order}
      onSort={sortTable}
      onPageChange={goToPage}
      onRowClick={(row) => (detailWarning = warningOf(row))}
    >
      <svelte:fragment slot="cell" let:row let:column let:value>
        {@const warning = warningOf(row)}
        {#if column.key === 'select'}
          <input
            type="checkbox"
            checked={selected.has(warning.id)}
            on:click|stopPropagation
            on:change={() => toggleWarningSelection(warning.id)}
            aria-label={`Select warning ${warning.id}`}
            disabled={activeTab !== 'active'}
          />
        {:else if column.key === 'student'}
          <div>
            <a
              class="font-semibold text-primary"
              href={`/dashboard/students/${warning.student_id}`}
              on:click|stopPropagation
            >
              {warningStudent(warning)}
            </a>
            <p class="mt-1 text-xs text-muted">
              {warning.student_roll_number ??
                warning.student_roll ??
                warning.student_id}
            </p>
          </div>
        {:else if column.key === 'level'}
          <span class={levelBadgeClass(warning.level)}
            >{levelLabel(warning.level)}</span
          >
        {:else if column.key === 'reason'}
          <span class="line-clamp-2">{warning.reason}</span>
        {:else if column.key === 'rule_name'}
          {warning.rule_name ?? '-'}
        {:else if column.key === 'status'}
          <StatusBadge value={warning.status} compact />
        {:else if column.key === 'created_at'}
          {dateTime(warning.created_at)}
        {:else}
          {value ?? '-'}
        {/if}
      </svelte:fragment>

      <svelte:fragment slot="row-actions" let:row>
        {@const warning = warningOf(row)}
        <div class="flex flex-wrap justify-end gap-2">
          <Button
            size="sm"
            variant="secondary"
            on:click={() => (detailWarning = warning)}
            id={`btn-view-warning-${warning.id}`}
          >
            <Eye size={14} />
            View
          </Button>
          <Button
            size="sm"
            variant="secondary"
            on:click={() => {
              resolveTarget = warning;
              resolveNote = '';
            }}
            disabled={warning.status !== 'active'}
            id={`btn-resolve-warning-${warning.id}`}
          >
            Resolve
          </Button>
          <Button
            size="sm"
            variant="secondary"
            on:click={() => {
              escalateTarget = warning;
              escalationReason = '';
            }}
            disabled={warning.status !== 'active'}
            id={`btn-escalate-warning-${warning.id}`}
          >
            Escalate
          </Button>
        </div>
      </svelte:fragment>

      <svelte:fragment slot="empty">
        <EmptyState
          title="No warnings"
          message="Adjust filters or create a manual warning for the selected student."
        />
      </svelte:fragment>
    </DataTable>
  </div>
{:else if activeTab === 'penalties'}
  <div class="mt-5">
    <DataTable
      columns={penaltyColumns}
      rows={penaltyRows}
      {loading}
      {page}
      total={filters.search ? penaltyRows.length : penalties.total}
      pageSize={size}
      sortKey={sort}
      sortDirection={order}
      onSort={sortTable}
      onPageChange={goToPage}
    >
      <svelte:fragment slot="cell" let:row let:column let:value>
        {@const penalty = penaltyOf(row)}
        {#if column.key === 'student'}
          <a
            class="font-semibold text-primary"
            href={`/dashboard/students/${penalty.student_id}`}
          >
            {penaltyStudent(penalty)}
          </a>
        {:else if column.key === 'points'}
          <span>
            {penalty.points ?? penalty.amount ?? 0}
          </span>
        {:else if column.key === 'warning_id'}
          {penalty.warning_id ?? 'Direct'}
        {:else if column.key === 'status'}
          <StatusBadge value={penalty.status} compact />
        {:else if column.key === 'created_at'}
          {dateTime(penalty.created_at)}
        {:else}
          {value ?? '-'}
        {/if}
      </svelte:fragment>

      <svelte:fragment slot="row-actions" let:row>
        {@const penalty = penaltyOf(row)}
        <Button
          size="sm"
          variant="secondary"
          on:click={() => {
            revokeTarget = penalty;
            revokeReason = '';
          }}
          disabled={penalty.status === 'revoked'}
          id={`btn-revoke-penalty-${penalty.id}`}
        >
          Revoke
        </Button>
      </svelte:fragment>

      <svelte:fragment slot="empty">
        <EmptyState
          title="No penalties"
          message="Direct penalties and warning-linked penalties appear here."
        />
      </svelte:fragment>
    </DataTable>
  </div>
{:else}
  <div class="mt-5">
    <DataTable
      columns={escalationColumns}
      rows={escalationRows}
      {loading}
      {page}
      total={filters.search ? escalationRows.length : escalations.total}
      pageSize={size}
      sortKey={sort}
      sortDirection={order}
      onSort={sortTable}
      onPageChange={goToPage}
    >
      <svelte:fragment slot="cell" let:row let:column let:value>
        {@const escalation = escalationOf(row)}
        {#if column.key === 'student'}
          <a
            class="font-semibold text-primary"
            href={`/dashboard/students/${escalation.student_id}`}
          >
            {escalationStudent(escalation)}
          </a>
        {:else if column.key === 'level'}
          <span class={levelBadgeClass(escalation.level)}
            >{levelLabel(escalation.level)}</span
          >
        {:else if column.key === 'escalated_to'}
          {titleCase(
            escalation.escalated_to ??
              escalation.escalated_to_role ??
              'institution_admin'
          )}
        {:else if column.key === 'note'}
          <span class="line-clamp-2"
            >{escalation.note ?? escalation.reason ?? '-'}</span
          >
        {:else if column.key === 'status'}
          <StatusBadge value={escalation.status} compact />
        {:else if column.key === 'created_at'}
          {dateTime(escalation.created_at)}
        {:else}
          {value ?? '-'}
        {/if}
      </svelte:fragment>

      <svelte:fragment slot="row-actions" let:row>
        {@const escalation = escalationOf(row)}
        <Button
          size="sm"
          variant="secondary"
          on:click={() => {
            reviewTarget = escalation;
            reviewResolution = 'resolved';
            reviewNote = '';
          }}
          disabled={escalation.status !== 'pending'}
          id={`btn-review-escalation-${escalation.id}`}
        >
          Review
        </Button>
      </svelte:fragment>

      <svelte:fragment slot="empty">
        <EmptyState
          title="No escalations"
          message="Escalated warnings waiting on review appear here."
        />
      </svelte:fragment>
    </DataTable>
  </div>
{/if}

<Modal
  open={manualWarnOpen}
  title="Create manual warning"
  description="Submit through the student warning endpoint."
  on:close={() => (manualWarnOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={submitManualWarning}>
    <FormField
      label="Student"
      required
      hint={warningForm.student_label ||
        'Search by name, roll number, or device ID.'}
    >
      <SearchInput
        value={studentSearch}
        placeholder="Search students"
        onSearch={searchStudents}
        onClear={resetStudentPicker}
        id="input-manual-warning-student"
      />
      {#if studentSearching}
        <p class="mt-2 text-xs text-muted">Searching...</p>
      {:else if studentOptions.length}
        <div
          class="mt-2 max-h-48 overflow-auto rounded-md border border-border bg-elevated"
        >
          {#each studentOptions as option}
            <button
              class="block w-full px-3 py-2 text-left text-sm text-body transition-colors hover:bg-card"
              type="button"
              on:click={() => selectStudent(option)}
            >
              <span class="font-semibold">{option.label}</span>
              {#if option.meta}
                <span class="mt-1 block text-xs text-muted">{option.meta}</span>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </FormField>

    <div class="grid gap-3 sm:grid-cols-2">
      <FormField label="Level" required>
        <select class="select-field" bind:value={warningForm.level} required>
          <option value="level_1">Yellow</option>
          <option value="level_2">Orange</option>
          <option value="level_3">Red</option>
        </select>
      </FormField>
      <FormField label="Food items">
        <input
          class="input-field"
          bind:value={warningForm.food_items}
          placeholder="Rice, curry"
        />
      </FormField>
    </div>

    <FormField label="Reason" required>
      <textarea
        class="textarea-field"
        bind:value={warningForm.reason}
        required
        placeholder="Describe the waste pattern or incident"
      ></textarea>
    </FormField>

    <label class="inline-flex items-center gap-2 text-sm text-body">
      <input type="checkbox" bind:checked={warningForm.send_email} />
      Send email notification
    </label>

    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (manualWarnOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-manual-warning"
        >Create warning</Button
      >
    </div>
  </form>
</Modal>

<Modal
  open={directPenaltyOpen}
  title="Create direct penalty"
  description="Submit through the student penalty endpoint."
  on:close={() => (directPenaltyOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={submitDirectPenalty}>
    <FormField
      label="Student"
      required
      hint={penaltyForm.student_label ||
        'Search by name, roll number, or device ID.'}
    >
      <SearchInput
        value={studentSearch}
        placeholder="Search students"
        onSearch={searchStudents}
        onClear={resetStudentPicker}
        id="input-direct-penalty-student"
      />
      {#if studentSearching}
        <p class="mt-2 text-xs text-muted">Searching...</p>
      {:else if studentOptions.length}
        <div
          class="mt-2 max-h-48 overflow-auto rounded-md border border-border bg-elevated"
        >
          {#each studentOptions as option}
            <button
              class="block w-full px-3 py-2 text-left text-sm text-body transition-colors hover:bg-card"
              type="button"
              on:click={() => selectStudent(option)}
            >
              <span class="font-semibold">{option.label}</span>
              {#if option.meta}
                <span class="mt-1 block text-xs text-muted">{option.meta}</span>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </FormField>

    <div class="grid gap-3 sm:grid-cols-2">
      <FormField label="Points" required hint="Points must be between 1 and 100">
        <input
          class="input-field"
          type="number"
          min="1"
          max="100"
          step="1"
          bind:value={penaltyForm.amount}
          required
        />
      </FormField>
    </div>

    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={penaltyForm.reason} required
      ></textarea>
    </FormField>

    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (directPenaltyOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-direct-penalty"
        >Create penalty</Button
      >
    </div>
  </form>
</Modal>

<Modal
  open={!!detailWarning}
  title="Warning detail"
  description={detailWarning
    ? `${warningStudent(detailWarning)} / ${levelLabel(detailWarning.level)}`
    : ''}
  on:close={() => (detailWarning = null)}
>
  {#if detailWarning}
    <div class="space-y-4">
      <div class="grid gap-3 sm:grid-cols-2">
        <div class="rounded-md border border-border bg-elevated/40 p-3">
          <p class="label">Student</p>
          <p class="mt-1 font-semibold text-body">
            {warningStudent(detailWarning)}
          </p>
          <p class="mt-1 text-xs text-muted">
            {detailWarning.student_roll_number ??
              detailWarning.student_roll ??
              detailWarning.student_id}
          </p>
        </div>
        <div class="rounded-md border border-border bg-elevated/40 p-3">
          <p class="label">Status</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <span class={levelBadgeClass(detailWarning.level)}>
              {levelLabel(detailWarning.level)}
            </span>
            <StatusBadge value={detailWarning.status} compact />
          </div>
        </div>
      </div>
      <div class="rounded-md border border-border bg-elevated/40 p-3">
        <p class="label">Reason</p>
        <p class="mt-2 text-sm leading-6 text-body">{detailWarning.reason}</p>
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        <div class="rounded-md border border-border bg-elevated/40 p-3">
          <p class="label">Rule</p>
          <p class="mt-1 text-sm text-body">
            {detailWarning.rule_name ??
              detailWarning.rule_id ??
              'Manual warning'}
          </p>
        </div>
        <div class="rounded-md border border-border bg-elevated/40 p-3">
          <p class="label">Waste Entry</p>
          <p class="mt-1 text-sm text-body">
            {detailWarning.waste_entry_id ?? 'Not linked'}
          </p>
        </div>
      </div>
      <div class="rounded-md border border-border bg-elevated/40 p-3">
        <p class="label">Timeline</p>
        <div class="mt-3 space-y-3 text-sm">
          <div class="flex items-center gap-3">
            <span class="dot-warn"></span>
            <span>Created {dateTime(detailWarning.created_at)}</span>
          </div>
          {#if detailWarning.status === 'escalated' || detailWarning.escalations?.length}
            <div class="flex items-center gap-3">
              <span class="dot-down"></span>
              <span>Escalated {detailWarning.escalations?.[0]?.note ?? ''}</span
              >
            </div>
          {/if}
          {#if detailWarning.resolved_at}
            <div class="flex items-center gap-3">
              <span class="dot-up"></span>
              <span>Resolved {dateTime(detailWarning.resolved_at)}</span>
            </div>
          {/if}
        </div>
      </div>
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          variant="secondary"
          on:click={() => {
            resolveTarget = detailWarning;
            resolveNote = '';
            detailWarning = null;
          }}
          disabled={detailWarning.status !== 'active'}
        >
          Resolve
        </Button>
        <Button
          type="button"
          on:click={() => {
            escalateTarget = detailWarning;
            escalationReason = '';
            detailWarning = null;
          }}
          disabled={detailWarning.status !== 'active'}
        >
          Escalate
        </Button>
      </div>
    </div>
  {/if}
</Modal>

<Modal
  open={!!resolveTarget}
  title="Resolve warning"
  description={resolveTarget?.reason ?? ''}
  on:close={() => (resolveTarget = null)}
>
  <form class="space-y-4" on:submit|preventDefault={submitResolve}>
    <FormField label="Resolution note" required>
      <textarea class="textarea-field" bind:value={resolveNote} required
      ></textarea>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (resolveTarget = null)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-resolve-warning">Resolve</Button>
    </div>
  </form>
</Modal>

<Modal
  open={!!escalateTarget}
  title="Escalate warning"
  description={escalateTarget?.reason ?? ''}
  on:close={() => (escalateTarget = null)}
>
  <form class="space-y-4" on:submit|preventDefault={submitEscalation}>
    <FormField label="Escalate to" required>
      <select class="select-field" bind:value={escalationRole} required>
        <option value="institution_admin">Institution admin</option>
        <option value="super_admin">Super admin</option>
        <option value="mess_admin">Mess admin</option>
      </select>
    </FormField>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={escalationReason} required
      ></textarea>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (escalateTarget = null)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-escalate-warning">Escalate</Button>
    </div>
  </form>
</Modal>

<Modal
  open={bulkResolveOpen}
  title="Resolve selected warnings"
  description={`${selectedCount} warning${selectedCount === 1 ? '' : 's'} selected`}
  on:close={() => (bulkResolveOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={submitBulkResolve}>
    <FormField label="Resolution note" required>
      <textarea class="textarea-field" bind:value={bulkResolveNote} required
      ></textarea>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (bulkResolveOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-bulk-resolve"
        >Resolve selected</Button
      >
    </div>
  </form>
</Modal>

<Modal
  open={exportOpen}
  title="Export warnings"
  description="Exports use the active warning filters."
  on:close={() => (exportOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={submitExport}>
    <FormField label="Format" required>
      <select class="select-field" bind:value={exportFormat} required>
        <option value="csv">CSV</option>
        <option value="excel">Excel</option>
      </select>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (exportOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-export-warnings">Export</Button>
    </div>
  </form>
</Modal>

<Modal
  open={!!revokeTarget}
  title="Revoke penalty"
  description={revokeTarget?.reason ?? ''}
  on:close={() => (revokeTarget = null)}
>
  <form class="space-y-4" on:submit|preventDefault={submitRevokePenalty}>
    <FormField label="Reason" required>
      <textarea class="textarea-field" bind:value={revokeReason} required
      ></textarea>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (revokeTarget = null)}
      >
        Cancel
      </Button>
      <Button type="submit" variant="danger" id="btn-submit-revoke-penalty"
        >Revoke</Button
      >
    </div>
  </form>
</Modal>

<Modal
  open={!!reviewTarget}
  title="Review escalation"
  description={reviewTarget?.warning_id ?? ''}
  on:close={() => (reviewTarget = null)}
>
  <form class="space-y-4" on:submit|preventDefault={submitEscalationReview}>
    <FormField label="Decision" required>
      <select class="select-field" bind:value={reviewResolution} required>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
      </select>
    </FormField>
    <FormField label="Review note">
      <textarea class="textarea-field" bind:value={reviewNote}></textarea>
    </FormField>
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (reviewTarget = null)}
      >
        Cancel
      </Button>
      <Button type="submit" id="btn-submit-review-escalation"
        >Submit review</Button
      >
    </div>
  </form>
</Modal>
