<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { Bell, Menu, PanelLeftClose, Power, Search } from '@lucide/svelte';
  import { api } from '$lib/api/client';
  import type { NotificationStats } from '$lib/api/types';
  import Button from '$lib/components/ui/Button.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ToastHost from '$lib/components/ui/ToastHost.svelte';
  import { auth, initAuth, logout } from '$lib/stores/auth';
  import { navItems } from './navigation';
  import { titleCase } from '$lib/utils/format';

  let collapsed = false;
  let mobileOpen = false;
  let query = '';
  let unreadCount = 0;

  $: role = $auth.user?.role ?? '';
  $: canUseNotifications = [
    'super_admin',
    'institution_admin',
    'mess_admin'
  ].includes(role);
  $: unreadLabel = unreadCount > 99 ? '99+' : String(unreadCount);
  $: visibleNav = navItems.filter((item) => !role || item.roles.includes(role));
  $: activeTitle =
    navItems.find(
      (item) =>
        $page.url.pathname === item.href ||
        ($page.url.pathname.startsWith(`${item.href}/`) &&
          item.href !== '/dashboard')
    )?.label ?? 'Dashboard';

  $: if ($auth.ready && !$auth.user) {
    void goto(`/login?next=${encodeURIComponent($page.url.pathname)}`);
  }

  onMount(() => {
    const handleNotificationRefresh = () => {
      void loadUnreadCount();
    };

    window.addEventListener(
      'cleanplates:notifications-refresh',
      handleNotificationRefresh
    );

    void boot();

    return () => {
      window.removeEventListener(
        'cleanplates:notifications-refresh',
        handleNotificationRefresh
      );
    };
  });

  async function boot() {
    await initAuth();
    if (!$auth.user) {
      await goto(`/login?next=${encodeURIComponent($page.url.pathname)}`);
      return;
    }
    await loadUnreadCount();
  }

  async function loadUnreadCount() {
    if (!canUseNotifications) {
      unreadCount = 0;
      return;
    }
    try {
      const stats = await api.get<NotificationStats>('/notifications/stats');
      unreadCount = stats.unread;
    } catch {
      unreadCount = 0;
    }
  }

  async function openNotifications() {
    await goto('/dashboard/notifications');
  }

  async function handleLogout() {
    await logout();
    await goto('/login');
  }
</script>

<ToastHost />

{#if $auth.ready && $auth.user}
  <div
    class="min-h-screen bg-canvas text-body lg:grid"
    class:lg:grid-cols-[76px_minmax(0,1fr)]={collapsed}
    class:lg:grid-cols-[260px_minmax(0,1fr)]={!collapsed}
  >
    <aside
      class={`fixed inset-y-0 left-0 z-40 flex w-[260px] transform flex-col border-r border-border bg-card transition lg:sticky lg:top-0 lg:h-screen lg:w-auto lg:translate-x-0 ${
        mobileOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div
        class="flex h-16 items-center justify-between border-b border-border px-4"
      >
        <a href="/dashboard" class="flex min-w-0 items-center gap-3">
          <div
            class="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-primary text-lg font-bold text-ink"
          >
            CP
          </div>
          {#if !collapsed}
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-body">
                CleanPlates
              </p>
              <p class="truncate text-xs text-muted">Waste intelligence</p>
            </div>
          {/if}
        </a>
        <button
          class="icon-btn hidden lg:inline-flex"
          type="button"
          aria-label="Collapse navigation"
          on:click={() => (collapsed = !collapsed)}
        >
          <PanelLeftClose size={17} />
        </button>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto p-3">
        {#each visibleNav as item}
          {@const active =
            $page.url.pathname === item.href ||
            ($page.url.pathname.startsWith(`${item.href}/`) &&
              item.href !== '/dashboard')}
          <a
            class={`nav-item ${collapsed ? 'justify-center px-0' : ''} ${active ? 'nav-item-active' : ''}`}
            href={item.href}
            title={item.label}
            on:click={() => (mobileOpen = false)}
          >
            <svelte:component this={item.icon} size={18} />
            {#if !collapsed}
              <span class="truncate">{item.label}</span>
            {/if}
          </a>
        {/each}
      </nav>

      <div class="border-t border-border p-3">
        <div
          class={`rounded-lg border border-border bg-elevated p-3 ${collapsed ? 'text-center' : ''}`}
        >
          {#if !collapsed}
            <p class="truncate text-sm font-semibold text-body">
              {$auth.user.name}
            </p>
            <p class="truncate text-xs text-muted">{$auth.user.email}</p>
            <div class="mt-2">
              <StatusBadge value={titleCase($auth.user.role)} compact />
            </div>
          {:else}
            <StatusBadge value={$auth.user.role} compact />
          {/if}
        </div>
      </div>
    </aside>

    {#if mobileOpen}
      <button
        class="fixed inset-0 z-30 bg-canvas/80 lg:hidden"
        aria-label="Close navigation"
        on:click={() => (mobileOpen = false)}
      ></button>
    {/if}

    <div class="min-w-0">
      <header
        class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-canvas/95 px-4 backdrop-blur lg:px-6"
      >
        <button
          class="icon-btn lg:hidden"
          type="button"
          aria-label="Open navigation"
          on:click={() => (mobileOpen = true)}
        >
          <Menu size={18} />
        </button>
        <div class="min-w-0 flex-1">
          <p class="text-xs font-semibold uppercase tracking-normal text-muted">
            CleanPlates
          </p>
          <h1 class="truncate text-lg font-semibold text-body">
            {activeTitle}
          </h1>
        </div>
        <label
          class="hidden min-w-64 items-center gap-2 rounded-md border border-border bg-elevated px-3 transition-colors focus-within:border-primary focus-within:shadow-ring-primary lg:flex"
        >
          <Search size={16} class="text-muted" />
          <input
            bind:value={query}
            class="h-10 min-w-0 flex-1 bg-transparent text-sm text-body outline-none placeholder:text-muted"
            placeholder="Search current view"
          />
        </label>
        {#if canUseNotifications}
          <button
            class="icon-btn relative"
            type="button"
            aria-label="Open notifications"
            on:click={openNotifications}
          >
            <Bell size={18} />
            {#if unreadCount > 0}
              <span
                class="absolute -right-1 -top-1 min-w-4 rounded-full bg-down px-1 text-[10px] font-bold leading-4 text-white"
              >
                {unreadLabel}
              </span>
            {/if}
          </button>
        {/if}
        <Button variant="secondary" size="sm" on:click={handleLogout}>
          <Power size={16} />
          <span class="hidden sm:inline">Logout</span>
        </Button>
      </header>

      <main class="mx-auto w-full max-w-[1560px] px-4 py-5 lg:px-6">
        <slot />
      </main>
    </div>
  </div>
{:else}
  <div class="grid min-h-screen place-items-center px-4">
    <div class="card w-full max-w-sm p-6 text-center">
      <div
        class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border border-t-primary"
      ></div>
      <p class="mt-3 text-sm text-muted">Checking session</p>
    </div>
  </div>
{/if}
