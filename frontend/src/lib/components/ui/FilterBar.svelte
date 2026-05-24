<script lang="ts" context="module">
  export type SelectOption = {
    value: string;
    label: string;
    disabled?: boolean;
  };

  export type FilterConfig = {
    type: 'text' | 'select' | 'date-range';
    key: string;
    label: string;
    options?: SelectOption[];
    placeholder?: string;
  };
</script>

<script lang="ts">
  import { onDestroy } from 'svelte';
  import Button from './Button.svelte';
  import DateRangePicker from './DateRangePicker.svelte';
  import SearchInput from './SearchInput.svelte';
  import SelectField from './SelectField.svelte';

  export let filters: FilterConfig[] = [];
  export let values: Record<string, unknown> = {};
  export let onFilter: (values: Record<string, unknown>) => void = () => {};
  export let onReset: (() => void) | undefined = undefined;

  let draft: Record<string, unknown> = { ...values };
  let previousValues = values;
  let timer: ReturnType<typeof setTimeout> | undefined;

  $: if (values !== previousValues) {
    previousValues = values;
    draft = { ...values };
  }

  onDestroy(() => {
    if (timer) clearTimeout(timer);
  });

  function emit(next: Record<string, unknown>) {
    draft = next;
    onFilter(draft);
  }

  function debounce(next: Record<string, unknown>) {
    draft = next;
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => onFilter(draft), 300);
  }

  function updateValue(key: string, value: unknown, immediate = true) {
    const next = { ...draft, [key]: value };
    if (immediate) emit(next);
    else debounce(next);
  }

  function updateRange(key: string, start: string | null, end: string | null) {
    emit({ ...draft, [key]: { start, end } });
  }

  function reset() {
    draft = {};
    if (onReset) onReset();
    else onFilter(draft);
  }
</script>

<div class="card flex flex-wrap items-end gap-3 p-4">
  {#each filters as filter}
    <div class="min-w-[180px] flex-1">
      <span class="form-label">{filter.label}</span>

      {#if filter.type === 'text'}
        <SearchInput
          value={String(draft[filter.key] ?? '')}
          placeholder={filter.placeholder ?? filter.label}
          onSearch={(value) => updateValue(filter.key, value)}
        />
      {:else if filter.type === 'select'}
        <SelectField
          value={String(draft[filter.key] ?? '')}
          options={filter.options ?? []}
          placeholder={filter.placeholder ?? 'Select'}
          onChange={(value) => updateValue(filter.key, value)}
        />
      {:else if filter.type === 'date-range'}
        {@const range = (draft[filter.key] ?? {}) as {
          start?: string | null;
          end?: string | null;
        }}
        <DateRangePicker
          start={range.start ?? null}
          end={range.end ?? null}
          onChange={(start, end) => updateRange(filter.key, start, end)}
        />
      {/if}
    </div>
  {/each}

  <Button type="button" variant="ghost" size="sm" on:click={reset}>Reset</Button
  >
</div>
