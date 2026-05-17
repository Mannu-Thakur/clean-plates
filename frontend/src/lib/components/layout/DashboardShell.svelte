<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { Menu, PanelLeftClose, Power, Search } from '@lucide/svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ToastHost from '$lib/components/ui/ToastHost.svelte';
  import { auth, initAuth, logout } from '$lib/stores/auth';
  import { navItems } from './navigation';
  import { titleCase } from '$lib/utils/format';

  let collapsed = false;
  let mobileOpen = false;
  let query = '';

  $: role = $auth.user?.role ?? '';
  $: visibleNav = navItems.filter((item) => !role || item.roles.includes(role));
  $: activeTitle =
    navItems.find(
      (item) =>
        $page.url.pathname === item.href ||
        $page.url.pathname.startsWith(`${item.href}/`)
    )?.label ?? 'Dashboard';

  onMount(async () => {
    await initAuth();
    if (!$auth.user) {
      await goto(`/login?next=${encodeURIComponent($page.url.pathname)}`);
    }
  });

  async function handleLogout() {
    await logout();
    await goto('/login');
  }
</script>

<ToastHost />

{#if $auth.user}
  <div
    class="min-h-screen lg:grid"
    class:lg:grid-cols-[76px_1fr]={collapsed}
    class:lg:grid-cols-[260px_1fr]={!collapsed}
  >
    <aside
      class={`fixed inset-y-0 left-0 z-40 flex w-72 transform flex-col border-r border-line bg-white transition lg:static lg:w-auto lg:translate-x-0 ${
        mobileOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div
        class="flex h-16 items-center justify-between border-b border-line px-4"
      >
        <a href="/dashboard" class="flex min-w-0 items-center gap-3">
          <div
            class="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-fresh text-lg font-bold text-white"
          >
            CP
          </div>
          {#if !collapsed}
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-ink">CleanPlates</p>
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
            class={`flex h-11 items-center gap-3 rounded-md px-3 text-sm font-semibold transition ${
              active
                ? 'bg-fresh text-white'
                : 'text-muted hover:bg-slate-100 hover:text-ink'
            }`}
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

      <div class="border-t border-line p-3">
        <div
          class={`rounded-lg bg-slate-50 p-3 ${collapsed ? 'text-center' : ''}`}
        >
          {#if !collapsed}
            <p class="truncate text-sm font-semibold text-ink">
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
        class="fixed inset-0 z-30 bg-ink/30 lg:hidden"
        aria-label="Close navigation"
        on:click={() => (mobileOpen = false)}
      ></button>
    {/if}

    <div class="min-w-0">
      <header
        class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-white/92 px-4 backdrop-blur lg:px-6"
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
          <h1 class="truncate text-lg font-semibold text-ink">{activeTitle}</h1>
        </div>
        <label
          class="hidden min-w-64 items-center gap-2 rounded-md border border-line bg-field px-3 lg:flex"
        >
          <Search size={16} class="text-muted" />
          <input
            bind:value={query}
            class="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
            placeholder="Search current view"
          />
        </label>
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
    <div class="surface w-full max-w-sm p-6 text-center">
      <div
        class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-line border-t-fresh"
      ></div>
      <p class="mt-3 text-sm text-muted">Checking session</p>
    </div>
  </div>
{/if}
