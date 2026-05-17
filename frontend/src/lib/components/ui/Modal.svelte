<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { X } from '@lucide/svelte';

  export let open = false;
  export let title = '';
  export let description = '';
  export let wide = false;

  const dispatch = createEventDispatcher<{ close: void }>();
</script>

{#if open}
  <button
    class="fixed inset-0 z-50 bg-ink/35"
    type="button"
    aria-label="Close modal"
    on:click={() => dispatch('close')}
  ></button>
  <div
    class="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4"
  >
    <section
      class={`pointer-events-auto max-h-[90vh] w-full overflow-hidden rounded-lg bg-white shadow-soft ${wide ? 'max-w-5xl' : 'max-w-xl'}`}
    >
      <header
        class="flex items-start justify-between gap-4 border-b border-line px-5 py-4"
      >
        <div>
          <h2 class="text-base font-semibold text-ink">{title}</h2>
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
