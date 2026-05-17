<script lang="ts">
  import { dismissToast, toasts } from '$lib/stores/toast';
  import {
    CheckCircle,
    Info,
    X,
    AlertTriangle,
    AlertCircle
  } from '@lucide/svelte';
</script>

<div
  class="fixed bottom-4 right-4 z-[60] flex w-[min(92vw,380px)] flex-col gap-2"
>
  {#each $toasts as toast (toast.id)}
    <div
      class={`card flex items-start gap-3 px-4 py-3 text-sm border-l-2 ${
        toast.type === 'success'
          ? 'border-l-up'
          : toast.type === 'error'
            ? 'border-l-down'
            : toast.type === 'warning'
              ? 'border-l-primary'
              : 'border-l-info'
      }`}
    >
      <span
        class={`mt-0.5 shrink-0 ${
          toast.type === 'success'
            ? 'text-up'
            : toast.type === 'error'
              ? 'text-down'
              : toast.type === 'warning'
                ? 'text-primary'
                : 'text-info'
        }`}
      >
        {#if toast.type === 'success'}
          <CheckCircle size={16} />
        {:else if toast.type === 'error'}
          <AlertCircle size={16} />
        {:else if toast.type === 'warning'}
          <AlertTriangle size={16} />
        {:else}
          <Info size={16} />
        {/if}
      </span>
      <p class="min-w-0 flex-1 text-body">{toast.message}</p>
      <button
        type="button"
        class="text-muted hover:text-body transition-colors"
        aria-label="Dismiss"
        on:click={() => dismissToast(toast.id)}
      >
        <X size={15} />
      </button>
    </div>
  {/each}
</div>
