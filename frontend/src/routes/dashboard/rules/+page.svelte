<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Copy,
    Edit3,
    FlaskConical,
    GitBranch,
    History,
    Play,
    Plus,
    RefreshCw,
    Trash2
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated } from '$lib/api/types';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';
  import DataTable, {
    type TableColumn
  } from '$lib/components/ui/DataTable.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FilterBar, {
    type FilterConfig
  } from '$lib/components/ui/FilterBar.svelte';
  import FormField from '$lib/components/ui/FormField.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs, { type TabItem } from '$lib/components/ui/Tabs.svelte';
  import Toggle from '$lib/components/ui/Toggle.svelte';
  import { dateTime, itemsOf, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type RulesTab = 'rules' | 'executions' | 'chains';
  type Logic = 'AND' | 'OR';
  type Rule = {
    id: string;
    name: string;
    description?: string | null;
    type: string;
    priority: string;
    active: boolean;
    conditions: ConditionGroup[];
    time_constraints?: TimeConstraint | null;
    scope?: RuleScope | null;
    actions: RuleAction[];
    execution_count?: number | null;
    triggered_today_count?: number | null;
    last_triggered_at?: string | null;
    chain_to_rule_id?: string | null;
    created_by?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
  };
  type ConditionGroup = {
    logic: Logic;
    conditions: Condition[];
  };
  type Condition = {
    field: string;
    operator: string;
    value: unknown;
    value_max?: unknown;
  };
  type TimeConstraint = {
    window?: string;
    lookback_days?: number;
  };
  type RuleScope = {
    target?: string;
    branch?: string;
    mess_id?: string;
    filters?: Record<string, unknown>;
  };
  type RuleAction = {
    type: string;
    params: Record<string, unknown>;
  };
  type RuleExecution = {
    id: string;
    rule_id: string;
    rule_name?: string;
    trigger_source?: string;
    trigger_event_type?: string;
    matched_conditions?: unknown;
    executed_actions?: unknown;
    result_status: string;
    executed_at: string;
  };
  type ConditionMetadata = {
    key: string;
    label: string;
    type: string;
    options?: string[];
    operators: string[];
  };
  type ActionMetadata = {
    type: string;
    label: string;
    params?: Record<string, ParamDefinitionInput>;
    required_params?: string[];
    optional_params?: string[];
  };
  type ParamDefinitionInput = {
    type?: string;
    required?: boolean;
    options?: string[];
  };
  type ParamDefinition = {
    key: string;
    label: string;
    type: string;
    required: boolean;
    options?: string[];
  };
  type BuilderCondition = {
    field: string;
    operator: string;
    value: string;
    value_max: string;
  };
  type BuilderAction = {
    type: string;
    params: Record<string, string | boolean>;
  };
  type RuleBuilderState = {
    id: string;
    name: string;
    description: string;
    type: string;
    priority: string;
    active: boolean;
    conditionLogic: Logic;
    conditions: BuilderCondition[];
    timeWindow: string;
    timeLookbackDays: string;
    scopeTarget: string;
    branch: string;
    actions: BuilderAction[];
    chain_to_rule_id: string;
  };
  type ChainNode = {
    id: string;
    name: string;
    priority?: string | null;
  };
  type ChainEdge = {
    from_rule_id?: string;
    to_rule_id?: string;
    from?: string;
    to?: string;
  };
  type ChainData = {
    nodes?: ChainNode[];
    edges?: ChainEdge[];
    chains?: Array<Record<string, unknown>>;
  };

  const defaultConditions: ConditionMetadata[] = [
    {
      key: 'waste_grams',
      label: 'Waste grams',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte', 'between']
    },
    {
      key: 'meal_type',
      label: 'Meal type',
      type: 'enum',
      options: ['breakfast', 'lunch', 'dinner', 'other'],
      operators: ['eq', 'neq', 'in', 'not_in']
    },
    {
      key: 'severity',
      label: 'Severity',
      type: 'enum',
      options: ['normal', 'warning', 'high'],
      operators: ['eq', 'neq', 'in', 'not_in']
    },
    {
      key: 'food_item',
      label: 'Food item',
      type: 'string',
      operators: ['eq', 'in', 'contains']
    },
    {
      key: 'student_branch',
      label: 'Student branch',
      type: 'string',
      operators: ['eq', 'neq', 'in', 'not_in']
    },
    {
      key: 'student_year',
      label: 'Student year',
      type: 'number',
      operators: ['eq', 'neq', 'in', 'between']
    },
    {
      key: 'warning_count',
      label: 'Warning count',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte', 'eq']
    },
    {
      key: 'penalty_count',
      label: 'Penalty count',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte', 'eq']
    },
    {
      key: 'sustainability_score',
      label: 'Sustainability score',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte', 'between']
    },
    {
      key: 'frequency_count',
      label: 'Frequency count',
      type: 'number',
      operators: ['gt', 'gte', 'eq']
    },
    {
      key: 'avg_waste_7d',
      label: 'Average waste 7d',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte']
    },
    {
      key: 'avg_waste_30d',
      label: 'Average waste 30d',
      type: 'number',
      operators: ['gt', 'gte', 'lt', 'lte']
    }
  ];
  const defaultActions: ActionMetadata[] = [
    {
      type: 'generate_warning',
      label: 'Generate warning',
      params: {
        level: {
          type: 'enum',
          required: true,
          options: ['level_1', 'level_2', 'level_3']
        },
        reason: { type: 'string', required: true },
        send_email: { type: 'boolean', required: false }
      }
    },
    {
      type: 'send_email',
      label: 'Send email',
      params: {
        template_id: { type: 'string', required: false },
        subject: { type: 'string', required: false },
        body: { type: 'string', required: false },
        recipient_override: { type: 'string', required: false }
      }
    },
    {
      type: 'increase_penalty',
      label: 'Increase penalty',
      params: {
        points: { type: 'number', required: true },
        reason: { type: 'string', required: false },
        send_email: { type: 'boolean', required: false }
      }
    },
    {
      type: 'trigger_escalation',
      label: 'Trigger escalation',
      params: {
        escalated_to_role: {
          type: 'enum',
          required: true,
          options: ['institution_admin', 'super_admin', 'mess_admin']
        },
        reason: { type: 'string', required: true }
      }
    },
    {
      type: 'classify_student',
      label: 'Classify student',
      params: {
        status: {
          type: 'enum',
          required: true,
          options: ['green', 'yellow', 'orange', 'red']
        }
      }
    },
    {
      type: 'create_audit_log',
      label: 'Create audit log',
      params: {
        summary: { type: 'string', required: true },
        metadata: { type: 'string', required: false }
      }
    }
  ];
  const tabs: TabItem[] = [
    { id: 'rules', label: 'Rule List', icon: FlaskConical },
    { id: 'executions', label: 'Execution History', icon: History },
    { id: 'chains', label: 'Rule Chains', icon: GitBranch }
  ];
  const ruleFilters: FilterConfig[] = [
    {
      key: 'search',
      label: 'Search',
      type: 'text',
      placeholder: 'Rule name'
    },
    {
      key: 'type',
      label: 'Type',
      type: 'select',
      options: [
        { value: '', label: 'All types' },
        { value: 'threshold', label: 'Threshold' },
        { value: 'frequency', label: 'Frequency' },
        { value: 'trend', label: 'Trend' },
        { value: 'composite', label: 'Composite' }
      ]
    },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      options: [
        { value: '', label: 'All priorities' },
        { value: 'critical', label: 'Critical' },
        { value: 'high', label: 'High' },
        { value: 'medium', label: 'Medium' },
        { value: 'low', label: 'Low' }
      ]
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: '', label: 'All statuses' },
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' }
      ]
    }
  ];
  const ruleColumns: TableColumn[] = [
    { key: 'name', label: 'Name', sortable: true, width: '220px' },
    { key: 'type', label: 'Type', width: '110px' },
    { key: 'priority', label: 'Priority', sortable: true, width: '110px' },
    { key: 'active', label: 'Active', width: '90px', align: 'center' },
    {
      key: 'triggered_today_count',
      label: 'Triggered Today',
      sortable: true,
      align: 'right'
    },
    {
      key: 'execution_count',
      label: 'Total Executions',
      sortable: true,
      align: 'right'
    },
    {
      key: 'last_triggered_at',
      label: 'Last Triggered',
      sortable: true,
      width: '150px'
    }
  ];
  const executionColumns: TableColumn[] = [
    { key: 'rule_name', label: 'Rule Name' },
    { key: 'trigger_source', label: 'Trigger Event' },
    { key: 'executed_at', label: 'Triggered At', width: '160px' },
    { key: 'matched_conditions', label: 'Conditions Matched' },
    { key: 'executed_actions', label: 'Actions Executed' },
    { key: 'result_status', label: 'Result', width: '110px' }
  ];

  let activeTab: RulesTab = 'rules';
  let loading = true;
  let metadataError = '';
  let error = '';
  let page = 1;
  let size = 25;
  let sort = 'name';
  let order: 'asc' | 'desc' = 'asc';
  let filters = defaultFilters();
  let rules: Paginated<Rule> = emptyPage<Rule>();
  let conditionsMetadata: ConditionMetadata[] = defaultConditions;
  let actionsMetadata: ActionMetadata[] = defaultActions;
  let chainData: ChainData = { nodes: [], edges: [], chains: [] };

  let builderOpen = false;
  let builder = defaultBuilder();
  let builderErrors: Record<string, string> = {};
  let builderSubmitError = '';
  let pendingToggle: { rule: Rule; active: boolean } | null = null;
  let deleteTarget: Rule | null = null;

  let testOpen = false;
  let testTarget: Rule | null = null;
  let testForm = {
    sample_data: JSON.stringify(
      {
        waste_grams: 180,
        meal_type: 'lunch',
        severity: 'warning',
        frequency_count: 2,
        warning_count: 1
      },
      null,
      2
    )
  };
  let testResult: unknown = null;

  let simulationOpen = false;
  let simulationTarget: Rule | null = null;
  let simulationDates = {
    date_from: isoDaysAgo(7),
    date_to: todayIso()
  };
  let simulationResult: Record<string, unknown> | null = null;

  let executionPage = 1;
  let executionSize = 25;
  let executionLoading = false;
  let selectedExecutionRuleId = '';
  let executions: Paginated<RuleExecution> = emptyPage<RuleExecution>();

  $: filterRecord = filters as unknown as Record<string, unknown>;
  $: ruleRows = rules.items as unknown as Record<string, unknown>[];
  $: executionRows = executions.items as unknown as Record<string, unknown>[];
  $: activeRules = rules.items.filter((rule) => rule.active).length;
  $: triggeredToday = rules.items.reduce(
    (total, rule) => total + Number(rule.triggered_today_count ?? 0),
    0
  );
  $: chainedRules =
    chainData.nodes?.length ??
    rules.items.filter((rule) => Boolean(rule.chain_to_rule_id)).length;
  $: conditionOptions = conditionsMetadata.length
    ? conditionsMetadata
    : defaultConditions;
  $: actionOptions = actionsMetadata.length ? actionsMetadata : defaultActions;

  function emptyPage<T>(pageNumber = 1, pageSize = 25): Paginated<T> {
    return { items: [], total: 0, page: pageNumber, size: pageSize, pages: 1 };
  }

  function defaultFilters() {
    return { search: '', type: '', priority: '', status: '' };
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function isoDaysAgo(days: number) {
    const date = new Date();
    date.setDate(date.getDate() - Math.max(days - 1, 0));
    return date.toISOString().slice(0, 10);
  }

  function defaultBuilder(): RuleBuilderState {
    return {
      id: '',
      name: '',
      description: '',
      type: 'threshold',
      priority: 'medium',
      active: true,
      conditionLogic: 'AND',
      conditions: [defaultBuilderCondition()],
      timeWindow: 'daily',
      timeLookbackDays: '',
      scopeTarget: 'student',
      branch: '',
      actions: [defaultBuilderAction('generate_warning')],
      chain_to_rule_id: ''
    };
  }

  function defaultBuilderCondition(): BuilderCondition {
    const first = availableConditions()[0] ?? defaultConditions[0];
    return {
      field: first.key,
      operator: first.operators[0],
      value: first.type === 'number' ? '100' : (first.options?.[0] ?? ''),
      value_max: ''
    };
  }

  function defaultBuilderAction(type: string): BuilderAction {
    const params: Record<string, string | boolean> = {};
    for (const param of actionParamDefinitions(type)) {
      if (param.type === 'boolean') params[param.key] = false;
      else
        params[param.key] = param.options?.[0] ?? defaultParamValue(param.key);
    }
    return { type, params };
  }

  function defaultParamValue(key: string) {
    if (key === 'reason') return 'Waste threshold exceeded';
    if (key === 'points') return '5';
    if (key === 'level') return 'level_1';
    if (key === 'status') return 'yellow';
    if (key === 'escalated_to_role') return 'institution_admin';
    if (key === 'summary') return 'Rule triggered';
    return '';
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

  function ruleOf(row: Record<string, unknown>) {
    return row as unknown as Rule;
  }

  function executionOf(row: Record<string, unknown>) {
    return row as unknown as RuleExecution;
  }

  function ruleQuery() {
    return {
      page,
      size,
      search: filters.search,
      type: filters.type,
      priority: filters.priority,
      status: filters.status,
      sort,
      order
    };
  }

  function inputValue(event: Event) {
    return (event.currentTarget as HTMLInputElement | HTMLSelectElement).value;
  }

  function checkedValue(event: Event) {
    return (event.currentTarget as HTMLInputElement).checked;
  }

  function normalizeConditions(payload: unknown): ConditionMetadata[] {
    const source = Array.isArray(payload)
      ? payload
      : Array.isArray((payload as { conditions?: unknown[] })?.conditions)
        ? (payload as { conditions: unknown[] }).conditions
        : Array.isArray((payload as { fields?: unknown[] })?.fields)
          ? (payload as { fields: unknown[] }).fields
          : [];
    const normalized = source
      .map((item) => {
        const record = item as Record<string, unknown>;
        const key = String(record.key ?? record.field ?? record.name ?? '');
        const label = String(record.label ?? titleCase(key));
        const type = String(record.type ?? 'string');
        const options = (record.options ?? record.enum_values) as
          | string[]
          | undefined;
        const operators =
          ((record.operators ?? record.applicable_operators) as
            | string[]
            | undefined) ?? defaultOperators(type);
        if (!key) return null;
        return { key, label, type, options, operators };
      })
      .filter(Boolean) as ConditionMetadata[];
    return normalized.length ? normalized : defaultConditions;
  }

  function normalizeActions(payload: unknown): ActionMetadata[] {
    const source = Array.isArray(payload)
      ? payload
      : Array.isArray((payload as { actions?: unknown[] })?.actions)
        ? (payload as { actions: unknown[] }).actions
        : [];
    const normalized = source
      .map((item) => {
        const record = item as Record<string, unknown>;
        const type = String(record.type ?? record.key ?? '');
        const label = String(record.label ?? titleCase(type));
        if (!type) return null;
        return {
          type,
          label,
          params: record.params as
            | Record<string, ParamDefinitionInput>
            | undefined,
          required_params: record.required_params as string[] | undefined,
          optional_params: record.optional_params as string[] | undefined
        };
      })
      .filter(Boolean) as ActionMetadata[];
    return normalized.length ? normalized : defaultActions;
  }

  function defaultOperators(type: string) {
    if (type === 'number' || type === 'numeric') return ['gt', 'gte', 'lt', 'lte', 'eq', 'neq', 'between'];
    if (type === 'datetime' || type === 'time')
      return ['within_window', 'is_between'];
    return ['eq', 'neq', 'in', 'not_in', 'contains'];
  }

  function conditionMetaFor(field: string) {
    const options = availableConditions();
    return (
      options.find((condition) => condition.key === field) ??
      options[0] ??
      defaultConditions[0]
    );
  }

  function actionMetaFor(type: string) {
    const options = availableActions();
    return (
      options.find((action) => action.type === type) ??
      options[0] ??
      defaultActions[0]
    );
  }

  function availableConditions() {
    return conditionsMetadata.length ? conditionsMetadata : defaultConditions;
  }

  function availableActions() {
    return actionsMetadata.length ? actionsMetadata : defaultActions;
  }

  function actionParamDefinitions(type: string): ParamDefinition[] {
    const meta = actionMetaFor(type);
    if (meta.params) {
      return Object.entries(meta.params).map(([key, value]) => ({
        key,
        label: titleCase(key),
        type: value.type ?? 'string',
        required: Boolean(value.required),
        options: value.options
      }));
    }
    const required = meta.required_params ?? [];
    const optional = meta.optional_params ?? [];
    return [...required, ...optional].map((key) => ({
      key,
      label: titleCase(key),
      type:
        key.includes('amount') || key.includes('points') ? 'number' : 'string',
      required: required.includes(key)
    }));
  }

  function priorityClass(priority: string | null | undefined) {
    const normalized = String(priority ?? '').toLowerCase();
    if (normalized === 'critical') return 'badge-down';
    if (normalized === 'high') return 'badge-primary';
    if (normalized === 'medium') return 'badge-info';
    return 'badge-muted';
  }

  function typeClass(type: string | null | undefined) {
    const normalized = String(type ?? '').toLowerCase();
    if (normalized === 'threshold') return 'badge-info';
    if (normalized === 'frequency') return 'badge-primary';
    if (normalized === 'composite')
      return 'inline-flex items-center gap-1 rounded-sm bg-purple-400/10 px-2 py-0.5 text-xs font-semibold text-purple-300';
    return 'badge-muted';
  }

  function applyFilters(values: Record<string, unknown>) {
    filters = {
      search: String(values.search ?? ''),
      type: String(values.type ?? ''),
      priority: String(values.priority ?? ''),
      status: String(values.status ?? '')
    };
    page = 1;
    loadRules();
  }

  function resetFilters() {
    filters = defaultFilters();
    page = 1;
    loadRules();
  }

  function sortRules(key: string, direction: 'asc' | 'desc') {
    sort = key;
    order = direction;
    page = 1;
    loadRules();
  }

  function goToPage(nextPage: number) {
    page = nextPage;
    loadRules();
  }

  function setTab(tab: string) {
    activeTab = tab as RulesTab;
    if (activeTab === 'chains') loadChains();
  }

  async function loadRules() {
    loading = true;
    error = '';
    metadataError = '';
    const [rulesResult, conditionsResult, actionsResult, chainsResult] =
      await Promise.allSettled([
        api.get<Paginated<Rule> | Rule[]>('/rules', ruleQuery()),
        api.get<unknown>('/rules/metadata/fields'),
        api.get<unknown>('/rules/metadata/actions'),
        api.get<ChainData>('/rules/chains')
      ]);

    try {
      if (rulesResult.status === 'rejected') throw rulesResult.reason;
      rules = asPage(rulesResult.value);

      if (conditionsResult.status === 'fulfilled')
        conditionsMetadata = normalizeConditions(conditionsResult.value);
      else {
        conditionsMetadata = defaultConditions;
        metadataError = 'Rule condition metadata is using local defaults.';
      }

      if (actionsResult.status === 'fulfilled')
        actionsMetadata = normalizeActions(actionsResult.value);
      else {
        actionsMetadata = defaultActions;
        metadataError = 'Rule action metadata is using local defaults.';
      }

      if (chainsResult.status === 'fulfilled') chainData = chainsResult.value;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load rules';
    } finally {
      loading = false;
    }
  }

  async function loadChains() {
    try {
      chainData = await api.get<ChainData>('/rules/chains');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load rule chains.',
        'error'
      );
    }
  }

  function conditionsFromRule(rule: Rule | null): BuilderCondition[] {
    const group = rule?.conditions?.[0];
    const conditions = Array.isArray(group?.conditions) ? group.conditions : [];
    if (!conditions.length) return [defaultBuilderCondition()];
    return conditions.map((condition) => ({
      field: condition.field,
      operator: condition.operator,
      value: String(condition.value ?? ''),
      value_max: String(condition.value_max ?? '')
    }));
  }

  function actionsFromRule(rule: Rule | null): BuilderAction[] {
    if (!rule?.actions?.length)
      return [defaultBuilderAction('generate_warning')];
    return rule.actions.map((action) => {
      const params: Record<string, string | boolean> = {};
      for (const [key, value] of Object.entries(action.params ?? {})) {
        params[key] = typeof value === 'boolean' ? value : String(value ?? '');
      }
      return { type: action.type, params };
    });
  }

  function openBuilder(rule: Rule | null = null) {
    const group = rule?.conditions?.[0];
    builder = {
      id: rule?.id ?? '',
      name: rule?.name ?? '',
      description: rule?.description ?? '',
      type: rule?.type ?? 'threshold',
      priority: rule?.priority ?? 'medium',
      active: rule?.active ?? true,
      conditionLogic: group?.logic ?? 'AND',
      conditions: conditionsFromRule(rule),
      timeWindow: rule?.time_constraints?.window ?? 'daily',
      timeLookbackDays: String(rule?.time_constraints?.lookback_days ?? ''),
      scopeTarget: rule?.scope?.target ?? 'student',
      branch: rule?.scope?.branch ?? '',
      actions: actionsFromRule(rule),
      chain_to_rule_id: rule?.chain_to_rule_id ?? ''
    };
    builderErrors = {};
    builderSubmitError = '';
    builderOpen = true;
  }

  function updateBuilder<K extends keyof RuleBuilderState>(
    key: K,
    value: RuleBuilderState[K]
  ) {
    builder = { ...builder, [key]: value };
  }

  function updateCondition(
    index: number,
    key: keyof BuilderCondition,
    value: string
  ) {
    const conditions = builder.conditions.map((condition, current) => {
      if (current !== index) return condition;
      if (key === 'field') {
        const meta = conditionMetaFor(value);
        return {
          field: value,
          operator: meta.operators[0],
          value: meta.type === 'number' ? '100' : (meta.options?.[0] ?? ''),
          value_max: ''
        };
      }
      return { ...condition, [key]: value };
    });
    builder = { ...builder, conditions };
  }

  function addCondition() {
    builder = {
      ...builder,
      conditions: [...builder.conditions, defaultBuilderCondition()]
    };
  }

  function removeCondition(index: number) {
    builder = {
      ...builder,
      conditions:
        builder.conditions.length === 1
          ? builder.conditions
          : builder.conditions.filter((_, current) => current !== index)
    };
  }

  function updateActionType(index: number, type: string) {
    const actions = builder.actions.map((action, current) =>
      current === index ? defaultBuilderAction(type) : action
    );
    builder = { ...builder, actions };
  }

  function updateActionParam(
    index: number,
    key: string,
    value: string | boolean
  ) {
    const actions = builder.actions.map((action, current) =>
      current === index
        ? { ...action, params: { ...action.params, [key]: value } }
        : action
    );
    builder = { ...builder, actions };
  }

  function addAction() {
    builder = {
      ...builder,
      actions: [
        ...builder.actions,
        defaultBuilderAction(availableActions()[0].type)
      ]
    };
  }

  function removeAction(index: number) {
    builder = {
      ...builder,
      actions:
        builder.actions.length === 1
          ? builder.actions
          : builder.actions.filter((_, current) => current !== index)
    };
  }

  function parseValue(field: string, value: string) {
    const meta = conditionMetaFor(field);
    if (meta.type === 'number' || meta.type === 'numeric') return Number(value);
    if (value === 'true') return true;
    if (value === 'false') return false;
    if (meta.type === 'enum' && value.includes(','))
      return value.split(',').map((item) => item.trim());
    return value;
  }

  function parseParam(definition: ParamDefinition, value: string | boolean) {
    if (definition.type === 'boolean') return Boolean(value);
    if (definition.type === 'number') return Number(value);
    return value;
  }

  function validateBuilder() {
    const nextErrors: Record<string, string> = {};
    if (!builder.name.trim()) nextErrors.name = 'Rule name is required.';
    builder.conditions.forEach((condition, index) => {
      if (!condition.field)
        nextErrors[`condition-${index}-field`] = 'Required.';
      if (!condition.operator)
        nextErrors[`condition-${index}-operator`] = 'Required.';
      if (condition.value === '')
        nextErrors[`condition-${index}-value`] = 'Required.';
      if (condition.operator === 'between') {
        if (condition.value_max === '')
          nextErrors[`condition-${index}-value_max`] = 'Required.';
        const min = Number(condition.value);
        const max = Number(condition.value_max);
        if (!Number.isNaN(min) && !Number.isNaN(max) && min >= max)
          nextErrors[`condition-${index}-value_max`] =
            'Maximum must be greater than minimum.';
      }
    });
    if (!builder.actions.length)
      nextErrors.actions = 'Add at least one action.';
    builder.actions.forEach((action, actionIndex) => {
      for (const param of actionParamDefinitions(action.type)) {
        const value = action.params[param.key];
        if (param.required && (value === undefined || value === '')) {
          nextErrors[`action-${actionIndex}-${param.key}`] = 'Required.';
        }
      }
    });
    builderErrors = nextErrors;
    return Object.keys(nextErrors).length === 0;
  }

  function rulePayload() {
    return {
      name: builder.name.trim(),
      description: builder.description.trim() || null,
      type: builder.type,
      priority: builder.priority,
      active: builder.active,
      conditions: [
        {
          logic: builder.conditionLogic,
          conditions: builder.conditions.map((condition) => {
            const payload: Condition = {
              field: condition.field,
              operator: condition.operator,
              value: parseValue(condition.field, condition.value)
            };
            if (condition.operator === 'between')
              payload.value_max = parseValue(
                condition.field,
                condition.value_max
              );
            return payload;
          })
        }
      ],
      time_constraints: builder.timeWindow
        ? {
            window: builder.timeWindow,
            lookback_days: builder.timeLookbackDays ? Number(builder.timeLookbackDays) : undefined
          }
        : undefined,
      scope: {
        target: builder.scopeTarget,
        branch: builder.branch || undefined
      },
      actions: builder.actions.map((action) => ({
        type: action.type,
        params: Object.fromEntries(
          actionParamDefinitions(action.type).map((param) => [
            param.key,
            parseParam(param, action.params[param.key] ?? '')
          ])
        )
      })),
      chain_to_rule_id: builder.chain_to_rule_id || null
    };
  }

  async function validateOnly() {
    if (validateBuilder()) notify('Rule definition is valid.', 'success');
  }

  async function saveRule() {
    builderSubmitError = '';
    if (!validateBuilder()) return;
    try {
      if (builder.id) await api.patch(`/rules/${builder.id}`, rulePayload());
      else await api.post('/rules', rulePayload());
      notify('Rule saved.', 'success');
      builderOpen = false;
      await loadRules();
    } catch (err) {
      builderSubmitError =
        err instanceof Error ? err.message : 'Could not save rule.';
    }
  }

  function requestToggle(rule: Rule, active: boolean) {
    if (!active && rule.active) {
      pendingToggle = { rule, active };
      rules = { ...rules, items: [...rules.items] };
      return;
    }
    toggleRule(rule, active);
  }

  async function toggleRule(rule: Rule, active: boolean) {
    try {
      await api.post(`/rules/${rule.id}/toggle`, { active });
      notify(active ? 'Rule activated.' : 'Rule deactivated.', 'success');
      pendingToggle = null;
      await loadRules();
    } catch (err) {
      pendingToggle = null;
      notify(
        err instanceof Error ? err.message : 'Could not toggle rule.',
        'error'
      );
      await loadRules();
    }
  }

  async function deleteRule() {
    if (!deleteTarget) return;
    try {
      await api.delete(`/rules/${deleteTarget.id}`);
      notify('Rule deleted.', 'success');
      deleteTarget = null;
      await loadRules();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not delete rule.',
        'error'
      );
    }
  }

  async function duplicateRule(rule: Rule) {
    try {
      await api.post(`/rules/${rule.id}/duplicate`);
      notify('Rule duplicated.', 'success');
      await loadRules();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not duplicate rule.',
        'error'
      );
    }
  }

  function rulePayloadFromRule(rule: Rule) {
    return {
      name: rule.name,
      description: rule.description ?? null,
      type: rule.type,
      priority: rule.priority,
      active: rule.active,
      conditions: rule.conditions ?? [],
      time_constraints: rule.time_constraints ?? undefined,
      scope: rule.scope ?? undefined,
      actions: rule.actions ?? [],
      chain_to_rule_id: rule.chain_to_rule_id ?? null
    };
  }

  function openTest(rule: Rule) {
    testTarget = rule;
    testResult = null;
    testOpen = true;
  }

  async function runTest() {
    if (!testTarget) return;
    try {
      const payload = JSON.parse(testForm.sample_data);
      testResult = await api.post(`/rules/${testTarget.id}/test`, payload);
    } catch (err) {
      notify(
        err instanceof SyntaxError
          ? 'Sample data must be valid JSON.'
          : err instanceof Error
            ? err.message
            : 'Could not test rule.',
        'error'
      );
    }
  }

  function openSimulation(rule: Rule) {
    simulationTarget = rule;
    simulationDates = { date_from: isoDaysAgo(7), date_to: todayIso() };
    simulationResult = null;
    simulationOpen = true;
  }

  async function runSimulation() {
    if (!simulationTarget) return;
    try {
      simulationResult = await api.post<Record<string, unknown>>(
        `/rules/${simulationTarget.id}/simulate`,
        undefined,
        { query: simulationDates }
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not simulate rule.',
        'error'
      );
    }
  }

  async function loadExecutions(ruleId = selectedExecutionRuleId) {
    if (!ruleId) {
      notify('Choose a rule first.', 'warning');
      return;
    }
    selectedExecutionRuleId = ruleId;
    activeTab = 'executions';
    executionLoading = true;
    try {
      executions = asPage(
        await api.get<Paginated<RuleExecution> | RuleExecution[]>(
          `/rules/${ruleId}/executions`,
          { page: executionPage, size: executionSize }
        ),
        executionPage,
        executionSize
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not load executions.',
        'error'
      );
    } finally {
      executionLoading = false;
    }
  }

  function chainNode(id: string | undefined) {
    return chainData.nodes?.find((node) => node.id === id);
  }

  function outgoingEdges(id: string) {
    return (chainData.edges ?? []).filter(
      (edge) => (edge.from_rule_id ?? edge.from) === id
    );
  }

  onMount(loadRules);
