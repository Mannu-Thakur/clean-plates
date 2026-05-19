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
  import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';
  import EmptyState from '$lib/components/ui/EmptyState.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import StatCard from '$lib/components/ui/StatCard.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import Tabs, { type TabItem } from '$lib/components/ui/Tabs.svelte';
  import Toggle from '$lib/components/ui/Toggle.svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { auth } from '$lib/stores/auth';
  import {
    applyTheme,
    normalizeTheme,
    readStoredTheme
  } from '$lib/stores/theme';
  import { notify } from '$lib/stores/toast';
  import {
    dateTime,
    fileSize,
    number,
    pct,
    titleCase
  } from '$lib/utils/format';

  type SettingsTab =
    | 'users'
    | 'security'
    | 'backups'
    | 'maintenance'
    | 'appearance';
  type SettingsUser = User & { created_at?: string | null };
  type Role = {
    id?: string;
    name: string;
    display_name?: string | null;
    description?: string | null;
  };
  type Backup = {
    id: string;
    filename: string;
    file_size?: number | null;
    backup_type: string;
    status: string;
    created_at: string;
  };
  type SecurityConfig = {
    access_token_expiry_minutes: number;
    refresh_token_expiry_days: number;
    min_password_length: number;
    require_uppercase: boolean;
    require_numbers: boolean;
    max_login_attempts: number;
    lockout_duration_minutes: number;
    session_timeout_minutes: number;
  };
  type AppearanceConfig = {
    theme: string;
    logo_path?: string | null;
    primary_color?: string;
    institution_display_name?: string | null;
  };
  type SystemInfo = {
    os_version?: string;
    python_version?: string;
    app_version?: string;
    db_size_mb?: number;
    uptime_seconds?: number;
    disk_usage_pct?: number;
    ram_usage_pct?: number;
    cpu_usage_pct?: number;
  };

  const tabs: TabItem[] = [
    { id: 'users', label: 'Users' },
    { id: 'security', label: 'Security' },
    { id: 'backups', label: 'Backups' },
    { id: 'maintenance', label: 'Maintenance' },
    { id: 'appearance', label: 'Appearance' }
  ];
  const defaultRoles = [
    'super_admin',
    'institution_admin',
    'mess_admin',
    'analytics_viewer',
    'staff_operator'
  ];
  const defaultSecurity: SecurityConfig = {
    access_token_expiry_minutes: 1440,
    refresh_token_expiry_days: 30,
    min_password_length: 8,
    require_uppercase: true,
    require_numbers: true,
    max_login_attempts: 5,
    lockout_duration_minutes: 15,
    session_timeout_minutes: 1440
  };
  const defaultAppearance: AppearanceConfig = {
    theme: 'dark',
    logo_path: null,
    primary_color: '#fcd535',
    institution_display_name: null
  };

  let activeTab: SettingsTab = 'users';
  let loading = true;
  let saving = false;
  let error = '';
  let users: SettingsUser[] = [];
  let roles: Role[] = [];
  let backups: Backup[] = [];
  let security: SecurityConfig = { ...defaultSecurity };
  let appearance: AppearanceConfig = { ...defaultAppearance };
  let systemInfo: SystemInfo = {};
  let logoFile: File | null = null;
  let uploadingLogo = false;
  let logoUploadKey = 0;
  let restoreFile: File | null = null;
  let userModalOpen = false;
  let editingUser: SettingsUser | null = null;
  let userForm = {
    name: '',
    email: '',
    role: 'mess_admin',
    password: ''
  };
  let deactivateTarget: SettingsUser | null = null;
  let resetPasswordTarget: SettingsUser | null = null;
  let tempPassword = '';
  let restoreConfirmOpen = false;
  let maintenanceConfirm: 'clear-cache' | 'optimize-db' | null = null;

  $: roleOptions = roles.length ? roles.map((role) => role.name) : defaultRoles;
  $: activeSuperAdmins = users.filter(
    (user) => user.role === 'super_admin' && user.is_active
  ).length;

  async function fetchUsers() {
    users = await api.get<SettingsUser[]>('/settings/users');
  }

  async function fetchRoles() {
    roles = await api.get<Role[]>('/roles/').catch(() => []);
  }

  async function fetchSecurity() {
    security = {
      ...defaultSecurity,
      ...(await api.get<SecurityConfig>('/settings/security'))
    };
  }

  async function fetchBackups() {
    backups = await api.get<Backup[]>('/settings/backups');
  }

  async function fetchAppearance() {
    const remoteAppearance = {
      ...defaultAppearance,
      ...(await api
        .get<AppearanceConfig>('/settings/appearance')
        .catch(() => ({})))
    };
    appearance = {
      ...remoteAppearance,
      theme: readStoredTheme() ?? normalizeTheme(remoteAppearance.theme)
    };
    applyTheme(appearance.theme);
  }

  async function fetchSystemInfo() {
    systemInfo = await api
      .get<SystemInfo>('/settings/maintenance/system-info')
      .catch(() => ({}));
  }

  async function loadSettings() {
    loading = true;
    error = '';
    try {
      await Promise.all([
        fetchUsers(),
        fetchRoles(),
        fetchSecurity(),
        fetchBackups(),
        fetchAppearance(),
        fetchSystemInfo()
      ]);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load settings.';
    } finally {
      loading = false;
    }
  }

  function openUserModal(user: SettingsUser | null = null) {
    editingUser = user;
    userForm = {
      name: user?.name ?? '',
      email: user?.email ?? '',
      role: user?.role ?? 'mess_admin',
      password: ''
    };
    userModalOpen = true;
  }

  async function createUser() {
    await api.post('/settings/users', {
      name: userForm.name,
      email: userForm.email,
      role: userForm.role,
      password: userForm.password || null
    });
  }

  async function updateUser() {
    if (!editingUser) return;
    await api.patch(`/settings/users/${editingUser.id}`, {
      name: userForm.name,
      email: userForm.email,
      role: userForm.role
    });
  }

  async function saveUser() {
    saving = true;
    try {
      if (editingUser) {
        await updateUser();
        notify('User updated.', 'success');
      } else {
        await createUser();
        notify(
          'User created. Temporary credentials were emailed if generated.',
          'success'
        );
      }
      userModalOpen = false;
      await fetchUsers();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save user.',
        'error'
      );
    } finally {
      saving = false;
    }
  }

  function canDeactivate(user: SettingsUser) {
    if (!user.is_active) return false;
    if (user.id === $auth.user?.id) return false;
    if (user.role === 'super_admin' && activeSuperAdmins <= 1) return false;
    return true;
  }

  async function deactivateUser() {
    if (!deactivateTarget) return;
    const target = deactivateTarget;
    deactivateTarget = null;
    try {
      await api.post(`/settings/users/${target.id}/deactivate`);
      notify('User deactivated.', 'success');
      await fetchUsers();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not deactivate user.',
        'error'
      );
    }
  }

  async function resetPassword() {
    if (!resetPasswordTarget) return;
    const target = resetPasswordTarget;
    resetPasswordTarget = null;
    try {
      const result = await api.post<{ temp_password: string; message: string }>(
        `/settings/users/${target.id}/reset-password`
      );
      tempPassword = result.temp_password;
      notify('Temporary password generated.', 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not reset password.',
        'error'
      );
    }
  }

  async function saveSecurity() {
    saving = true;
    try {
      await api.patch('/settings/security', security);
      notify('Security settings saved.', 'success');
      await fetchSecurity();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save security.',
        'error'
      );
    } finally {
      saving = false;
    }
  }

  async function triggerBackup() {
    try {
      await api.post('/settings/backups');
      notify('Backup queued.', 'success');
      await fetchBackups();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not queue backup.',
        'error'
      );
    }
  }

  async function downloadBackup(backup: Backup) {
    try {
      await api.download(
        `/settings/backups/${backup.id}/download`,
        backup.filename
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not download backup.',
        'error'
      );
    }
  }

  async function restoreBackup() {
    restoreConfirmOpen = false;
    if (!restoreFile) {
      notify('Choose a backup file first.', 'error');
      return;
    }
    try {
      await api.upload('/settings/backups/restore', 'backup_file', restoreFile);
      notify('Restore staged. The backend may restart to apply it.', 'success');
      restoreFile = null;
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not restore backup.',
        'error'
      );
    }
  }

  async function saveAppearance() {
    saving = true;
    try {
      await api.patch('/settings/appearance', {
        ...appearance,
        theme: normalizeTheme(appearance.theme),
        primary_color: appearance.primary_color ?? defaultAppearance.primary_color,
        institution_display_name: null
      });
      applyTheme(appearance.theme);
      notify('Theme saved.', 'success');
      await fetchAppearance();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not save appearance.',
        'error'
      );
    } finally {
      saving = false;
    }
  }

  async function uploadLogo(file = logoFile) {
    if (!file) {
      notify('Choose a logo file first.', 'error');
      return;
    }
    uploadingLogo = true;
    try {
      const result = await api.upload<{ logo_url: string }>(
        '/settings/appearance/logo',
        'image_file',
        file
      );
      appearance = { ...appearance, logo_path: result.logo_url };
      logoFile = null;
      logoUploadKey += 1;
      notify('Logo uploaded.', 'success');
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not upload logo.',
        'error'
      );
    } finally {
      uploadingLogo = false;
    }
  }

  async function runMaintenanceAction() {
    const action = maintenanceConfirm;
    maintenanceConfirm = null;
    try {
      if (action === 'clear-cache') {
        const result = await api.post<{ keys_removed: number }>(
          '/settings/maintenance/clear-cache'
        );
        notify(`Cleared ${number(result.keys_removed)} cache keys.`, 'success');
      } else if (action === 'optimize-db') {
        const result = await api.post<{ freed_mb: number }>(
          '/settings/maintenance/optimize-db'
        );
        notify(
          `Optimized database, freed ${number(result.freed_mb)} MB.`,
          'success'
        );
      }
      await fetchSystemInfo();
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Maintenance action failed.',
        'error'
      );
    }
  }

  async function exportAll() {
    try {
      await api.download(
        '/settings/maintenance/export-all',
        'cleanplates-export.zip'
      );
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Could not export data.',
        'error'
      );
    }
  }

  function setSecurity(patch: Partial<SecurityConfig>) {
    security = { ...security, ...patch };
  }

  function setAppearanceTheme(theme: string) {
    appearance = { ...appearance, theme };
    applyTheme(theme);
  }

  function formatSeconds(seconds: number | undefined) {
    const safe = Number(seconds ?? 0);
    if (safe < 3600) return `${Math.round(safe / 60)} min`;
    if (safe < 86400) return `${(safe / 3600).toFixed(1)} h`;
    return `${(safe / 86400).toFixed(1)} d`;
  }

  onMount(loadSettings);
