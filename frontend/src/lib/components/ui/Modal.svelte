<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { X } from '@lucide/svelte';

  export let open = false;
  export let title = '';
  export let description = '';
  export let wide = false;

  const dispatch = createEventDispatcher<{ close: void }>();

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') dispatch('close');
  }
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
  <!-- Backdrop -->
  <button
    class="fixed inset-0 z-50 bg-canvas/80 backdrop-blur-sm"
    type="button"
    aria-label="Close modal"
    on:click={() => dispatch('close')}
  ></button>

  <!-- Panel -->
  <div class="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
    <section
      class={`pointer-events-auto max-h-[90vh] w-full overflow-hidden card ${wide ? 'max-w-5xl' : 'max-w-xl'}`}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <header class="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
        <div>
          <h2 class="text-base font-semibold text-body">{title}</h2>
          {#if description}
            <p class="mt-1 text-sm text-muted">{description}</p>
          {/if}
        </div>
        <button
          class="icon-btn"
          type="button"
          aria-label="Close"
          on:click={() => dispatch('close')}
        >
          <X size={18} />
        </button>
      </header>
      <div class="max-h-[calc(90vh-76px)] overflow-auto p-5">
        <slot />
      </div>
    </section>
  </div>
{/if}
