<script lang="ts">
  import { dismissToast, toasts } from '$lib/stores/toast';
  import { X } from '@lucide/svelte';
</script>

<div class="fixed right-4 top-4 z-[60] flex w-[min(92vw,380px)] flex-col gap-2">
  {#each $toasts as toast (toast.id)}
    <div
      class={`surface flex items-start gap-3 px-4 py-3 text-sm ${
        toast.type === 'success'
          ? 'border-fresh/30'
          : toast.type === 'error'
            ? 'border-coral/30'
            : 'border-sky/30'
      }`}
    >
      <span
        class={`mt-1 h-2 w-2 shrink-0 rounded-full ${
          toast.type === 'success'
            ? 'bg-fresh'
            : toast.type === 'error'
              ? 'bg-coral'
              : 'bg-sky'
        }`}
      ></span>
      <p class="min-w-0 flex-1 text-ink">{toast.message}</p>
      <button
        type="button"
        class="text-muted hover:text-ink"
        aria-label="Dismiss"
        on:click={() => dismissToast(toast.id)}
      >
        <X size={15} />
      </button>
    </div>
  {/each}
</div>
