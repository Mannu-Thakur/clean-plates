<script lang="ts">
  export let label = '';
  export let error = '';
  export let required = false;
  export let hint = '';
</script>

<label class="block">
  {#if label}
    <span class="form-label">
      {label}
      {#if required}
        <span class="text-down" aria-hidden="true">*</span>
      {/if}
    </span>
  {/if}

  <slot />

  {#if error}
    <p class="mt-1 text-xs font-medium text-down">{error}</p>
  {:else if hint}
    <p class="mt-1 text-xs text-muted">{hint}</p>
  {/if}
</label>
