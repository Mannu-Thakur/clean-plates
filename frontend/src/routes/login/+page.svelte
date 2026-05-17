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

<main class="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
  <section
    class="flex min-h-screen flex-col justify-between bg-ink p-6 text-white lg:p-10"
  >
    <div class="flex items-center gap-3">
      <div class="grid h-11 w-11 place-items-center rounded-md bg-fresh">
        <Utensils size={22} />
      </div>
      <div>
        <h1 class="text-xl font-semibold">CleanPlates</h1>
        <p class="text-sm text-white/68">Institutional food waste monitoring</p>
      </div>
    </div>

    <div class="max-w-xl py-12">
      <div
        class="mb-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/8 px-3 py-1 text-sm"
      >
        <Server size={15} />
        Backend
        <StatusBadge value={health} compact />
      </div>
      <h2 class="text-4xl font-semibold leading-tight">
        Operational dashboard for cleaner meal service.
      </h2>
      <p class="mt-4 max-w-lg text-base leading-7 text-white/72">
        Review live waste entries, student patterns, devices, reports, and
        enforcement rules from one connected control surface.
      </p>
    </div>

    <div class="grid grid-cols-3 gap-3 text-sm">
      <div class="rounded-lg border border-white/12 bg-white/7 p-3">
        <p class="font-semibold">Live feed</p>
        <p class="mt-1 text-white/60">WebSocket ready</p>
      </div>
      <div class="rounded-lg border border-white/12 bg-white/7 p-3">
        <p class="font-semibold">JWT session</p>
        <p class="mt-1 text-white/60">Auto refresh</p>
      </div>
      <div class="rounded-lg border border-white/12 bg-white/7 p-3">
        <p class="font-semibold">RBAC</p>
        <p class="mt-1 text-white/60">Role aware</p>
      </div>
    </div>
  </section>

  <section class="flex min-h-screen items-center justify-center px-4 py-10">
    <div class="surface w-full max-w-md p-6 sm:p-8">
      {#if expired}
        <div
          class="mb-5 rounded-md border border-amber/30 bg-amber/10 px-4 py-3 text-sm text-amber"
        >
          Your session expired. Sign in again to continue.
        </div>
      {/if}

      <div class="mb-6">
        <p class="label">Secure access</p>
        <h2 class="mt-2 text-2xl font-semibold text-ink">
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
              class="mt-2 flex items-center gap-2 rounded-md border border-line bg-field px-3"
            >
              <Mail size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none"
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
              class="mt-2 flex items-center gap-2 rounded-md border border-line bg-field px-3"
            >
              <Mail size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none"
                type="email"
                autocomplete="email"
                bind:value={email}
              />
            </span>
          </label>
          <label class="block">
            <span class="label">Password</span>
            <span
              class="mt-2 flex items-center gap-2 rounded-md border border-line bg-field px-3"
            >
              <LockKeyhole size={16} class="text-muted" />
              <input
                class="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none"
                type={showPassword ? 'text' : 'password'}
                autocomplete="current-password"
                bind:value={password}
              />
              <button
                class="text-muted hover:text-ink"
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
                class="h-4 w-4 rounded border-line text-fresh"
                type="checkbox"
                bind:checked={remember}
              />
              Remember me
            </label>
            <button
              class="font-semibold text-fresh hover:text-fresh/80"
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
              class="rounded-md border border-coral/30 bg-coral/10 px-3 py-2 text-sm text-coral"
            >
              {$auth.error}
            </p>
          {/if}
        </form>
      {/if}
    </div>
  </section>
</main>