</script>

<svelte:head><title>Settings | CleanPlates</title></svelte:head>

<PageHeader
  label="Settings"
  title="Application administration"
  description="Manage operators, security policy, backups, system maintenance, and branding."
>
  <svelte:fragment slot="actions">
    <Button
      variant="secondary"
      on:click={loadSettings}
      disabled={loading}
      id="btn-refresh-settings"
    >
      <RefreshCw size={16} />Refresh
    </Button>
  </svelte:fragment>
</PageHeader>

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  <StatCard
    title="Users"
    value={number(users.length)}
    helper="Admin and operators"
  >
    <svelte:fragment slot="icon"><UserCog size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Backups"
    value={number(backups.length)}
    helper="Stored archives"
  >
    <svelte:fragment slot="icon"><Database size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="CPU"
    value={pct(Number(systemInfo.cpu_usage_pct ?? 0))}
    helper="System load"
  >
    <svelte:fragment slot="icon"><Database size={19} /></svelte:fragment>
  </StatCard>
  <StatCard
    title="Disk"
    value={pct(Number(systemInfo.disk_usage_pct ?? 0))}
    helper={`${number(systemInfo.db_size_mb)} MB DB`}
  >
    <svelte:fragment slot="icon"><Database size={19} /></svelte:fragment>
  </StatCard>
