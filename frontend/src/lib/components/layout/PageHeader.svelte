<script lang="ts">
  export let label = '';
  export let title = '';
  export let description = '';
</script>

<header
  class="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
>
  <div class="min-w-0">
    {#if label}
      <p class="label">{label}</p>
    {/if}
    <h1 class="mt-1 text-2xl font-semibold text-body">{title}</h1>
    {#if description}
      <p class="mt-2 max-w-3xl text-sm leading-6 text-muted">{description}</p>
    {/if}
  </div>

  {#if $$slots.actions}
    <div class="flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  {/if}
</header>
