<script lang="ts">
  import { onMount } from 'svelte';
  import { Eye, Plus, RotateCcw, Save, Trash2 } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import { dateTime, titleCase } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type Section =
    | 'institution'
    | 'device'
    | 'thresholds'
    | 'meals'
    | 'branches'
    | 'templates'
    | 'permissions'
    | 'system';
  type Template = {
    id: string;
    name: string;
    type: string;
    subject: string;
    body_html: string;
    variables: string[];
    is_default: boolean;
  };
  type Role = {
    id: string;
    name: string;
    description?: string | null;
    permissions: Record<string, unknown>;
    is_system: boolean;
  };

  const sections: Section[] = [
    'institution',
    'device',
    'thresholds',
    'meals',
    'branches',
    'templates',
    'permissions',
    'system'
  ];

  let activeSection: Section = 'institution';
  let loading = true;
  let error = '';
  let original = '';
  let draft = '';
  let templates: Template[] = [];
  let roles: Role[] = [];
  let auditEvents: Array<Record<string, unknown>> = [];
  let templateOpen = false;
  let previewOpen = false;
  let previewHtml = '';
  let selectedTemplate: Template | null = null;
  let templateForm = {
    name: '',
    type: 'warning',
    subject: '',
    body_html: '',
    variables: ''
  };
  let selectedRoleId = '';
  let roleDraft = '';

  $: hasChanges = draft !== original;

  function pretty(data: unknown) {
    return JSON.stringify(data, null, 2);
  }

  async function loadSection(section = activeSection) {
    activeSection = section;
    loading = true;
    error = '';
    try {
      if (section === 'templates') {
        templates = await api.get<Template[]>('/templates');
      } else if (section === 'permissions') {
        roles = await api.get<Role[]>('/roles');
        selectedRoleId = roles[0]?.id ?? '';
        roleDraft = pretty(roles[0]?.permissions ?? {});
      } else {
        const raw = await api.get<unknown>(`/config/${section}`);
        // institution and device wrap their value in { data: ... }; others return flat
        const data =
          section === 'institution' || section === 'device'
            ? (raw as { data: unknown }).data
            : raw;
        original = pretty(data);
        draft = original;
      }
      const audit = await api
        .get<{
          items: Array<Record<string, unknown>>;
        }>('/audit', { resource_type: 'config', size: 5 })
        .catch(() => ({ items: [] }));
      auditEvents = audit.items;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load config';
    } finally {
      loading = false;
    }
  }

  async function saveConfig() {
    try {
      const parsed = JSON.parse(draft);
      if (activeSection === 'institution' || activeSection === 'device')
        await api.patch(`/config/${activeSection}`, { data: parsed });
      else if (activeSection === 'meals' || activeSection === 'branches')
        await api.put(`/config/${activeSection}`, parsed);
      else if (activeSection === 'thresholds' || activeSection === 'system')
        await api.patch(`/config/${activeSection}`, parsed);
      notify('Configuration saved.', 'success');
      await loadSection(activeSection);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Invalid JSON or save failed.',
        'error'
      );
    }
  }

  async function resetDefaults() {
    if (!window.confirm(`Reset ${activeSection} to defaults?`)) return;
    try {
      await api.post(`/config/reset/${activeSection}`);
      notify('Defaults restored.', 'success');
      await loadSection(activeSection);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not reset defaults.',
        'error'
      );
    }
  }

  function openTemplate(template: Template | null = null) {
    selectedTemplate = template;
    templateForm = {
      name: template?.name ?? '',
      type: template?.type ?? 'warning',
      subject: template?.subject ?? '',
      body_html: template?.body_html ?? '',
      variables: template?.variables?.join(', ') ?? ''
    };
    templateOpen = true;
  }

  async function saveTemplate() {
    const body = {
      ...templateForm,
      variables: templateForm.variables
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
    };
    try {
      if (selectedTemplate)
        await api.patch(`/templates/${selectedTemplate.id}`, body);
      else await api.post('/templates', body);
      notify('Template saved.', 'success');
      templateOpen = false;
      await loadSection('templates');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save template.',
        'error'
      );
    }
  }

  async function previewTemplate(template: Template) {
    try {
      const result = await api.post<{ html: string }>(
        `/templates/${template.id}/preview`,
        { variables: {} }
      );
      previewHtml = result.html;
      previewOpen = true;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not preview template.',
        'error'
      );
    }
  }

  async function deleteTemplate(template: Template) {
    if (!window.confirm(`Delete ${template.name}?`)) return;
    await api.delete(`/templates/${template.id}`);
    await loadSection('templates');
  }

  async function saveRole() {
    const role = roles.find((item) => item.id === selectedRoleId);
    if (!role) return;
    try {
      await api.patch(`/roles/${role.id}`, {
        permissions: JSON.parse(roleDraft),
        description: role.description
      });
      notify('Role permissions saved.', 'success');
      await loadSection('permissions');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save role.',
        'error'
      );
    }
  }

  function selectRole() {
    const role = roles.find((item) => item.id === selectedRoleId);
    roleDraft = pretty(role?.permissions ?? {});
  }

  onMount(() => loadSection());
</script>

