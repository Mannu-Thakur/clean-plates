<script lang="ts">
  export let title: string;
  export let value: string | number;
  export let helper = '';
  export let trend: string | number | null = null;
  export let tone: 'good' | 'warn' | 'bad' | 'hot' | 'neutral' = 'neutral';

  $: toneClass =
    tone === 'good'
      ? 'bg-fresh/10 text-fresh'
      : tone === 'warn'
        ? 'bg-amber/10 text-amber'
        : tone === 'bad'
          ? 'bg-coral/10 text-coral'
          : tone === 'hot'
            ? 'bg-orange-100 text-orange-700'
            : 'bg-slate-100 text-slate-600';
</script>

<article class="surface min-h-32 p-4">
  <div class="flex items-start justify-between gap-3">
    <p class="text-sm font-medium text-muted">{title}</p>
    <div
      class={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${toneClass}`}
    >
      <slot name="icon" />
    </div>
  </div>
  <div class="mt-4 flex items-end justify-between gap-3">
    <div class="min-w-0">
      <p class="truncate text-2xl font-semibold text-ink">{value}</p>
      {#if helper}
        <p class="mt-1 text-xs text-muted">{helper}</p>
      {/if}
    </div>
    {#if trend !== null && trend !== ''}
      <span class={`rounded-full px-2 py-1 text-xs font-semibold ${toneClass}`}
        >{trend}</span
      >
    {/if}
  </div>
</article>
