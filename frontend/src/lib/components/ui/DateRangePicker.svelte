<script lang="ts" context="module">
  export type DatePreset = {
    label: string;
    days: number;
  };
</script>

<script lang="ts">
  export let start: string | null = null;
  export let end: string | null = null;
  export let presets: DatePreset[] = [
    { label: '7d', days: 7 },
    { label: '30d', days: 30 },
    { label: 'Semester', days: 120 }
  ];
  export let onChange: (
    start: string | null,
    end: string | null
  ) => void = () => {};

  $: invalid = Boolean(start && end && start > end);

  function localDateIso(date: Date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function todayIso() {
    return localDateIso(new Date());
  }

  function isoDaysAgo(days: number) {
    const date = new Date();
    date.setDate(date.getDate() - Math.max(days - 1, 0));
    return localDateIso(date);
  }

  function applyPreset(days: number) {
    start = isoDaysAgo(days);
    end = todayIso();
    onChange(start, end);
  }

  function emitChange() {
    if (!invalid) onChange(start, end);
  }
</script>

<div class="space-y-3">
  {#if presets.length}
    <div class="flex flex-wrap gap-2">
      {#each presets as preset}
        <button
          class="btn-ghost btn-sm"
          type="button"
          on:click={() => applyPreset(preset.days)}
        >
          {preset.label}
        </button>
      {/each}
    </div>
  {/if}

  <div class="grid gap-2 sm:grid-cols-2">
    <label class="block">
      <span class="form-label">Start</span>
      <input
        class="input-field"
        type="date"
        bind:value={start}
        on:change={emitChange}
      />
    </label>
    <label class="block">
      <span class="form-label">End</span>
      <input
        class="input-field"
        type="date"
        bind:value={end}
        on:change={emitChange}
      />
    </label>
  </div>

  {#if invalid}
    <p class="text-xs font-medium text-down">
      Start date must be before the end date.
    </p>
  {/if}
</div>
