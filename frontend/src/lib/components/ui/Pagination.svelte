<script lang="ts">
  export let page = 1;
  export let total = 0;
  export let pageSize = 25;
  export let onChange: (page: number) => void = () => {};

  $: totalPages = Math.max(1, Math.ceil(total / Math.max(pageSize, 1)));
  $: safePage = Math.min(Math.max(page, 1), totalPages);
  $: start = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  $: end = Math.min(total, safePage * pageSize);

  $: pages = buildPages(safePage, totalPages);

  function buildPages(current: number, pagesCount: number) {
    if (pagesCount <= 7)
      return Array.from({ length: pagesCount }, (_, i) => i + 1);

    const result: Array<number | 'ellipsis'> = [1];
    const left = Math.max(2, current - 1);
    const right = Math.min(pagesCount - 1, current + 1);

    if (left > 2) result.push('ellipsis');
    for (let item = left; item <= right; item += 1) result.push(item);
    if (right < pagesCount - 1) result.push('ellipsis');
    result.push(pagesCount);

    return result;
  }

  function go(next: number) {
    const target = Math.min(Math.max(next, 1), totalPages);
    if (target !== safePage) onChange(target);
  }
</script>

<div
  class="flex flex-wrap items-center justify-between gap-3 border-t border-border bg-card px-4 py-3"
>
  <p class="text-sm text-muted">{start}-{end} of {total}</p>

  <div class="flex items-center gap-1">
    <button
      class="btn-secondary btn-sm"
      type="button"
      disabled={safePage <= 1}
      on:click={() => go(safePage - 1)}
    >
      Prev
    </button>

    {#each pages as item, index}
      {#if item === 'ellipsis'}
        <span class="px-2 text-sm text-muted" aria-hidden="true">...</span>
      {:else}
        <button
          class={`h-8 min-w-8 rounded-md px-2 text-sm font-semibold transition-colors ${
            item === safePage
              ? 'bg-primary text-ink'
              : 'text-muted hover:bg-elevated hover:text-body'
          }`}
          type="button"
          aria-current={item === safePage ? 'page' : undefined}
          on:click={() => go(item)}
        >
          {item}
        </button>
      {/if}
    {/each}

    <button
      class="btn-secondary btn-sm"
      type="button"
      disabled={safePage >= totalPages}
      on:click={() => go(safePage + 1)}
    >
      Next
    </button>
  </div>
</div>