<svelte:head><title>Configuration | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Configuration</p>
    <h2 class="mt-1 text-2xl font-semibold text-ink">
      Institution, policy, templates, and permissions
    </h2>
  </div>
  {#if activeSection !== 'templates' && activeSection !== 'permissions'}
    <div class="flex flex-wrap gap-2">
      <Button
        variant="secondary"
        on:click={() => (draft = original)}
        disabled={!hasChanges}
        id="btn-discard-config">Discard</Button
      ><Button
        variant="secondary"
        on:click={resetDefaults}
        id="btn-reset-defaults"><RotateCcw size={16} />Defaults</Button
      ><Button on:click={saveConfig} disabled={!hasChanges} id="btn-save-config"
        ><Save size={16} />Save</Button
      >
    </div>
  {/if}
</div>

<div class="grid gap-5 lg:grid-cols-[260px_1fr]">
  <Card title="Config sections">
    <nav class="space-y-1">
      {#each sections as section}
        <button
          class={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm font-semibold ${activeSection === section ? 'bg-fresh text-white' : 'text-muted hover:bg-slate-100 hover:text-ink'}`}
          on:click={() => loadSection(section)}
          id={`nav-config-${section}`}
        >
          {titleCase(section)}
          {#if activeSection === section && hasChanges}<span
              class="h-2 w-2 rounded-full bg-amber"
            ></span>{/if}
        </button>
      {/each}
    </nav>
  </Card>

  <div class="space-y-5">
    <Card
      title={titleCase(activeSection)}
      description={activeSection === 'templates'
        ? 'Email templates with preview.'
        : activeSection === 'permissions'
          ? 'Role permission matrices.'
          : 'Edit JSON-backed configuration safely.'}
    >
      {#if error}<div
          class="rounded-md border border-coral/30 bg-coral/10 p-3 text-coral"
        >
          {error}
        </div>
      {:else if loading}<div
          class="h-96 animate-pulse rounded-lg bg-slate-100"
        ></div>
      {:else if activeSection === 'templates'}
        <div class="mb-4 flex justify-end">
          <Button on:click={() => openTemplate()} id="btn-create-template"
            ><Plus size={16} />Create template</Button
          >
        </div>
        {#if templates.length === 0}<EmptyState title="No templates" />{:else}
          <div class="space-y-3">
            {#each templates as template}<div
                class="rounded-lg border border-line p-4"
              >
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p class="font-semibold">{template.name}</p>
                    <p class="mt-1 text-sm text-muted">{template.subject}</p>
                  </div>
                  <StatusBadge
                    value={template.is_default ? 'default' : template.type}
                  />
                </div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => previewTemplate(template)}
                    id={`btn-preview-template-${template.id}`}
                    ><Eye size={14} />Preview</Button
                  ><Button
                    size="sm"
                    variant="secondary"
                    on:click={() => openTemplate(template)}
                    id={`btn-edit-template-${template.id}`}>Edit</Button
                  ><Button
                    size="sm"
                    variant="danger"
                    on:click={() => deleteTemplate(template)}
                    id={`btn-delete-template-${template.id}`}
                    ><Trash2 size={14} /></Button
                  >
                </div>
              </div>{/each}
          </div>
        {/if}
      {:else if activeSection === 'permissions'}
        {#if roles.length === 0}<EmptyState title="No roles" />{:else}
          <div class="space-y-3">
            <label
              ><span class="label">Role</span><select
                class="field mt-2 w-full"
                bind:value={selectedRoleId}
                on:change={selectRole}
                >{#each roles as role}<option value={role.id}
                    >{titleCase(role.name)}</option
                  >{/each}</select
              ></label
            ><label
              ><span class="label">Permissions JSON</span><textarea
                class="field mt-2 min-h-[360px] w-full py-3 font-mono text-xs"
                bind:value={roleDraft}
              ></textarea></label
            >
            <div class="flex justify-end">
              <Button on:click={saveRole} id="btn-edit-perms">Save role</Button>
            </div>
          </div>
        {/if}
      {:else}
        <textarea
          class="field min-h-[520px] w-full py-3 font-mono text-xs leading-6"
          bind:value={draft}
        ></textarea>
      {/if}
    </Card>

    <Card title="Recent config audit">
      {#if auditEvents.length === 0}<EmptyState
          title="No config audit events"
        />{:else}
        <div class="space-y-2">
          {#each auditEvents as event}<div
              class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line p-3 text-sm"
            >
              <span>{event.summary}</span><span class="text-muted"
                >{dateTime(String(event.created_at))}</span
              >
            </div>{/each}
        </div>
      {/if}
    </Card>
  </div>
</div>

<Modal
  open={templateOpen}
  title={selectedTemplate ? 'Edit template' : 'Create template'}
  wide
  on:close={() => (templateOpen = false)}
>
  <form
    class="grid gap-3 md:grid-cols-2"
    on:submit|preventDefault={saveTemplate}
  >
    <label
      ><span class="label">Name</span><input
        class="field mt-2 w-full"
        bind:value={templateForm.name}
        required
      /></label
    >
    <label
      ><span class="label">Type</span><input
        class="field mt-2 w-full"
        bind:value={templateForm.type}
        required
      /></label
    >
    <label class="md:col-span-2"
      ><span class="label">Subject</span><input
        class="field mt-2 w-full"
        bind:value={templateForm.subject}
        required
      /></label
    >
    <label class="md:col-span-2"
      ><span class="label">Body HTML</span><textarea
        class="field mt-2 min-h-56 w-full py-3"
        bind:value={templateForm.body_html}
        required
      ></textarea></label
    >
    <label class="md:col-span-2"
      ><span class="label">Variables</span><input
        class="field mt-2 w-full"
        bind:value={templateForm.variables}
        placeholder="student_name, warning_level"
      /></label
    >
    <div class="flex justify-end gap-2 md:col-span-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (templateOpen = false)}>Cancel</Button
      ><Button type="submit">Save template</Button>
    </div>
  </form>
</Modal>

<Modal
  open={previewOpen}
  title="Template preview"
  wide
  on:close={() => (previewOpen = false)}
>
  <iframe
    title="Template preview"
    class="h-[560px] w-full rounded-lg border border-line"
    srcdoc={previewHtml}
  ></iframe>
</Modal>
