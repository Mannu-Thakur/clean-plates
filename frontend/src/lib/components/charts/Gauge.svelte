<script lang="ts">
  export let value = 0;
  export let max = 100;
  export let label = '';
  export let unit = '';

  $: pct = Math.max(0, Math.min(100, (value / Math.max(max, 1)) * 100));
  $: color = pct > 85 ? '#f6465d' : pct > 60 ? '#fcd535' : '#0ecb81';
  $: radius = 50;
  $: circumference = 2 * Math.PI * radius;
  $: offset = circumference - (pct / 100) * circumference;
</script>

<div class="flex flex-col items-center justify-center">
  <div class="relative grid h-40 w-40 place-items-center">
    <svg
      class="h-full w-full -rotate-90"
      viewBox="0 0 120 120"
      aria-hidden="true"
    >
      <circle
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke="#2b3139"
        stroke-width="12"
      />
      <circle
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke={color}
        stroke-linecap="round"
        stroke-width="12"
        stroke-dasharray={circumference}
        stroke-dashoffset={offset}
      />
    </svg>
    <div
      class="absolute grid h-28 w-28 place-items-center rounded-full border border-border bg-card text-center"
    >
      <div>
        <p class="text-2xl font-semibold text-body">
          {value.toFixed(value >= 10 ? 0 : 1)}
        </p>
        <p class="text-xs font-semibold uppercase tracking-normal text-muted">
          {unit}
        </p>
      </div>
    </div>
  </div>
  {#if label}
    <p class="mt-3 text-sm font-medium text-muted">{label}</p>
  {/if}
</div>
