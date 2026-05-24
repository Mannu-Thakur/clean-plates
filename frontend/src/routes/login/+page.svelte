<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import {
    Eye,
    EyeOff,
    Loader2,
    LockKeyhole,
    Mail,
    Server,
    Utensils
  } from '@lucide/svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import ToastHost from '$lib/components/ui/ToastHost.svelte';
  import { api } from '$lib/api/client';
  import { auth, initAuth, login } from '$lib/stores/auth';
  import { notify } from '$lib/stores/toast';

  let email = '';
  let password = '';
  let remember = true;
  let showPassword = false;
  let forgotMode = false;
  let resetEmail = '';
  let submitting = false;
  let health: 'checking' | 'online' | 'offline' = 'checking';
  const loginSlogans = [
    'Waste less. Serve smarter.',
    'Every plate tells a planning story.',
    'Measure meals. Improve tomorrow.',
    'Cleaner plates. Clearer decisions.',
    'Food saved is value protected.'
  ];
  const rollingSlogans = [...loginSlogans, ...loginSlogans];

  $: expired = $page.url.searchParams.get('expired') === '1';

  onMount(async () => {
    await initAuth();
    if ($auth.user) await routeAfterLogin($auth.user.role);
    try {
      const response = await fetch('/health');
      health = response.ok ? 'online' : 'offline';
    } catch {
      health = 'offline';
    }
  });

  async function routeAfterLogin(role: string) {
    const next = $page.url.searchParams.get('next');
    if (next?.startsWith('/dashboard')) {
      await goto(next);
      return;
    }
    await goto(
      role === 'staff_operator' ? '/dashboard/monitoring' : '/dashboard'
    );
  }

  async function submitLogin() {
    if (!email || !password) {
      notify('Email and password are required.', 'error');
      return;
    }
    submitting = true;
    try {
      const user = await login(email, password, remember);
      notify('Signed in successfully.', 'success');
      await routeAfterLogin(user.role);
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Could not sign in.',
        'error'
      );
    } finally {
      submitting = false;
    }
  }

  async function sendReset() {
    if (!resetEmail) {
      notify('Enter the account email first.', 'error');
      return;
    }
    submitting = true;
    try {
      await api.post(
        '/auth/forgot-password',
        { email: resetEmail },
        { skipAuth: true }
      );
      notify('If that email exists, a reset link has been sent.', 'success');
      forgotMode = false;
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Could not request a reset.',
        'error'
      );
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>Login | CleanPlates</title>
</svelte:head>

<ToastHost />

<main
  class="grid min-h-screen bg-canvas text-body lg:grid-cols-[1.05fr_0.95fr]"
>
  <section
    class="hidden min-h-screen flex-col justify-between border-r border-border bg-card p-6 lg:flex lg:p-10"
  >
    <div class="flex items-center gap-3">
      <div
        class="grid h-11 w-11 place-items-center rounded-md bg-primary text-ink"
      >
        <Utensils size={22} />
      </div>
      <div>
        <h1 class="text-xl font-semibold text-body">CleanPlates</h1>
        <p class="text-sm text-muted">Institutional food waste monitoring</p>
      </div>
    </div>

    <div class="max-w-xl py-12">
      <div
        class="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-elevated px-3 py-1 text-sm text-muted"
      >
        <Server size={15} />
        Backend
        <StatusBadge value={health} compact />
      </div>
      <h2 class="text-4xl font-semibold leading-tight text-body">
        Operational dashboard for cleaner meal service.
      </h2>
      <p class="mt-4 max-w-lg text-base leading-7 text-muted-strong">
        Review live waste entries, student patterns, devices, reports, and
        enforcement rules from one connected control center.
      </p>

      <div class="slogan-rail mt-8" aria-label={loginSlogans.join(' ')}>
        <div class="slogan-track" aria-hidden="true">
          {#each rollingSlogans as slogan}
            <span class="slogan-chip">{slogan}</span>
          {/each}
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3 text-sm">
      <div class="rounded-lg border border-border bg-elevated p-3">
        <p class="font-semibold text-primary">Live feed</p>
        <p class="mt-1 text-muted">WebSocket ready</p>
      </div>
      <div class="rounded-lg border border-border bg-elevated p-3">
        <p class="font-semibold text-primary">JWT session</p>
        <p class="mt-1 text-muted">Auto refresh</p>
      </div>
      <div class="rounded-lg border border-border bg-elevated p-3">
        <p class="font-semibold text-primary">RBAC</p>
        <p class="mt-1 text-muted">Role aware</p>
      </div>
    </div>
  </section>

  <section
    class="flex min-h-screen flex-col items-center justify-center px-4 py-10"
  >
    <div class="card w-full max-w-md p-6 sm:p-8">
      {#if expired}
        <div
          class="mb-5 rounded-md border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary"
        >
          Your session expired. Sign in again to continue.
        </div>
      {/if}

      <div class="mb-6">
        <p class="label">Secure access</p>
        <h2 class="mt-2 text-2xl font-semibold text-body">
          {forgotMode ? 'Reset password' : 'Sign in'}
        </h2>
        <p class="mt-2 text-sm text-muted">
          {forgotMode
            ? 'Enter your email to receive the reset flow.'
            : 'Use your CleanPlates administrator or operator account.'}
        </p>
      </div>

      {#if forgotMode}
        <form class="space-y-4" on:submit|preventDefault={sendReset}>
          <label class="block">
            <span class="label">Email</span>
            <span
              class="mt-2 flex items-center gap-2 rounded-md border border-border bg-elevated px-3 transition-colors focus-within:border-primary focus-within:shadow-ring-primary"
            >
              <Mail size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm text-body outline-none placeholder:text-muted"
                type="email"
                bind:value={resetEmail}
              />
            </span>
          </label>
          <div class="flex gap-2">
            <Button type="submit" disabled={submitting}>
              {#if submitting}<Loader2 class="animate-spin" size={16} />{/if}
              Send reset
            </Button>
            <Button
              type="button"
              variant="secondary"
              on:click={() => (forgotMode = false)}>Back</Button
            >
          </div>
        </form>
      {:else}
        <form class="space-y-4" on:submit|preventDefault={submitLogin}>
          <label class="block">
            <span class="label">Email</span>
            <span
              class="mt-2 flex items-center gap-2 rounded-md border border-border bg-elevated px-3 transition-colors focus-within:border-primary focus-within:shadow-ring-primary"
            >
              <Mail size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm text-body outline-none placeholder:text-muted"
                type="email"
                autocomplete="email"
                bind:value={email}
              />
            </span>
          </label>
          <label class="block">
            <span class="label">Password</span>
            <span
              class="mt-2 flex items-center gap-2 rounded-md border border-border bg-elevated px-3 transition-colors focus-within:border-primary focus-within:shadow-ring-primary"
            >
              <LockKeyhole size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm text-body outline-none placeholder:text-muted"
                type={showPassword ? 'text' : 'password'}
                autocomplete="current-password"
                bind:value={password}
              />
              <button
                class="text-muted transition-colors hover:text-body"
                type="button"
                aria-label="Toggle password"
                on:click={() => (showPassword = !showPassword)}
              >
                {#if showPassword}<EyeOff size={17} />{:else}<Eye
                    size={17}
                  />{/if}
              </button>
            </span>
          </label>

          <div class="flex items-center justify-between gap-3 text-sm">
            <label class="inline-flex items-center gap-2 text-muted">
              <input
                class="h-4 w-4 rounded border-border accent-primary"
                type="checkbox"
                bind:checked={remember}
              />
              Remember me
            </label>
            <button
              class="font-semibold text-primary hover:text-primary-hover"
              type="button"
              on:click={() => (forgotMode = true)}
            >
              Forgot password
            </button>
          </div>

          <Button
            class="w-full"
            type="submit"
            disabled={submitting || $auth.loading}
          >
            {#if submitting || $auth.loading}<Loader2
                class="animate-spin"
                size={16}
              />{/if}
            Sign in
          </Button>

          {#if $auth.error}
            <p
              class="rounded-md border border-down/30 bg-down/10 px-3 py-2 text-sm text-down"
            >
              {$auth.error}
            </p>
          {/if}
        </form>
      {/if}
    </div>

    <div
      class="slogan-rail mt-5 w-full max-w-md lg:hidden"
      aria-label={loginSlogans.join(' ')}
    >
      <div class="slogan-track" aria-hidden="true">
        {#each rollingSlogans as slogan}
          <span class="slogan-chip">{slogan}</span>
        {/each}
      </div>
    </div>
  </section>
</main>

<style>
  .slogan-rail {
    overflow: hidden;
    border: 1px solid rgb(var(--color-border));
    border-radius: 999px;
    background: rgb(var(--color-elevated) / 0.72);
    contain: paint;
  }

  .slogan-track {
    display: flex;
    width: max-content;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    animation: slogan-roll 36s linear infinite;
    will-change: transform;
  }

  .slogan-chip {
    display: inline-flex;
    align-items: center;
    min-height: 1.75rem;
    white-space: nowrap;
    border: 1px solid rgb(var(--color-border));
    border-radius: 999px;
    padding: 0.25rem 0.85rem;
    color: rgb(var(--color-muted-strong));
    font-size: 0.8125rem;
    font-weight: 600;
    line-height: 1.2;
  }

  .slogan-chip::before {
    content: '';
    width: 0.375rem;
    height: 0.375rem;
    margin-right: 0.5rem;
    border-radius: 999px;
    background: rgb(var(--color-primary));
  }

  .slogan-rail:hover .slogan-track {
    animation-play-state: paused;
  }

  @keyframes slogan-roll {
    from {
      transform: translateX(0);
    }
    to {
      transform: translateX(-50%);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .slogan-track {
      animation: none;
      transform: none;
    }
  }
</style>
