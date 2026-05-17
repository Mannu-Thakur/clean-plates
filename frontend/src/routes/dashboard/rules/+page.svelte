<script lang="ts">
  import { onMount } from 'svelte';
  import { Copy, FlaskConical, Plus, RefreshCw, Trash2 } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { Paginated, RuleItem } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, number, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type FieldOption = {
    field: string;
    label: string;
    type: string;
    operators: string[];
    enum_values?: string[] | null;
  };
  type ActionOption = {
    type: string;
    label: string;
    required_params: string[];
    optional_params: string[];
  };

  let loading = true;
  let error = '';
  let rules: Paginated<RuleItem> = {
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 1
  };
  let fields: FieldOption[] = [];
  let actions: ActionOption[] = [];
  let chains: {
    nodes: Array<{ id: string; name: string }>;
    edges: Array<{ from_rule_id: string; to_rule_id: string }>;
  } = { nodes: [], edges: [] };
  let executions: Paginated<Record<string, unknown>> | null = null;
  let filters = { type: '', priority: '', status: '' };
  let activeTab: 'executions' | 'chains' = 'executions';
  let builderOpen = false;
  let simulationOpen = false;
  let selectedRule: RuleItem | null = null;
  let simulationResult: Record<string, unknown> | null = null;
  let simDates = {
    date_from: new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10),
    date_to: new Date().toISOString().slice(0, 10)
  };
  let builder = {
    id: '',
    name: '',
    description: '',
    type: 'threshold',
    priority: 'medium',
    active: true,
    field: 'weight_grams',
    operator: 'gt',
    value: '100',
    action_type: 'generate_warning',
    warning_level: 'level_1',
    action_reason: 'Waste threshold exceeded',
    points: 5,
    chain_to_rule_id: ''
  };

  $: activeRules = rules.items.filter((rule) => rule.active).length;
  $: triggeredToday = rules.items.reduce(
    (total, rule) => total + Number(rule.execution_count ?? 0),
    0
  );
  $: chainedRules = rules.items.filter((rule) =>
    Boolean((rule as unknown as { chain_to_rule_id?: string }).chain_to_rule_id)
  ).length;
  $: selectedField = fields.find((field) => field.field === builder.field);

  async function loadRules() {
    loading = true;
    error = '';
    try {
      const [rulesData, fieldsData, actionsData, chainsData] =
        await Promise.all([
          api.get<Paginated<RuleItem>>('/rules', filters),
          api.get<FieldOption[]>('/rules/metadata/fields'),
          api.get<ActionOption[]>('/rules/metadata/actions'),
          api.get<typeof chains>('/rules/chains')
        ]);
      rules = rulesData;
      fields = fieldsData;
      actions = actionsData;
      chains = chainsData;
      if (!builder.field && fieldsData[0]) builder.field = fieldsData[0].field;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load rules';
    } finally {
      loading = false;
    }
  }

  function parseValue(value: string) {
    if (selectedField?.type === 'number') return Number(value);
    if (value === 'true') return true;
    if (value === 'false') return false;
    return value;
  }

  function actionPayload() {
    if (builder.action_type === 'generate_warning')
      return { level: builder.warning_level, reason: builder.action_reason };
    if (builder.action_type === 'increase_penalty')
      return { points: Number(builder.points), reason: builder.action_reason };
    if (builder.action_type === 'trigger_escalation')
      return {
        escalated_to_role: 'institution_admin',
        reason: builder.action_reason
      };
    if (builder.action_type === 'classify_student') return { status: 'red' };
    if (builder.action_type === 'create_audit_log')
      return { summary: builder.action_reason };
    if (builder.action_type === 'send_email')
      return { subject: builder.name, body: builder.action_reason };
    return {};
  }

  function rulePayload() {
    return {
      name: builder.name,
      description: builder.description || null,
      type: builder.type,
      priority: builder.priority,
      active: builder.active,
      conditions: [
        {
          logic: 'AND',
          conditions: [
            {
              field: builder.field,
              operator: builder.operator,
              value: parseValue(builder.value)
            }
          ]
        }
      ],
      time_constraints: { lookback_days: 1 },
      scope: { target: 'student', filters: {} },
      actions: [{ type: builder.action_type, params: actionPayload() }],
      chain_to_rule_id: builder.chain_to_rule_id || null
    };
  }

  function openBuilder(rule: RuleItem | null = null) {
    selectedRule = rule;
    const condition = ((
      rule?.conditions?.[0] as
        | {
            conditions?: Array<{
              field?: string;
              operator?: string;
              value?: unknown;
            }>;
          }
        | undefined
    )?.conditions ?? [])[0];
    const action =
      (rule?.actions?.[0] as
        | { type?: string; params?: Record<string, unknown> }
        | undefined) ?? undefined;
    builder = {
      id: rule?.id ?? '',
      name: rule?.name ?? '',
      description: rule?.description ?? '',
      type: rule?.type ?? 'threshold',
      priority: rule?.priority ?? 'medium',
      active: rule?.active ?? true,
      field: condition?.field ?? fields[0]?.field ?? 'weight_grams',
      operator: condition?.operator ?? 'gt',
      value: String(condition?.value ?? '100'),
      action_type: action?.type ?? 'generate_warning',
      warning_level: String(action?.params?.level ?? 'level_1'),
      action_reason: String(
        action?.params?.reason ??
          action?.params?.body ??
          'Waste threshold exceeded'
      ),
      points: Number(action?.params?.points ?? 5),
      chain_to_rule_id:
        (rule as unknown as { chain_to_rule_id?: string })?.chain_to_rule_id ??
        ''
    };
    builderOpen = true;
  }

  async function saveRule() {
    try {
      if (builder.id) await api.patch(`/rules/${builder.id}`, rulePayload());
      else await api.post('/rules', rulePayload());
      notify('Rule saved.', 'success');
      builderOpen = false;
      await loadRules();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save rule.',
        'error'
      );
    }
  }

  async function toggleRule(rule: RuleItem) {
    try {
      await api.post(`/rules/${rule.id}/toggle`, { active: !rule.active });
      await loadRules();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not toggle rule.',
        'error'
      );
    }
  }

  async function deleteRule(rule: RuleItem) {
    if (!window.confirm(`Delete ${rule.name}?`)) return;
    try {
      await api.delete(`/rules/${rule.id}`);
      notify('Rule deleted.', 'success');
      await loadRules();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not delete rule.',
        'error'
      );
    }
  }

  async function duplicateRule(rule: RuleItem) {
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

  async function openSimulation(rule: RuleItem) {
    selectedRule = rule;
    simulationResult = null;
    simulationOpen = true;
  }

  async function runSimulation() {
    if (!selectedRule) return;
    try {
      simulationResult = await api.post(
        `/rules/${selectedRule.id}/simulate`,
        undefined,
        { query: simDates }
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not simulate rule.',
        'error'
      );
    }
  }

  async function testRule(rule: RuleItem) {
    try {
      const result = await api.post<Record<string, unknown>>(
        `/rules/${rule.id}/test`,
        {
          waste_grams: 180,
          meal_type: 'lunch',
          severity: 'red',
          warning_count: 2,
          sustainability_score: 45
        }
      );
      notify(
        String(
          result.reason ??
            (result.matched
              ? 'Rule matched sample data.'
              : 'Rule did not match sample data.')
        ),
        'info'
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not test rule.',
        'error'
      );
    }
  }

  async function loadExecutions(rule: RuleItem) {
    selectedRule = rule;
    activeTab = 'executions';
    executions = await api.get<Paginated<Record<string, unknown>>>(
      `/rules/${rule.id}/executions`
    );
  }

  onMount(loadRules);
</script>

<svelte:head><title>Rule Engine | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Rule engine</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      Automated waste policy enforcement
    </h2>
  </div>
  <div class="flex flex-wrap gap-2">
    <Button variant="secondary" on:click={loadRules}
      ><RefreshCw size={16} />Refresh</Button
    ><Button on:click={() => openBuilder()} id="btn-create-rule"
      ><Plus size={16} />Create rule</Button
    >
  </div>
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Total Rules"
    value={number(rules.total)}
    helper="Configured rules"
    ><svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Active"
    value={number(activeRules)}
    helper="Evaluating events"
    tone="good"
    ><svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Executions"
    value={number(triggeredToday)}
    helper="Loaded set"
    ><svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard title="Chained" value={number(chainedRules)} helper="Rule handoffs"
    ><svelte:fragment slot="icon"><FlaskConical size={19} /></svelte:fragment
    ></StatCard
  >
</div>

<Card class="mt-5" title="Filters">
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
    <label
      ><span class="label">Type</span><select
        class="field mt-2 w-full"
        bind:value={filters.type}
        id="select-rule-type"
        ><option value="">All</option><option>threshold</option><option
          >frequency</option
        ><option>trend</option><option>composite</option></select
      ></label
    >
    <label
      ><span class="label">Priority</span><select
        class="field mt-2 w-full"
        bind:value={filters.priority}
        id="select-rule-priority"
        ><option value="">All</option><option>critical</option><option
          >high</option
        ><option>medium</option><option>low</option></select
      ></label
    >
    <label
      ><span class="label">Status</span><select
        class="field mt-2 w-full"
        bind:value={filters.status}
        id="select-rule-status"
        ><option value="">All</option><option value="active">Active</option
        ><option value="inactive">Inactive</option></select
      ></label
    >
    <div class="flex items-end">
      <Button class="w-full" on:click={loadRules}>Apply</Button>
    </div>
  </div>
</Card>

<Card class="mt-5" title="Rule list">
  {#if error}<div
      class="rounded-md border border-coral/30 bg-coral/10 p-3 text-coral"
    >
      {error}
    </div>
  {:else if loading}<div
      class="h-96 animate-pulse rounded-lg bg-slate-100"
    ></div>
  {:else if rules.items.length === 0}<EmptyState
      title="No rules yet"
      message="Create a threshold, frequency, trend, or composite rule."
    />
  {:else}
    <div class="overflow-auto">
      <table>
        <thead class="table-head"
          ><tr
            ><th class="table-cell">Rule</th><th class="table-cell">Type</th><th
              class="table-cell">Priority</th
            ><th class="table-cell">Status</th><th class="table-cell"
              >Executions</th
            ><th class="table-cell">Updated</th><th class="table-cell"
              >Actions</th
            ></tr
          ></thead
        ><tbody
          >{#each rules.items as rule}<tr
              ><td class="table-cell"
                ><p class="font-semibold">{rule.name}</p>
                <p class="text-xs text-muted">
                  {rule.description ?? 'No description'}
                </p></td
              ><td class="table-cell">{titleCase(rule.type)}</td><td
                class="table-cell"
                ><StatusBadge value={rule.priority} compact /></td
              ><td class="table-cell"
                ><button
                  on:click={() => toggleRule(rule)}
                  id={`switch-rule-active-${rule.id}`}
                  ><StatusBadge
                    value={rule.active ? 'active' : 'inactive'}
                    compact
                  /></button
                ></td
              ><td class="table-cell">{number(rule.execution_count)}</td><td
                class="table-cell">{dateTime(rule.updated_at)}</td
              ><td class="table-cell"
                ><div class="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => openBuilder(rule)}
                    id={`btn-edit-rule-${rule.id}`}>Edit</Button
                  ><Button
                    size="sm"
                    variant="secondary"
                    on:click={() => testRule(rule)}
                    id={`btn-test-rule-${rule.id}`}>Test</Button
                  ><Button
                    size="sm"
                    variant="secondary"
                    on:click={() => openSimulation(rule)}>Sim</Button
                  ><Button
                    size="sm"
                    variant="secondary"
                    on:click={() => duplicateRule(rule)}
                    id={`btn-duplicate-rule-${rule.id}`}
                    ><Copy size={14} /></Button
                  ><Button
                    size="sm"
                    variant="secondary"
                    on:click={() => loadExecutions(rule)}
                    id={`btn-view-log-${rule.id}`}>Log</Button
                  ><Button
                    size="sm"
                    variant="danger"
                    on:click={() => deleteRule(rule)}
                    id={`btn-delete-rule-${rule.id}`}
                    ><Trash2 size={14} /></Button
                  >
                </div></td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
  {/if}
</Card>

<div class="mt-5 flex gap-2">
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'executions' ? 'bg-fresh text-white' : 'bg-white text-muted'}`}
    on:click={() => (activeTab = 'executions')}>Execution log</button
  >
  <button
    class={`rounded-md px-4 py-2 text-sm font-semibold ${activeTab === 'chains' ? 'bg-fresh text-white' : 'bg-white text-muted'}`}
    on:click={() => (activeTab = 'chains')}>Chains</button
  >
</div>

<Card
  class="mt-5"
  title={activeTab === 'executions'
    ? 'Rule execution log'
    : 'Rule chain visualizer'}
>
  {#if activeTab === 'executions'}
    {#if !executions}<EmptyState
        title="Select a rule log"
        message="Use the Log action on a rule to inspect executions."
      />
    {:else if executions.items.length === 0}<EmptyState title="No executions" />
    {:else}<div class="overflow-auto">
        <table>
          <thead class="table-head"
            ><tr
              ><th class="table-cell">Time</th><th class="table-cell">Event</th
              ><th class="table-cell">Status</th><th class="table-cell"
                >Actions</th
              ></tr
            ></thead
          ><tbody
            >{#each executions.items as execution}<tr
                ><td class="table-cell"
                  >{dateTime(String(execution.executed_at))}</td
                ><td class="table-cell"
                  >{titleCase(String(execution.trigger_event_type))}</td
                ><td class="table-cell"
                  ><StatusBadge
                    value={String(execution.result_status)}
                    compact
                  /></td
                ><td class="table-cell"
                  ><code class="text-xs"
                    >{JSON.stringify(execution.executed_actions).slice(
                      0,
                      120
                    )}</code
                  ></td
                ></tr
              >{/each}</tbody
          >
        </table>
      </div>{/if}
  {:else if chains.nodes.length === 0}<EmptyState title="No rule chains" />
  {:else}<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {#each chains.nodes as node}<div
          class="rounded-lg border border-line p-4"
        >
          <p class="font-semibold">{node.name}</p>
          <p class="mt-1 text-xs text-muted">
            {chains.edges.filter((edge) => edge.from_rule_id === node.id)
              .length} outgoing links
          </p>
        </div>{/each}
    </div>{/if}
</Card>

<Modal
  open={builderOpen}
  title={builder.id ? 'Edit rule' : 'Create rule'}
  description="Build one IF condition and one THEN action. Composite rules can be expanded from here."
  wide
  on:close={() => (builderOpen = false)}
>
  <form class="grid gap-4 lg:grid-cols-2" on:submit|preventDefault={saveRule}>
    <label
      ><span class="label">Name</span><input
        class="field mt-2 w-full"
        bind:value={builder.name}
        required
      /></label
    >
    <label
      ><span class="label">Description</span><input
        class="field mt-2 w-full"
        bind:value={builder.description}
      /></label
    >
    <label
      ><span class="label">Type</span><select
        class="field mt-2 w-full"
        bind:value={builder.type}
        ><option>threshold</option><option>frequency</option><option
          >trend</option
        ><option>composite</option></select
      ></label
    >
    <label
      ><span class="label">Priority</span><select
        class="field mt-2 w-full"
        bind:value={builder.priority}
        ><option>critical</option><option>high</option><option>medium</option
        ><option>low</option></select
      ></label
    >
    <label class="flex items-center gap-2 text-sm"
      ><input type="checkbox" bind:checked={builder.active} /> Active</label
    >
    <label
      ><span class="label">Chain to rule</span><select
        class="field mt-2 w-full"
        bind:value={builder.chain_to_rule_id}
        ><option value="">None</option
        >{#each rules.items.filter((rule) => rule.id !== builder.id) as rule}<option
            value={rule.id}>{rule.name}</option
          >{/each}</select
      ></label
    >
    <div class="rounded-lg border border-line p-4 lg:col-span-2">
      <p class="mb-3 font-semibold">IF</p>
      <div class="grid gap-3 md:grid-cols-3">
        <label
          ><span class="label">Field</span><select
            class="field mt-2 w-full"
            bind:value={builder.field}
            >{#each fields as field}<option value={field.field}
                >{field.label}</option
              >{/each}</select
          ></label
        >
        <label
          ><span class="label">Operator</span><select
            class="field mt-2 w-full"
            bind:value={builder.operator}
            >{#each selectedField?.operators ?? ['gt', 'lt', 'eq'] as operator}<option
                value={operator}>{operator}</option
              >{/each}</select
          ></label
        >
        <label
          ><span class="label">Value</span
          >{#if selectedField?.enum_values}<select
              class="field mt-2 w-full"
              bind:value={builder.value}
              >{#each selectedField.enum_values as value}<option {value}
                  >{titleCase(value)}</option
                >{/each}</select
            >{:else}<input
              class="field mt-2 w-full"
              bind:value={builder.value}
            />{/if}</label
        >
      </div>
    </div>
    <div class="rounded-lg border border-line p-4 lg:col-span-2">
      <p class="mb-3 font-semibold">THEN</p>
      <div class="grid gap-3 md:grid-cols-4">
        <label
          ><span class="label">Action</span><select
            class="field mt-2 w-full"
            bind:value={builder.action_type}
            >{#each actions as action}<option value={action.type}
                >{action.label}</option
              >{/each}</select
          ></label
        >
        <label
          ><span class="label">Warning level</span><select
            class="field mt-2 w-full"
            bind:value={builder.warning_level}
            ><option value="level_1">Level 1</option><option value="level_2"
              >Level 2</option
            ><option value="level_3">Level 3</option></select
          ></label
        >
        <label
          ><span class="label">Penalty points</span><input
            class="field mt-2 w-full"
            type="number"
            min="1"
            max="100"
            bind:value={builder.points}
          /></label
        >
        <label
          ><span class="label">Reason / body</span><input
            class="field mt-2 w-full"
            bind:value={builder.action_reason}
          /></label
        >
      </div>
    </div>
    <div class="flex justify-end gap-2 lg:col-span-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (builderOpen = false)}>Cancel</Button
      ><Button type="submit" id="btn-save-rule">Save rule</Button>
    </div>
  </form>
</Modal>

<Modal
  open={simulationOpen}
  title="Rule simulation"
  description={selectedRule?.name ?? ''}
  on:close={() => (simulationOpen = false)}
>
  <div class="space-y-4">
    <div class="grid gap-3 sm:grid-cols-2">
      <label
        ><span class="label">From</span><input
          class="field mt-2 w-full"
          type="date"
          bind:value={simDates.date_from}
        /></label
      ><label
        ><span class="label">To</span><input
          class="field mt-2 w-full"
          type="date"
          bind:value={simDates.date_to}
        /></label
      >
    </div>
    <Button on:click={runSimulation} id="btn-run-simulation"
      >Run simulation</Button
    >
    {#if simulationResult}
      <pre
        class="max-h-80 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(
          simulationResult,
          null,
          2
        )}</pre>
    {/if}
  </div>
</Modal>
