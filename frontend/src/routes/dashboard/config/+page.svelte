<script lang="ts">
  import { onMount } from 'svelte';
  import { Plus, RotateCcw, Save, Trash2 } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Tabs, { type TabItem } from '$lib/components/ui/Tabs.svelte';
  import Toggle from '$lib/components/ui/Toggle.svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { notify } from '$lib/stores/toast';
  import { number, titleCase } from '$lib/utils/format';

  type ConfigSection = 'institution' | 'thresholds' | 'meals' | 'branches';
  type ConfigEnvelope<T> = { section: string; data: T };
  type InstitutionConfig = {
    name: string;
    code: string;
    timezone: string;
    address?: string;
    phone?: string;
    email?: string;
    website?: string;
  };
  type ThresholdConfig = {
    waste_threshold_grams: number;
    warning_threshold_grams: number;
    penalty_threshold_grams: number;
    improvement_target_pct: number;
    reset_duration_days: number;
    warning_count_for_penalty: number;
  };
  type MealTiming = {
    name: string;
    display_name: string;
    start_time: string;
    end_time: string;
    is_active: boolean;
    order_index: number;
  };
  type Branch = { code: string; name: string };

  const tabs: TabItem[] = [
    { id: 'institution', label: 'Institution' },
    { id: 'thresholds', label: 'Thresholds' },
    { id: 'meals', label: 'Meal Schedule' },
    { id: 'branches', label: 'Branches' }
  ];
  const timezoneOptions = [
    'Asia/Kolkata',
    'UTC',
    'Asia/Dubai',
    'Asia/Singapore',
    'Europe/London',
    'America/New_York'
  ];

  const defaults = {
    institution: {
      name: '',
      code: '',
      timezone: 'Asia/Kolkata',
      address: '',
      phone: '',
      email: '',
      website: ''
    } satisfies InstitutionConfig,
    thresholds: {
      waste_threshold_grams: 150,
      warning_threshold_grams: 100,
      penalty_threshold_grams: 200,
      improvement_target_pct: 25,
      reset_duration_days: 30,
      warning_count_for_penalty: 5
    } satisfies ThresholdConfig,
    meals: [
      {
        name: 'breakfast',
        display_name: 'Breakfast',
        start_time: '07:00',
        end_time: '09:30',
        is_active: true,
        order_index: 0
      },
      {
        name: 'lunch',
        display_name: 'Lunch',
        start_time: '12:00',
        end_time: '14:30',
        is_active: true,
        order_index: 1
      },
      {
        name: 'dinner',
        display_name: 'Dinner',
        start_time: '19:00',
        end_time: '21:30',
        is_active: true,
        order_index: 2
      }
    ] satisfies MealTiming[],
    branches: [] as Branch[]
  };

  let activeTab: ConfigSection = 'institution';
  let loading = true;
  let error = '';
  let saving: Record<ConfigSection, boolean> = {
    institution: false,
    thresholds: false,
    meals: false,
    branches: false
  };
  let snapshots: Record<ConfigSection, string> = {
    institution: '',
    thresholds: '',
    meals: '',
    branches: ''
  };
  let resetTarget: ConfigSection | null = null;

  let institution: InstitutionConfig = clone(defaults.institution);
  let thresholds: ThresholdConfig = clone(defaults.thresholds);
  let meals: MealTiming[] = clone(defaults.meals);
  let branches: Branch[] = clone(defaults.branches);

  $: thresholdSpread = Math.max(
    1,
    thresholds.penalty_threshold_grams - thresholds.warning_threshold_grams
  );
  $: dirtyCount = (Object.keys(snapshots) as ConfigSection[]).filter(
    (section) => isDirty(section)
  ).length;

  function clone<T>(value: T): T {
    return JSON.parse(JSON.stringify(value)) as T;
  }

  function dataOf<T>(payload: T | ConfigEnvelope<T>, fallback: T): T {
    if (payload && typeof payload === 'object' && 'data' in payload) {
      return { ...fallback, ...((payload as ConfigEnvelope<T>).data ?? {}) };
    }
    return { ...fallback, ...(payload as T) };
  }

  function remember(section: ConfigSection) {
    snapshots = { ...snapshots, [section]: JSON.stringify(payload(section)) };
  }

  function isDirty(section: ConfigSection) {
    return snapshots[section] !== JSON.stringify(payload(section));
  }

  function payload(section: ConfigSection) {
    if (section === 'institution') return institution;
    if (section === 'thresholds') return thresholds;
    if (section === 'meals') return meals;
    return branches;
  }

  function markDirty() {
    snapshots = { ...snapshots };
  }

  async function fetchSection(section: ConfigSection) {
    if (section === 'institution') {
      institution = dataOf(
        await api.get<ConfigEnvelope<InstitutionConfig>>('/config/institution'),
        defaults.institution
      );
    } else if (section === 'thresholds') {
      thresholds = dataOf(
        await api.get<ThresholdConfig>('/config/thresholds'),
        defaults.thresholds
      );
    } else if (section === 'meals') {
      meals = await api.get<MealTiming[]>('/config/meals');
    } else {
      branches = await api.get<Branch[]>('/config/branches');
    }
    remember(section);
  }

  async function loadConfig() {
    loading = true;
    error = '';
    try {
      const [institutionData, thresholdData, mealData, branchData] =
        await Promise.all([
          api.get<ConfigEnvelope<InstitutionConfig>>('/config/institution'),
          api.get<ThresholdConfig>('/config/thresholds'),
          api.get<MealTiming[]>('/config/meals'),
          api.get<Branch[]>('/config/branches')
        ]);
      institution = dataOf(institutionData, defaults.institution);
      thresholds = dataOf(thresholdData, defaults.thresholds);
      meals = mealData;
      branches = branchData;
      (Object.keys(snapshots) as ConfigSection[]).forEach(remember);
    } catch (err) {
      error =
        err instanceof Error ? err.message : 'Could not load configuration.';
    } finally {
      loading = false;
    }
  }

  function validateSection(section: ConfigSection) {
    if (section === 'institution' && (!institution.name || !institution.code)) {
      notify('Institution name and code are required.', 'error');
      return false;
    }
    if (
      section === 'thresholds' &&
      thresholds.penalty_threshold_grams < thresholds.warning_threshold_grams
    ) {
      notify(
        'Penalty threshold must be greater than warning threshold.',
        'error'
      );
      return false;
    }
    if (
      section === 'meals' &&
      meals.some(
        (meal) => !meal.display_name || meal.start_time >= meal.end_time
      )
    ) {
      notify('Every meal needs a label and a valid time window.', 'error');
      return false;
    }
    if (
      section === 'branches' &&
      branches.some((item) => !item.code || !item.name)
    ) {
      notify('Every branch needs a code and name.', 'error');
      return false;
    }
    return true;
  }

  async function saveSection(section: ConfigSection) {
    if (!validateSection(section)) return;
    saving = { ...saving, [section]: true };
    try {
      if (section === 'institution') {
        await api.patch('/config/institution', { data: institution });
      } else if (section === 'thresholds') {
        await api.patch('/config/thresholds', thresholds);
      } else if (section === 'meals') {
        await api.put('/config/meals', meals);
      } else {
        await api.put(
          '/config/branches',
          branches.map((branch) => ({
            code: branch.code.trim().toUpperCase(),
            name: branch.name.trim()
          }))
        );
      }
      notify(`${titleCase(section)} saved.`, 'success');
      await fetchSection(section);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save config.',
        'error'
      );
    } finally {
      saving = { ...saving, [section]: false };
    }
  }

  async function saveAll() {
    for (const section of tabs.map((tab) => tab.id as ConfigSection)) {
      if (isDirty(section)) await saveSection(section);
    }
  }

  async function resetSection() {
    if (!resetTarget) return;
    const section = resetTarget;
    resetTarget = null;
    try {
      await api.post(`/config/reset/${section}`);
      await fetchSection(section);
      notify(`${titleCase(section)} reset to defaults.`, 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not reset defaults.',
        'error'
      );
    }
  }

  function updateMeal(index: number, patch: Partial<MealTiming>) {
    meals = meals.map((meal, itemIndex) =>
      itemIndex === index ? { ...meal, ...patch } : meal
    );
    markDirty();
  }

  function updateBranch(index: number, patch: Partial<Branch>) {
    branches = branches.map((branch, itemIndex) =>
      itemIndex === index ? { ...branch, ...patch } : branch
    );
    markDirty();
  }

  function addBranch() {
    branches = [...branches, { code: '', name: '' }];
    markDirty();
  }

  function removeBranch(index: number) {
    branches = branches.filter((_, itemIndex) => itemIndex !== index);
    markDirty();
  }

  onMount(loadConfig);
