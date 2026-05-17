<script lang="ts">
  export let value = 0;
  export let max = 100;
  export let label = '';
  export let unit = '';

  $: pct = Math.max(0, Math.min(100, (value / Math.max(max, 1)) * 100));
  $: color = pct > 85 ? '#d95d54' : pct > 60 ? '#c77700' : '#188a6b';
</script>

<div class="flex flex-col items-center justify-center">
  <div
    class="grid h-40 w-40 place-items-center rounded-full"
    style={`background: conic-gradient(${color} ${pct * 3.6}deg, #edf2f6 0deg);`}
  >
    <div
      class="grid h-28 w-28 place-items-center rounded-full bg-white text-center shadow-inner"
    >
      <div>
        <p class="text-2xl font-semibold text-ink">
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
