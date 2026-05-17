<script lang="ts">
  import { onDestroy, onMount, tick } from 'svelte';
  import { Search, X } from '@lucide/svelte';

  export let value = '';
  export let placeholder = 'Search';
  export let autofocus = false;
  export let debounceMs = 300;
  export let onSearch: (value: string) => void = () => {};
  export let onClear: (() => void) | undefined = undefined;
  let klass = '';
  export { klass as class };

  let input: HTMLInputElement;
  let timer: ReturnType<typeof setTimeout> | undefined;

  onMount(async () => {
    if (autofocus) {
      await tick();
      input?.focus();
    }
  });

  onDestroy(() => {
    if (timer) clearTimeout(timer);
  });

  function scheduleSearch() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => onSearch(value), debounceMs);
  }

  function clear() {
    value = '';
    if (timer) clearTimeout(timer);
    onClear?.();
    onSearch('');
    input?.focus();
  }
</script>

<div class={`relative ${klass}`}>
  <Search
    class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
    size={16}
  />
  <input
    bind:this={input}
    bind:value
    class="input-field pl-9 pr-9"
    type="search"
    {placeholder}
    on:input={scheduleSearch}
    {...$$restProps}
  />
  {#if value}
    <button
      class="absolute right-2 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-sm text-muted transition-colors hover:bg-card hover:text-body"
      type="button"
      aria-label="Clear search"
      on:click={clear}
    >
      <X size={14} />
    </button>
  {/if}
</div>
