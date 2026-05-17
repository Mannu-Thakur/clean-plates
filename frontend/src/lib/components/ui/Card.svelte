<script lang="ts">
  export let title = '';
  export let description = '';
  let klass = '';
  export { klass as class };
</script>

<section class={`surface p-5 ${klass}`}>
  {#if title || description || $$slots.actions}
    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        {#if title}
          <h2 class="text-base font-semibold text-ink">{title}</h2>
        {/if}
        {#if description}
          <p class="mt-1 text-sm text-muted">{description}</p>
        {/if}
      </div>
      {#if $$slots.actions}
        <div class="flex items-center gap-2">
          <slot name="actions" />
        </div>
      {/if}
    </div>
  {/if}
  <slot />
</section>