</script>

<svelte:head><title>Configuration | CleanPlates</title></svelte:head>

<PageHeader
  label="Configuration"
  title="Institution configuration"
  description="Manage institution identity, waste thresholds, meal windows, and branch catalogs."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={loadConfig}
      disabled={loading}
      id="btn-refresh-config"
    >
      <RotateCcw size={16} />Refresh
    </Button>
    <Button
      on:click={saveAll}
      disabled={dirtyCount === 0 || loading}
      id="btn-save-all-config"
    >
      <Save size={16} />Save all
    </Button>
  </svelte:fragment>
</PageHeader>

{#if error}
  <Card>
    <div
      class="rounded-md border border-down/30 bg-down/10 p-4 text-sm text-down"
    >
      {error}
    </div>
  </Card>
{:else}
  <div class="space-y-5">
    <Card>
      <Tabs
        {tabs}
        active={activeTab}
        onChange={(id) => (activeTab = id as ConfigSection)}
      />
    </Card>

    <Card
      title={tabs.find((tab) => tab.id === activeTab)?.label ?? 'Configuration'}
      description={isDirty(activeTab)
        ? 'Unsaved changes are waiting on this section.'
        : 'Current backend values are in sync.'}
    >
      <svelte:fragment slot="actions">
        <Button
          variant="secondary"
          on:click={() => (resetTarget = activeTab)}
          disabled={loading}
          id={`btn-reset-${activeTab}`}
        >
          <RotateCcw size={16} />Reset
        </Button>
        <Button
          on:click={() => saveSection(activeTab)}
          disabled={loading || saving[activeTab] || !isDirty(activeTab)}
          id={`btn-save-${activeTab}`}
        >
          <Save size={16} />Save
        </Button>
      </svelte:fragment>

      {#if loading}
        <div class="h-96 skeleton"></div>
      {:else if activeTab === 'institution'}
        <div class="grid gap-4 lg:grid-cols-2">
          <label>
            <span class="form-label">Institution name</span>
            <input
              class="input-field"
              bind:value={institution.name}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Institution code</span>
            <input
              class="input-field"
              bind:value={institution.code}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Timezone</span>
            <select
              class="select-field"
              bind:value={institution.timezone}
              on:change={markDirty}
            >
              {#each timezoneOptions as zone}
                <option value={zone}>{zone}</option>
              {/each}
            </select>
          </label>
          <label>
            <span class="form-label">Email</span>
            <input
              class="input-field"
              type="email"
              bind:value={institution.email}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Phone</span>
            <input
              class="input-field"
              bind:value={institution.phone}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Website</span>
            <input
              class="input-field"
              bind:value={institution.website}
              on:input={markDirty}
            />
          </label>
          <label class="lg:col-span-2">
            <span class="form-label">Address</span>
            <textarea
              class="textarea-field min-h-28"
              bind:value={institution.address}
              on:input={markDirty}
            ></textarea>
          </label>
        </div>
      {:else if activeTab === 'thresholds'}
        <div class="grid gap-4 lg:grid-cols-3">
          <label>
            <span class="form-label">Daily waste threshold (g)</span>
            <input
              class="input-field"
              type="number"
              min="0"
              bind:value={thresholds.waste_threshold_grams}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Warning threshold (g)</span>
            <input
              class="input-field"
              type="number"
              min="0"
              bind:value={thresholds.warning_threshold_grams}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Penalty threshold (g)</span>
            <input
              class="input-field"
              type="number"
              min="0"
              bind:value={thresholds.penalty_threshold_grams}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Improvement target (%)</span>
            <input
              class="input-field"
              type="number"
              min="0"
              max="100"
              bind:value={thresholds.improvement_target_pct}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Reset duration (days)</span>
            <input
              class="input-field"
              type="number"
              min="1"
              bind:value={thresholds.reset_duration_days}
              on:input={markDirty}
            />
          </label>
          <label>
            <span class="form-label">Warnings before penalty</span>
            <input
              class="input-field"
              type="number"
              min="1"
              bind:value={thresholds.warning_count_for_penalty}
              on:input={markDirty}
            />
          </label>
        </div>
        <div class="mt-5 rounded-lg border border-border bg-elevated p-4">
          <div class="mb-3 flex flex-wrap justify-between gap-3 text-sm">
            <span class="text-up"
              >OK below {number(thresholds.warning_threshold_grams)}g</span
            >
            <span class="text-primary">
              Warning span {number(thresholdSpread)}g
            </span>
            <span class="text-down"
              >Penalty from {number(thresholds.penalty_threshold_grams)}g</span
            >
          </div>
          <div
            class="grid h-3 overflow-hidden rounded-sm sm:grid-cols-[1fr_1fr_1fr]"
          >
            <div class="bg-up"></div>
            <div class="bg-primary"></div>
            <div class="bg-down"></div>
          </div>
        </div>
      {:else if activeTab === 'meals'}
        <div class="grid gap-4 xl:grid-cols-3">
          {#each meals as meal, index}
            <div class="rounded-lg border border-border bg-elevated p-4">
              <div class="mb-4 flex items-center justify-between gap-3">
                <h3 class="font-semibold text-body">{titleCase(meal.name)}</h3>
                <Toggle
                  value={meal.is_active}
                  label="Active"
                  onChange={(value) => updateMeal(index, { is_active: value })}
                />
              </div>
              <div class="space-y-3">
                <label>
                  <span class="form-label">Label</span>
                  <input
                    class="input-field"
                    value={meal.display_name}
                    on:input={(event) =>
                      updateMeal(index, {
                        display_name: event.currentTarget.value
                      })}
                  />
                </label>
                <div class="grid gap-3 sm:grid-cols-2">
                  <label>
                    <span class="form-label">Start</span>
                    <input
                      class="input-field"
                      type="time"
                      value={meal.start_time}
                      on:change={(event) =>
                        updateMeal(index, {
                          start_time: event.currentTarget.value
                        })}
                    />
                  </label>
                  <label>
                    <span class="form-label">End</span>
                    <input
                      class="input-field"
                      type="time"
                      value={meal.end_time}
                      on:change={(event) =>
                        updateMeal(index, {
                          end_time: event.currentTarget.value
                        })}
                    />
                  </label>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="mb-4 flex justify-end">
          <Button on:click={addBranch} id="btn-add-branch">
            <Plus size={16} />Add branch
          </Button>
        </div>
        {#if branches.length === 0}
          <EmptyState
            title="No branches"
            message="Add the first branch to begin."
          />
        {:else}
          <div class="overflow-auto rounded-lg border border-border">
            <table>
              <thead class="bg-elevated">
                <tr>
                  <th class="th">Code</th>
                  <th class="th">Name</th>
                  <th class="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {#each branches as branch, index}
                  <tr>
                    <td class="td">
                      <input
                        class="input-field"
                        value={branch.code}
                        on:input={(event) =>
                          updateBranch(index, {
                            code: event.currentTarget.value.toUpperCase()
                          })}
                      />
                    </td>
                    <td class="td">
                      <input
                        class="input-field"
                        value={branch.name}
                        on:input={(event) =>
                          updateBranch(index, {
                            name: event.currentTarget.value
                          })}
                      />
                    </td>
                    <td class="td text-right">
                      <button
                        class="icon-btn"
                        type="button"
                        aria-label="Remove branch"
                        on:click={() => removeBranch(index)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}
    </Card>
  </div>
{/if}

<ConfirmDialog
  open={!!resetTarget}
  title="Reset section"
  message={`Reset ${titleCase(resetTarget ?? '')} to backend defaults? This cannot be undone.`}
  confirmLabel="Reset"
  danger
  onCancel={() => (resetTarget = null)}
  onConfirm={resetSection}
/>
