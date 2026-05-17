<script lang="ts">
  export let title: string;
  export let value: string | number;
  export let helper = '';
  export let trend: string | number | null = null;
  export let tone: 'good' | 'warn' | 'bad' | 'hot' | 'neutral' = 'neutral';

  $: iconClass =
    tone === 'good'
      ? 'bg-up/10 text-up'
      : tone === 'warn'
        ? 'bg-primary/10 text-primary'
        : tone === 'bad'
          ? 'bg-down/10 text-down'
          : tone === 'hot'
            ? 'bg-primary/15 text-primary'
            : 'bg-elevated text-muted';

  $: trendClass =
    tone === 'good'
      ? 'bg-up/10 text-up'
      : tone === 'warn'
        ? 'bg-primary/10 text-primary'
        : tone === 'bad'
          ? 'bg-down/10 text-down'
          : tone === 'hot'
            ? 'bg-primary/15 text-primary'
            : 'bg-elevated text-muted';
</script>

<article class="card min-h-32 p-4">
  <div class="flex items-start justify-between gap-3">
    <p class="text-sm font-medium text-muted">{title}</p>
    <div
      class={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${iconClass}`}
    >
      <slot name="icon" />
    </div>
  </div>
  <div class="mt-4 flex items-end justify-between gap-3">
    <div class="min-w-0">
      <p class="truncate text-2xl font-semibold text-body">{value}</p>
      {#if helper}
        <p class="mt-1 text-xs text-muted">{helper}</p>
      {/if}
    </div>
    {#if trend !== null && trend !== ''}
      <span class={`rounded-sm px-2 py-0.5 text-xs font-semibold ${trendClass}`}
        >{trend}</span
      >
    {/if}
  </div>
</article>
