<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Database,
    Download,
    KeyRound,
    Plus,
    RefreshCw,
    Save,
    Upload,
    UserCog
  } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { User } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import {
    dateTime,
    fileSize,
    number,
    pct,
    titleCase
  } from '$lib/utils/format';
  import { notify } from '$lib/stores/toast';

  type Section = 'users' | 'security' | 'backup' | 'appearance' | 'maintenance';
  type Backup = {
    id: string;
    filename: string;
    file_size?: number | null;
    backup_type: string;
    status: string;
    created_at: string;
  };

  const sections: Section[] = [
    'users',
    'security',
    'backup',
    'appearance',
    'maintenance'
  ];

  let activeSection: Section = 'users';
  let loading = true;
  let users: User[] = [];
  let backups: Backup[] = [];
  let security: Record<string, unknown> = {};
  let securityJson = '{}';
  let appearance = {
    theme: 'light',
    logo_path: '',
    primary_color: '#188a6b',
    institution_display_name: ''
  };
  let systemInfo: Record<string, unknown> = {};
  let userOpen = false;
  let userForm = { name: '', email: '', role: 'mess_admin', password: '' };
  let logoFile: File | null = null;
  let restoreFile: File | null = null;

  async function loadSettings() {
    loading = true;
    try {
      const [userData, backupData, appearanceData, systemData] =
        await Promise.all([
          api.get<User[]>('/settings/users').catch(() => []),
          api.get<Backup[]>('/settings/backups').catch(() => []),
          api
            .get<typeof appearance>('/settings/appearance')
            .catch(() => appearance),
          api
            .get<Record<string, unknown>>('/settings/maintenance/system-info')
            .catch(() => ({}))
        ]);
      users = userData;
      backups = backupData;
      appearance = { ...appearance, ...appearanceData };
      systemInfo = systemData;
      security = await api
        .get<Record<string, unknown>>('/settings/security')
        .catch(() => ({}));
      securityJson = JSON.stringify(security, null, 2);
    } finally {
      loading = false;
    }
  }

  async function createUser() {
    try {
      await api.post('/settings/users', {
        ...userForm,
        password: userForm.password || null
      });
      notify('User created.', 'success');
      userOpen = false;
      userForm = { name: '', email: '', role: 'mess_admin', password: '' };
      await loadSettings();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not create user.',
        'error'
      );
    }
  }

  async function deactivate(user: User) {
    if (!window.confirm(`Deactivate ${user.email}?`)) return;
    await api.post(`/settings/users/${user.id}/deactivate`);
    notify('User deactivated.', 'success');
    await loadSettings();
  }

  async function resetPassword(user: User) {
    const result = await api.post<{ temp_password: string; message: string }>(
      `/settings/users/${user.id}/reset-password`
    );
    notify(`Temporary password: ${result.temp_password}`, 'info');
  }

  async function saveSecurity() {
    if (
      !window.confirm(
        'Save security settings? Invalid values (e.g. lockout_duration_minutes: 0) may affect all user logins.'
      )
    )
      return;
    try {
      security = JSON.parse(securityJson);
      await api.patch('/settings/security', security);
      notify('Security settings saved.', 'success');
    } catch (err) {
      notify(
        err instanceof Error
          ? err.message
          : 'Could not save security settings.',
        'error'
      );
    }
  }

  async function backupNow() {
    await api.post('/settings/backups');
    notify('Backup started.', 'success');
    await loadSettings();
  }

  async function downloadBackup(backup: Backup) {
    await api.download(
      `/settings/backups/${backup.id}/download`,
      backup.filename
    );
  }

  async function restoreBackup() {
    if (!restoreFile) {
      notify('Choose a backup file first.', 'error');
      return;
    }
    if (!window.confirm('Restore this backup? The backend may restart.'))
      return;
    await api.upload('/settings/backups/restore', 'backup_file', restoreFile);
    notify('Restore queued.', 'success');
  }

  async function saveAppearance() {
    await api.patch('/settings/appearance', appearance);
    notify('Appearance saved.', 'success');
  }

  async function uploadLogo() {
    if (!logoFile) {
      notify('Choose a logo file first.', 'error');
      return;
    }
    const result = await api.upload<{ logo_url: string }>(
      '/settings/appearance/logo',
      'image_file',
      logoFile
    );
    appearance.logo_path = result.logo_url;
    notify('Logo uploaded.', 'success');
  }

  async function clearCache() {
    const result = await api.post<{ keys_removed: number }>(
      '/settings/maintenance/clear-cache'
    );
    notify(`Cleared ${number(result.keys_removed)} cache keys.`, 'success');
  }

  async function optimizeDb() {
    const result = await api.post<{ freed_mb: number }>(
      '/settings/maintenance/optimize-db'
    );
    notify(
      `Optimized database, freed ${number(result.freed_mb)} MB.`,
      'success'
    );
  }

  async function exportAll() {
    await api.download(
      '/settings/maintenance/export-all',
      'cleanplates-export.zip'
    );
  }

  onMount(loadSettings);