</script>

<svelte:head>
  <title>Rule Engine | CleanPlates</title>
</svelte:head>

<PageHeader
  label="Rule engine"
  title="Automated waste policy enforcement"
  description="Create IF/THEN rule definitions, test sample events, simulate historical windows, and inspect execution chains."
>
  <svelte:fragment slot="actions">
    <Button variant="secondary" on:click={loadRules} id="btn-refresh-rules">
      <RefreshCw size={16} />
      Refresh
    </Button>
    <Button on:click={() => openBuilder()} id="btn-create-rule">
      <Plus size={16} />
      Create rule
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Total Rules"
    value={number(rules.total)}
    helper="Configured rules"
  >
    <svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Active"
    value={number(activeRules)}
    helper="Evaluating events"
    tone="good"
  >
    <svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Triggered Today"
    value={number(triggeredToday)}
    helper="Loaded rule set"
    tone="warn"
  >
    <svelte:fragment slot="icon"><Play size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Chained Rules"
    value={number(chainedRules)}
    helper="Rule handoffs"
  >
    <svelte:fragment slot="icon"><GitBranch size={19} /></svelte:fragment>
  </StatCard>
</div>

{#if metadataError}
  <div
    class="mt-5 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary"
  >
    {metadataError}
  </div>
{/if}

<div class="mt-5">
  <Tabs {tabs} active={activeTab} onChange={setTab} />
</div>

{#if activeTab === 'rules'}
  <div class="mt-5">
    <FilterBar
      filters={ruleFilters}
      values={filterRecord}
      onFilter={applyFilters}
      onReset={resetFilters}
    />
  </div>

  <div class="mt-5 flex justify-end">
    <select
      class="select-field w-28"
      bind:value={size}
      on:change={() => {
        page = 1;
        loadRules();
      }}
      id="select-rules-page-size"
    >
      <option value={10}>10</option>
      <option value={25}>25</option>
      <option value={50}>50</option>
      <option value={100}>100</option>
    </select>
  </div>

  <div class="mt-4">
    {#if error}
      <div
        class="rounded-md border border-down/30 bg-down/10 p-4 text-sm text-down"
      >
        {error}
      </div>
    {:else}
      <DataTable
        columns={ruleColumns}
        rows={ruleRows}
        {loading}
        {page}
        total={rules.total}
        pageSize={size}
        sortKey={sort}
        sortDirection={order}
        onSort={sortRules}
        onPageChange={goToPage}
      >
        <svelte:fragment slot="cell" let:row let:column let:value>
          {@const rule = ruleOf(row)}
          {#if column.key === 'name'}
            <div>
              <p class="font-semibold text-body">{rule.name}</p>
              <p class="mt-1 line-clamp-2 text-xs text-muted">
                {rule.description ?? 'No description'}
              </p>
            </div>
          {:else if column.key === 'type'}
            <span class={typeClass(rule.type)}>{titleCase(rule.type)}</span>
          {:else if column.key === 'priority'}
            <span class={priorityClass(rule.priority)}
              >{titleCase(rule.priority)}</span
            >
          {:else if column.key === 'active'}
            <div class="flex justify-center">
              <Toggle
                value={rule.active}
                onChange={(active) => requestToggle(rule, active)}
              />
            </div>
          {:else if column.key === 'triggered_today_count'}
            {number(rule.triggered_today_count ?? 0)}
          {:else if column.key === 'execution_count'}
            {number(rule.execution_count ?? 0)}
          {:else if column.key === 'last_triggered_at'}
            {dateTime(rule.last_triggered_at)}
          {:else}
            {value ?? '-'}
          {/if}
        </svelte:fragment>

        <svelte:fragment slot="row-actions" let:row>
          {@const rule = ruleOf(row)}
          <div class="flex flex-wrap justify-end gap-2">
            <Button
              size="sm"
              variant="secondary"
              on:click={() => openBuilder(rule)}
              id={`btn-edit-rule-${rule.id}`}
            >
              <Edit3 size={14} />
              Edit
            </Button>
            <Button
              size="sm"
              variant="secondary"
              on:click={() => openTest(rule)}
              id={`btn-test-rule-${rule.id}`}
            >
              <Play size={14} />
              Test
            </Button>
            <Button
              size="sm"
              variant="secondary"
              on:click={() => openSimulation(rule)}
              id={`btn-simulate-rule-${rule.id}`}
            >
              Sim
            </Button>
            <Button
              size="sm"
              variant="secondary"
              on:click={() => duplicateRule(rule)}
              id={`btn-duplicate-rule-${rule.id}`}
            >
              <Copy size={14} />
            </Button>
            <Button
              size="sm"
              variant="secondary"
              on:click={() => loadExecutions(rule.id)}
              id={`btn-view-rule-executions-${rule.id}`}
            >
              Log
            </Button>
            <Button
              size="sm"
              variant="danger"
              on:click={() => (deleteTarget = rule)}
              id={`btn-delete-rule-${rule.id}`}
            >
              <Trash2 size={14} />
            </Button>
          </div>
        </svelte:fragment>

        <svelte:fragment slot="empty">
          <EmptyState
            title="No rules"
            message="Create a threshold, frequency, trend, or composite rule."
          />
        </svelte:fragment>
      </DataTable>
    {/if}
  </div>
{:else if activeTab === 'executions'}
  <div
    class="mt-5 grid gap-3 rounded-md border border-border bg-elevated/30 p-4 md:grid-cols-[1fr_auto]"
  >
    <FormField label="Rule">
      <select
        class="select-field"
        bind:value={selectedExecutionRuleId}
        id="select-execution-rule"
      >
        <option value="">Choose rule</option>
        {#each rules.items as rule}
          <option value={rule.id}>{rule.name}</option>
        {/each}
      </select>
    </FormField>
    <div class="flex items-end">
      <Button on:click={() => loadExecutions()} id="btn-load-executions">
        <History size={16} />
        Load history
      </Button>
    </div>
  </div>

  <div class="mt-5">
    <DataTable
      columns={executionColumns}
      rows={executionRows}
      loading={executionLoading}
      page={executionPage}
      total={executions.total}
      pageSize={executionSize}
      onPageChange={(nextPage) => {
        executionPage = nextPage;
        loadExecutions();
      }}
    >
      <svelte:fragment slot="cell" let:row let:column let:value>
        {@const execution = executionOf(row)}
        {#if column.key === 'rule_name'}
          {execution.rule_name ??
            chainNode(execution.rule_id)?.name ??
            execution.rule_id}
        {:else if column.key === 'trigger_source'}
          {titleCase(
            execution.trigger_source ?? execution.trigger_event_type ?? 'event'
          )}
        {:else if column.key === 'executed_at'}
          {dateTime(execution.executed_at)}
        {:else if column.key === 'matched_conditions'}
          <code class="text-xs text-muted-strong">
            {JSON.stringify(execution.matched_conditions ?? {}).slice(0, 90)}
          </code>
        {:else if column.key === 'executed_actions'}
          <code class="text-xs text-muted-strong">
            {JSON.stringify(execution.executed_actions ?? {}).slice(0, 90)}
          </code>
        {:else if column.key === 'result_status'}
          <StatusBadge value={execution.result_status} compact />
        {:else}
          {value ?? '-'}
        {/if}
      </svelte:fragment>
      <svelte:fragment slot="empty">
        <EmptyState
          title="No executions"
          message="Choose a rule and load its execution history."
        />
      </svelte:fragment>
    </DataTable>
  </div>
{:else}
  <div class="mt-5">
    {#if !chainData.nodes?.length && !chainData.chains?.length}
      <div class="table-wrapper p-6">
        <EmptyState
          title="No rule chains"
          message="Rules with chain targets appear here."
        />
      </div>
    {:else if chainData.nodes?.length}
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {#each chainData.nodes as node}
          <div class="rounded-md border border-border bg-elevated/30 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-semibold text-body">{node.name}</p>
                <p class="mt-1 text-xs text-muted">{node.id}</p>
              </div>
              <StatusBadge value={node.priority ?? 'chain'} compact />
            </div>
            <div class="mt-3 space-y-2 text-sm">
              {#if outgoingEdges(node.id).length}
                {#each outgoingEdges(node.id) as edge}
                  {@const target = chainNode(edge.to_rule_id ?? edge.to)}
                  <div class="flex items-center gap-2 text-muted-strong">
                    <GitBranch size={14} />
                    <span>{target?.name ?? edge.to_rule_id ?? edge.to}</span>
                  </div>
                {/each}
              {:else}
                <p class="text-muted">No outgoing links</p>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <DataTable
        columns={[
          { key: 'source', label: 'Rule' },
          { key: 'trigger', label: 'Triggers' },
          { key: 'target', label: 'Next Rule' }
        ]}
        rows={(chainData.chains ?? []) as Record<string, unknown>[]}
        page={1}
        total={chainData.chains?.length ?? 0}
        pageSize={50}
      />
    {/if}
  </div>
{/if}

<Modal
  open={builderOpen}
  title={builder.id ? 'Edit rule' : 'Create rule'}
  description="Build a rule definition from conditions and actions."
  wide
  on:close={() => (builderOpen = false)}
>
  <form class="space-y-5" on:submit|preventDefault={saveRule}>
    {#if builderSubmitError}
      <div
        class="rounded-md border border-down/30 bg-down/10 p-3 text-sm text-down"
      >
        {builderSubmitError}
      </div>
    {/if}

    <div class="grid gap-3 md:grid-cols-2">
      <FormField label="Name" required error={builderErrors.name}>
        <input
          class="input-field"
          value={builder.name}
          on:input={(event) => updateBuilder('name', inputValue(event))}
          required
        />
      </FormField>
      <FormField label="Description">
        <input
          class="input-field"
          value={builder.description}
          on:input={(event) => updateBuilder('description', inputValue(event))}
        />
      </FormField>
      <FormField label="Type" required>
        <select
          class="select-field"
          value={builder.type}
          on:change={(event) => updateBuilder('type', inputValue(event))}
        >
          <option value="threshold">Threshold</option>
          <option value="frequency">Frequency</option>
          <option value="trend">Trend</option>
          <option value="composite">Composite</option>
        </select>
      </FormField>
      <FormField label="Priority" required>
        <select
          class="select-field"
          value={builder.priority}
          on:change={(event) => updateBuilder('priority', inputValue(event))}
        >
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </FormField>
      <div class="md:col-span-2">
        <Toggle
          value={builder.active}
          onChange={(active) => updateBuilder('active', active)}
          label="Active"
        />
      </div>
    </div>

    <section class="rounded-md border border-border bg-elevated/30 p-4">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="label">IF</p>
          <h3 class="mt-1 text-base font-semibold text-body">Conditions</h3>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          on:click={addCondition}
        >
          <Plus size={14} />
          Add condition
        </Button>
      </div>

      <div class="mb-3 max-w-xs">
        <FormField label="Logic">
          <select
            class="select-field"
            value={builder.conditionLogic}
            on:change={(event) =>
              updateBuilder('conditionLogic', inputValue(event) as Logic)}
          >
            <option value="AND">AND</option>
            <option value="OR">OR</option>
          </select>
        </FormField>
      </div>

      <div class="space-y-3">
        {#each builder.conditions as condition, index}
          {@const meta = conditionMetaFor(condition.field)}
          <div
            class="grid gap-3 rounded-md border border-border bg-card/50 p-3 md:grid-cols-[1fr_1fr_1fr_auto]"
          >
            <FormField
              label="Field"
              required
              error={builderErrors[`condition-${index}-field`]}
            >
              <select
                class="select-field"
                value={condition.field}
                on:change={(event) =>
                  updateCondition(index, 'field', inputValue(event))}
              >
                {#each conditionOptions as option}
                  <option value={option.key}>{option.label}</option>
                {/each}
              </select>
            </FormField>
            <FormField
              label="Operator"
              required
              error={builderErrors[`condition-${index}-operator`]}
            >
              <select
                class="select-field"
                value={condition.operator}
                on:change={(event) =>
                  updateCondition(index, 'operator', inputValue(event))}
              >
                {#each meta.operators as operator}
                  <option value={operator}>{titleCase(operator)}</option>
                {/each}
              </select>
            </FormField>
            <div
              class={condition.operator === 'between' ? 'md:col-span-1' : ''}
            >
              <FormField
                label={condition.operator === 'between' ? 'Minimum' : 'Value'}
                required
                error={builderErrors[`condition-${index}-value`]}
              >
                {#if meta.options?.length}
                  <select
                    class="select-field"
                    value={condition.value}
                    on:change={(event) =>
                      updateCondition(index, 'value', inputValue(event))}
                  >
                    {#each meta.options as option}
                      <option value={option}>{titleCase(option)}</option>
                    {/each}
                  </select>
                {:else}
                  <input
                    class="input-field"
                    type={meta.type === 'number' || meta.type === 'numeric' ? 'number' : 'text'}
                    value={condition.value}
                    on:input={(event) =>
                      updateCondition(index, 'value', inputValue(event))}
                  />
                {/if}
              </FormField>
              {#if condition.operator === 'between'}
                <div class="mt-3">
                  <FormField
                    label="Maximum"
                    required
                    error={builderErrors[`condition-${index}-value_max`]}
                  >
                    <input
                      class="input-field"
                      type={meta.type === 'number' || meta.type === 'numeric' ? 'number' : 'text'}
                      value={condition.value_max}
                      on:input={(event) =>
                        updateCondition(index, 'value_max', inputValue(event))}
                    />
                  </FormField>
                </div>
              {/if}
            </div>
            <div class="flex items-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                on:click={() => removeCondition(index)}
                disabled={builder.conditions.length === 1}
              >
                Remove
              </Button>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <section
      class="grid gap-3 rounded-md border border-border bg-elevated/30 p-4 md:grid-cols-2"
    >
      <div>
        <p class="label">Time constraints</p>
        <div class="mt-3 grid gap-3 sm:grid-cols-2">
          <FormField label="Window">
            <select
              class="select-field"
              value={builder.timeWindow}
              on:change={(event) =>
                updateBuilder('timeWindow', inputValue(event))}
            >
              <option value="per_meal">Per meal</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </FormField>
          <FormField label="Lookback days" hint="Optional — restricts condition evaluation to the past N days">
            <input
              class="input-field"
              type="number"
              min="1"
              value={builder.timeLookbackDays}
              placeholder="e.g. 7"
              on:input={(event) =>
                updateBuilder('timeLookbackDays', inputValue(event))}
            />
          </FormField>
        </div>
      </div>
      <div>
        <p class="label">Scope</p>
        <div class="mt-3 grid gap-3 sm:grid-cols-2">
          <FormField label="Target">
            <select
              class="select-field"
              value={builder.scopeTarget}
              on:change={(event) =>
                updateBuilder('scopeTarget', inputValue(event))}
            >
              <option value="student">Student</option>
              <option value="device">Device</option>
              <option value="institution">Institution</option>
            </select>
          </FormField>
          <FormField label="Branch">
            <input
              class="input-field"
              value={builder.branch}
              placeholder="All branches"
              on:input={(event) => updateBuilder('branch', inputValue(event))}
            />
          </FormField>
        </div>
      </div>
    </section>

    <section class="rounded-md border border-border bg-elevated/30 p-4">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="label">THEN</p>
          <h3 class="mt-1 text-base font-semibold text-body">Actions</h3>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          on:click={addAction}
        >
          <Plus size={14} />
          Add action
        </Button>
      </div>

      {#if builderErrors.actions}
        <p class="mb-3 text-sm text-down">{builderErrors.actions}</p>
      {/if}

      <div class="space-y-3">
        {#each builder.actions as action, actionIndex}
          <div class="rounded-md border border-border bg-card/50 p-3">
            <div class="mb-3 flex flex-wrap items-end justify-between gap-3">
              <FormField label="Action" required>
                <select
                  class="select-field min-w-64"
                  value={action.type}
                  on:change={(event) =>
                    updateActionType(actionIndex, inputValue(event))}
                >
                  {#each actionOptions as option}
                    <option value={option.type}>{option.label}</option>
                  {/each}
                </select>
              </FormField>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                on:click={() => removeAction(actionIndex)}
                disabled={builder.actions.length === 1}
              >
                Remove
              </Button>
            </div>

            <div class="grid gap-3 md:grid-cols-3">
              {#each actionParamDefinitions(action.type) as param}
                <FormField
                  label={param.label}
                  required={param.required}
                  error={builderErrors[`action-${actionIndex}-${param.key}`]}
                >
                  {#if param.type === 'boolean'}
                    <label
                      class="inline-flex h-10 items-center gap-2 text-sm text-body"
                    >
                      <input
                        type="checkbox"
                        checked={Boolean(action.params[param.key])}
                        on:change={(event) =>
                          updateActionParam(
                            actionIndex,
                            param.key,
                            checkedValue(event)
                          )}
                      />
                      Enabled
                    </label>
                  {:else if param.options?.length}
                    <select
                      class="select-field"
                      value={String(action.params[param.key] ?? '')}
                      on:change={(event) =>
                        updateActionParam(
                          actionIndex,
                          param.key,
                          inputValue(event)
                        )}
                    >
                      {#each param.options as option}
                        <option value={option}>{titleCase(option)}</option>
                      {/each}
                    </select>
                  {:else}
                    <input
                      class="input-field"
                      type={param.type === 'number' ? 'number' : 'text'}
                      value={String(action.params[param.key] ?? '')}
                      on:input={(event) =>
                        updateActionParam(
                          actionIndex,
                          param.key,
                          inputValue(event)
                        )}
                    />
                  {/if}
                </FormField>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </section>

    <section class="rounded-md border border-border bg-elevated/30 p-4">
      <FormField label="Chain rule">
        <select
          class="select-field"
          value={builder.chain_to_rule_id}
          on:change={(event) =>
            updateBuilder('chain_to_rule_id', inputValue(event))}
        >
          <option value="">None</option>
          {#each rules.items.filter((rule) => rule.id !== builder.id) as rule}
            <option value={rule.id}>{rule.name}</option>
          {/each}
        </select>
      </FormField>
    </section>

    <div class="flex flex-wrap justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (builderOpen = false)}
      >
        Cancel
      </Button>
      <Button type="button" variant="secondary" on:click={validateOnly}>
        Validate
      </Button>
      <Button type="submit" id="btn-save-rule">Save rule</Button>
    </div>
  </form>
</Modal>

<Modal
  open={testOpen}
  title="Test rule"
  description={testTarget?.name ?? ''}
  wide
  on:close={() => (testOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={runTest}>
    <FormField label="Sample data" hint="Fields: waste_grams, meal_type, severity, frequency_count, warning_count, penalty_count, student_branch, student_year, sustainability_score">
      <textarea
        class="textarea-field min-h-[220px] font-mono text-xs"
        bind:value={testForm.sample_data}
      ></textarea>
    </FormField>
    <div class="flex justify-end">
      <Button type="submit" id="btn-run-rule-test">
        <Play size={16} />
        Run test
      </Button>
    </div>
    {#if testResult !== null}
      <pre
        class="max-h-80 overflow-auto rounded-md bg-canvas p-4 text-xs text-body">{JSON.stringify(
          testResult,
          null,
          2
        )}</pre>
    {/if}
  </form>
</Modal>

<Modal
  open={simulationOpen}
  title="Simulate rule"
  description={simulationTarget?.name ?? ''}
  on:close={() => (simulationOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={runSimulation}>
    <div class="grid gap-3 sm:grid-cols-2">
      <FormField label="From" required>
        <input
          class="input-field"
          type="date"
          bind:value={simulationDates.date_from}
          required
        />
      </FormField>
      <FormField label="To" required>
        <input
          class="input-field"
          type="date"
          bind:value={simulationDates.date_to}
          required
        />
      </FormField>
    </div>
    <div class="flex justify-end">
      <Button type="submit" id="btn-run-simulation">
        <Play size={16} />
        Run simulation
      </Button>
    </div>
    {#if simulationResult}
      <div class="grid gap-3 sm:grid-cols-2">
        {#each Object.entries(simulationResult).slice(0, 4) as [key, value]}
          <div class="rounded-md border border-border bg-elevated/40 p-3">
            <p class="label">{titleCase(key)}</p>
            <p class="mt-1 text-lg font-semibold text-body">
              {typeof value === 'number' ? number(value) : String(value)}
            </p>
          </div>
        {/each}
      </div>
      <pre
        class="max-h-64 overflow-auto rounded-md bg-canvas p-4 text-xs text-body">{JSON.stringify(
          simulationResult,
          null,
          2
        )}</pre>
    {/if}
  </form>
</Modal>

<ConfirmDialog
  open={!!pendingToggle}
  title="Deactivate rule"
  message={pendingToggle
    ? `Deactivate "${pendingToggle.rule.name}"? It will stop evaluating new events.`
    : ''}
  confirmLabel="Deactivate"
  danger
  onConfirm={() => pendingToggle && toggleRule(pendingToggle.rule, false)}
  onCancel={() => {
    pendingToggle = null;
    rules = { ...rules, items: [...rules.items] };
  }}
/>

<ConfirmDialog
  open={!!deleteTarget}
  title="Delete rule"
  message={deleteTarget
    ? `Delete "${deleteTarget.name}"? This cannot be undone.`
    : ''}
  confirmLabel="Delete"
  danger
  onConfirm={deleteRule}
  onCancel={() => (deleteTarget = null)}
/>