</div>

{#if error}
  <Card class="mt-5">
    <div
      class="rounded-md border border-down/30 bg-down/10 p-4 text-sm text-down"
    >
      {error}
    </div>
  </Card>
{:else}
  <div class="mt-5 space-y-5">
    <Card>
      <Tabs
        {tabs}
        active={activeTab}
        onChange={(id) => (activeTab = id as SettingsTab)}
      />
    </Card>

    <Card title={tabs.find((tab) => tab.id === activeTab)?.label ?? 'Settings'}>
      {#if loading}
        <div class="h-96 skeleton"></div>
      {:else if activeTab === 'users'}
        <div class="mb-4 flex justify-end">
          <Button on:click={() => openUserModal()} id="btn-add-user">
            <Plus size={16} />Add user
          </Button>
        </div>
        {#if users.length === 0}
          <EmptyState title="No users" />
        {:else}
          <div class="overflow-auto rounded-lg border border-border">
            <table>
              <thead class="bg-elevated">
                <tr>
                  <th class="th">Name</th>
                  <th class="th">Email</th>
                  <th class="th">Role</th>
                  <th class="th">Status</th>
                  <th class="th">Last login</th>
                  <th class="th text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {#each users as user}
                  <tr>
                    <td class="td font-semibold">{user.name}</td>
                    <td class="td">{user.email}</td>
                    <td class="td"><StatusBadge value={user.role} compact /></td
                    >
                    <td class="td"
                      ><StatusBadge value={user.is_active} compact /></td
                    >
                    <td class="td">{dateTime(user.last_login)}</td>
                    <td class="td">
                      <div class="flex flex-wrap justify-end gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          on:click={() => openUserModal(user)}
                          id={`btn-edit-user-${user.id}`}
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          on:click={() => (resetPasswordTarget = user)}
                          id={`btn-reset-pwd-${user.id}`}
                        >
                          <KeyRound size={14} />Reset
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          disabled={!canDeactivate(user)}
                          on:click={() => (deactivateTarget = user)}
                          id={`btn-deactivate-user-${user.id}`}
                        >
                          Deactivate
                        </Button>
                      </div>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {:else if activeTab === 'security'}
        <div class="grid gap-4 lg:grid-cols-3">
          <label>
            <span class="form-label">Access token expiry (min)</span>
            <input
              class="input-field"
              type="number"
              min="5"
              bind:value={security.access_token_expiry_minutes}
            />
          </label>
          <label>
            <span class="form-label">Refresh token expiry (days)</span>
            <input
              class="input-field"
              type="number"
              min="1"
              bind:value={security.refresh_token_expiry_days}
            />
          </label>
          <label>
            <span class="form-label">Session timeout (min)</span>
            <input
              class="input-field"
              type="number"
              min="5"
              bind:value={security.session_timeout_minutes}
            />
          </label>
          <label>
            <span class="form-label">Minimum password length</span>
            <input
              class="input-field"
              type="number"
              min="8"
              bind:value={security.min_password_length}
            />
          </label>
          <label>
            <span class="form-label">Max login attempts</span>
            <input
              class="input-field"
              type="number"
              min="1"
              bind:value={security.max_login_attempts}
            />
          </label>
          <label>
            <span class="form-label">Lockout duration (min)</span>
            <input
              class="input-field"
              type="number"
              min="1"
              bind:value={security.lockout_duration_minutes}
            />
          </label>
        </div>
        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <div class="rounded-lg border border-border bg-elevated p-4">
            <Toggle
              value={security.require_uppercase}
              label="Require uppercase letters"
              onChange={(value) => setSecurity({ require_uppercase: value })}
            />
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <Toggle
              value={security.require_numbers}
              label="Require numbers"
              onChange={(value) => setSecurity({ require_numbers: value })}
            />
          </div>
        </div>
        <div class="mt-5 flex justify-end">
          <Button
            on:click={saveSecurity}
            disabled={saving}
            id="btn-save-security"
          >
            <Save size={16} />Save security
          </Button>
        </div>
      {:else if activeTab === 'backups'}
        <div class="mb-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
          <div class="rounded-lg border border-border bg-elevated p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-body">Manual backup</p>
                <p class="mt-1 text-sm text-muted">
                  Queue a database backup now.
                </p>
              </div>
              <Button on:click={triggerBackup} id="btn-backup-now">
                <Database size={16} />Create backup
              </Button>
            </div>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <FileUpload
              accept=".zip"
              maxSizeMb={250}
              label="Restore backup archive"
              onSelect={(file) => (restoreFile = file)}
            />
            <div class="mt-3 flex justify-end">
              <Button
                variant="danger"
                disabled={!restoreFile}
                on:click={() => (restoreConfirmOpen = true)}
                id="btn-restore-backup"
              >
                <Upload size={16} />Restore
              </Button>
            </div>
          </div>
        </div>
        {#if backups.length === 0}
          <EmptyState title="No backups" />
        {:else}
          <div class="space-y-3">
            {#each backups as backup}
              <div
                class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border p-4"
              >
                <div>
                  <p class="font-semibold">{backup.filename}</p>
                  <p class="mt-1 text-sm text-muted">
                    {titleCase(backup.backup_type)} - {fileSize(
                      backup.file_size
                    )} - {dateTime(backup.created_at)}
                  </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <StatusBadge value={backup.status} />
                  <Button
                    size="sm"
                    variant="secondary"
                    on:click={() => downloadBackup(backup)}
                    id={`btn-download-backup-${backup.id}`}
                  >
                    <Download size={14} />Download
                  </Button>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      {:else if activeTab === 'maintenance'}
        <div class="grid gap-4 lg:grid-cols-3">
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">App version</p>
            <p class="mt-2 font-mono text-lg font-semibold text-primary">
              {systemInfo.app_version ?? 'n/a'}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">Python</p>
            <p class="mt-2 font-mono text-lg font-semibold text-body">
              {systemInfo.python_version ?? 'n/a'}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">Uptime</p>
            <p class="mt-2 text-lg font-semibold text-body">
              {formatSeconds(systemInfo.uptime_seconds)}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">RAM</p>
            <p class="mt-2 text-lg font-semibold text-body">
              {pct(systemInfo.ram_usage_pct)}
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">Database size</p>
            <p class="mt-2 text-lg font-semibold text-body">
              {number(systemInfo.db_size_mb)} MB
            </p>
          </div>
          <div class="rounded-lg border border-border bg-elevated p-4">
            <p class="label">OS</p>
            <p class="mt-2 text-sm font-semibold text-body">
              {systemInfo.os_version ?? 'n/a'}
            </p>
          </div>
        </div>
        <div class="mt-5 flex flex-wrap gap-2">
          <Button
            variant="secondary"
            on:click={() => (maintenanceConfirm = 'clear-cache')}
            id="btn-clear-cache"
          >
            Clear cache
          </Button>
          <Button
            variant="secondary"
            on:click={() => (maintenanceConfirm = 'optimize-db')}
            id="btn-optimize-db"
          >
            Optimize DB
          </Button>
          <Button on:click={exportAll} id="btn-export-all">
            <Download size={16} />Export all data
          </Button>
        </div>
      {:else}
        <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(260px,360px)]">
          <div class="space-y-4">
            <div class="rounded-lg border border-border bg-elevated p-4">
              <Toggle
                value={appearance.theme === 'dark'}
                label={appearance.theme === 'dark' ? 'Dark mode' : 'Light mode'}
                onChange={(value) =>
                  setAppearanceTheme(value ? 'dark' : 'light')}
              />
            </div>
            <div
              class="rounded-lg border border-primary/30 bg-primary/10 p-4 text-sm text-primary"
            >
              Theme changes apply immediately. Save to keep this preference for
              future sessions.
            </div>
            <div class="flex justify-end sm:justify-start">
              <Button
                on:click={saveAppearance}
                disabled={saving}
                id="btn-save-appearance"
              >
                <Save size={16} />Save theme
              </Button>
            </div>
          </div>
          <div class="space-y-4">
            {#key logoUploadKey}
              <FileUpload
                accept=".png,.jpg,.jpeg,.webp,.gif,.svg"
                maxSizeMb={5}
                label="Upload institution logo"
                uploading={uploadingLogo}
                onSelect={(file) => {
                  logoFile = file;
                  uploadLogo(file);
                }}
                onClear={() => (logoFile = null)}
              />
            {/key}
            {#if appearance.logo_path}
              <img
                class="h-24 w-24 rounded-lg border border-border bg-elevated object-contain p-2"
                src={appearance.logo_path}
                alt="Institution logo"
              />
            {/if}
          </div>
        </div>
      {/if}
    </Card>
  </div>
{/if}

<Modal
  open={userModalOpen}
  title={editingUser ? 'Edit user' : 'Create user'}
  on:close={() => (userModalOpen = false)}
>
  <form class="space-y-4" on:submit|preventDefault={saveUser}>
    <label>
      <span class="form-label">Name</span>
      <input class="input-field" bind:value={userForm.name} required />
    </label>
    <label>
      <span class="form-label">Email</span>
      <input
        class="input-field"
        type="email"
        bind:value={userForm.email}
        required
      />
    </label>
    <label>
      <span class="form-label">Role</span>
      <select class="select-field" bind:value={userForm.role}>
        {#each roleOptions as role}
          <option value={role}>{titleCase(role)}</option>
        {/each}
      </select>
    </label>
    {#if !editingUser}
      <label>
        <span class="form-label">Temporary password</span>
        <input
          class="input-field"
          type="password"
          bind:value={userForm.password}
          placeholder="Leave blank to auto-generate"
        />
      </label>
    {/if}
    <div class="flex justify-end gap-2">
      <Button
        type="button"
        variant="secondary"
        on:click={() => (userModalOpen = false)}
      >
        Cancel
      </Button>
      <Button type="submit" disabled={saving}>
        {editingUser ? 'Save changes' : 'Create user'}
      </Button>
    </div>
  </form>
</Modal>

<Modal
  open={!!tempPassword}
  title="Temporary password"
  on:close={() => (tempPassword = '')}
>
  <div class="space-y-4">
    <p class="text-sm text-muted">
      Use this once and ask the user to rotate it after login.
    </p>
    <pre
      class="rounded-lg bg-canvas p-4 font-mono text-sm text-primary">{tempPassword}</pre>
    <div class="flex justify-end">
      <Button on:click={() => (tempPassword = '')}>Done</Button>
    </div>
  </div>
</Modal>

<ConfirmDialog
  open={!!deactivateTarget}
  title="Deactivate user"
  message={`Deactivate ${deactivateTarget?.email ?? 'this user'}? They will no longer be able to sign in.`}
  confirmLabel="Deactivate"
  danger
  onCancel={() => (deactivateTarget = null)}
  onConfirm={deactivateUser}
/>

<ConfirmDialog
  open={!!resetPasswordTarget}
  title="Reset password"
  message={`Generate a temporary password for ${resetPasswordTarget?.email ?? 'this user'}?`}
  confirmLabel="Reset password"
  onCancel={() => (resetPasswordTarget = null)}
  onConfirm={resetPassword}
/>

<ConfirmDialog
  open={restoreConfirmOpen}
  title="Restore backup"
  message="Restoring a backup can overwrite current data and may restart the backend. Continue?"
  confirmLabel="Restore"
  danger
  onCancel={() => (restoreConfirmOpen = false)}
  onConfirm={restoreBackup}
/>

<ConfirmDialog
  open={!!maintenanceConfirm}
  title="Run maintenance"
  message={maintenanceConfirm === 'optimize-db'
    ? 'Optimize the database now?'
    : 'Clear application cache now?'}
  confirmLabel="Run"
  onCancel={() => (maintenanceConfirm = null)}
  onConfirm={runMaintenanceAction}
/>