</script>

<svelte:head><title>Settings | CleanPlates</title></svelte:head>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <p class="label">Settings</p>
    <h2 class="mt-1 text-2xl font-semibold text-body">
      Users, security, backup, and maintenance
    </h2>
  </div>
  <Button variant="secondary" on:click={loadSettings}
    ><RefreshCw size={16} />Refresh</Button
  >
</div>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Users"
    value={number(users.length)}
    helper="Admin and operators"
    ><svelte:fragment slot="icon"><UserCog size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Backups"
    value={number(backups.length)}
    helper="Stored archives"
    ><svelte:fragment slot="icon"><Database size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="CPU"
    value={pct(Number(systemInfo.cpu_usage_pct ?? 0))}
    helper="System info"
    ><svelte:fragment slot="icon"><Database size={19} /></svelte:fragment
    ></StatCard
  >
  <StatCard
    title="Disk"
    value={pct(Number(systemInfo.disk_usage_pct ?? 0))}
    helper={`${number(systemInfo.db_size_mb as number)} MB DB`}
    ><svelte:fragment slot="icon"><Database size={19} /></svelte:fragment
    ></StatCard
  >
</div>

<div class="mt-5 grid gap-5 lg:grid-cols-[240px_1fr]">
  <Card title="Settings">
    <nav class="space-y-1">
      {#each sections as section}<button
          class={`w-full rounded-md px-3 py-2 text-left text-sm font-semibold ${activeSection === section ? 'bg-primary text-ink' : 'text-muted hover:bg-elevated hover:text-body'}`}
          on:click={() => (activeSection = section)}
          >{titleCase(section)}</button
        >{/each}
    </nav>
  </Card>

  <Card title={titleCase(activeSection)}>
    {#if loading}
      <div class="h-96 animate-pulse rounded-lg bg-elevated"></div>
    {:else if activeSection === 'users'}
      <div class="mb-4 flex justify-end">
        <Button on:click={() => (userOpen = true)} id="btn-add-user"
          ><Plus size={16} />Add user</Button
        >
      </div>
      {#if users.length === 0}<EmptyState title="No users" />{:else}
        <div class="overflow-auto">
          <table>
            <thead class="bg-elevated"
              ><tr
                ><th class="th">Name</th><th class="th">Email</th><th class="th"
                  >Role</th
                ><th class="th">Last login</th><th class="th">Actions</th></tr
              ></thead
            ><tbody
              >{#each users as user}<tr
                  ><td class="td">{user.name}</td><td class="td"
                    >{user.email}</td
                  ><td class="td"><StatusBadge value={user.role} compact /></td
                  ><td class="td">{dateTime(user.last_login)}</td><td class="td"
                    ><div class="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        on:click={() => resetPassword(user)}
                        id={`btn-reset-pwd-${user.id}`}>Reset</Button
                      ><Button
                        size="sm"
                        variant="danger"
                        on:click={() => deactivate(user)}
                        id={`btn-deactivate-user-${user.id}`}>Deactivate</Button
                      >
                    </div></td
                  ></tr
                >{/each}</tbody
            >
          </table>
        </div>
      {/if}
    {:else if activeSection === 'security'}
      <label
        ><span class="label">Security JSON</span><textarea
          class="textarea-field mt-2 min-h-[420px] w-full py-3 font-mono text-xs"
          bind:value={securityJson}
        ></textarea></label
      >
      <div class="mt-4 flex justify-end">
        <Button on:click={saveSecurity} id="btn-save-security"
          ><Save size={16} />Save security</Button
        >
      </div>
    {:else if activeSection === 'backup'}
      <div class="mb-4 flex flex-wrap justify-between gap-3">
        <div class="flex gap-2">
          <Button on:click={backupNow} id="btn-backup-now">Backup now</Button
          ><Button
            variant="secondary"
            on:click={restoreBackup}
            id="btn-restore-backup">Restore backup</Button
          >
        </div>
        <input
          class="input-field py-2"
          type="file"
          on:change={(event) =>
            (restoreFile = event.currentTarget.files?.[0] ?? null)}
        />
      </div>
      {#if backups.length === 0}<EmptyState title="No backups" />{:else}
        <div class="space-y-3">
          {#each backups as backup}<div
              class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border p-4"
            >
              <div>
                <p class="font-semibold">{backup.filename}</p>
                <p class="mt-1 text-sm text-muted">
                  {fileSize(backup.file_size)} · {dateTime(backup.created_at)}
                </p>
              </div>
              <div class="flex gap-2">
                <StatusBadge value={backup.status} /><Button
                  size="sm"
                  variant="secondary"
                  on:click={() => downloadBackup(backup)}
                  id={`btn-download-backup-${backup.id}`}
                  ><Download size={14} />Download</Button
                >
              </div>
            </div>{/each}
        </div>
      {/if}
    {:else if activeSection === 'appearance'}
      <div class="grid gap-3 md:grid-cols-2">
        <label
          ><span class="label">Theme</span><select
            class="select-field mt-2 w-full"
            bind:value={appearance.theme}
            id="btn-toggle-theme"
            ><option>light</option><option>dark</option></select
          ></label
        ><label
          ><span class="label">Primary color</span><input
            class="input-field mt-2 w-full"
            type="color"
            bind:value={appearance.primary_color}
          /></label
        ><label
          ><span class="label">Display name</span><input
            class="input-field mt-2 w-full"
            bind:value={appearance.institution_display_name}
          /></label
        ><label
          ><span class="label">Logo</span><input
            class="input-field mt-2 w-full py-2"
            type="file"
            accept="image/*"
            on:change={(event) =>
              (logoFile = event.currentTarget.files?.[0] ?? null)}
          /></label
        >
      </div>
      {#if appearance.logo_path}<img
          class="mt-4 h-20 rounded-md border border-border object-contain p-2"
          src={appearance.logo_path}
          alt="Institution logo"
        />{/if}
      <div class="mt-4 flex justify-end gap-2">
        <Button variant="secondary" on:click={uploadLogo} id="btn-upload-logo"
          ><Upload size={16} />Upload logo</Button
        ><Button on:click={saveAppearance}>Save appearance</Button>
      </div>
    {:else}
      <div class="grid gap-4 md:grid-cols-2">
        <Button variant="secondary" on:click={clearCache} id="btn-clear-cache"
          >Clear cache</Button
        ><Button variant="secondary" on:click={optimizeDb} id="btn-optimize-db"
          >Optimize DB</Button
        ><Button on:click={exportAll} id="btn-export-all"
          ><Download size={16} />Export all data</Button
        >
      </div>
      <pre
        class="mt-5 max-h-96 overflow-auto rounded-lg bg-canvas p-4 text-xs text-body">{JSON.stringify(
          systemInfo,
          null,
          2
        )}</pre>
    {/if}
  </Card>
</div>

<Modal open={userOpen} title="Create user" on:close={() => (userOpen = false)}>
  <form class="space-y-3" on:submit|preventDefault={createUser}>
    <label
      ><span class="label">Name</span><input
        class="input-field mt-2 w-full"
        bind:value={userForm.name}
        required
      /></label
    >
    <label
      ><span class="label">Email</span><input
        class="input-field mt-2 w-full"
        type="email"
        bind:value={userForm.email}
        required
      /></label
    >
    <label
      ><span class="label">Role</span><select
        class="select-field mt-2 w-full"
        bind:value={userForm.role}
        ><option>super_admin</option><option>institution_admin</option><option
          >mess_admin</option
        ><option>analytics_viewer</option><option>staff_operator</option
        ></select
      ></label
    >
    <label
      ><span class="label">Password</span><input
        class="input-field mt-2 w-full"
        type="password"
        bind:value={userForm.password}
      /></label
    >
    <div class="flex justify-end gap-2">
      <Button
        variant="secondary"
        type="button"
        on:click={() => (userOpen = false)}>Cancel</Button
      ><Button type="submit">Create user</Button>
    </div>
  </form>
</Modal>
