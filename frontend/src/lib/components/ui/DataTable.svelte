<script lang="ts" context="module">
  export interface TableColumn {
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
    format?: (value: unknown, row: Record<string, unknown>) => string | number;
  }
</script>

<script lang="ts">
  import { ArrowDown, ArrowUp, ChevronsUpDown } from '@lucide/svelte';
  import EmptyState from './EmptyState.svelte';
  import Pagination from './Pagination.svelte';
  import SkeletonRow from './SkeletonRow.svelte';

  export let columns: TableColumn[] = [];
  export let rows: Record<string, unknown>[] = [];
  export let loading = false;
  export let page = 1;
  export let total = 0;
  export let pageSize = 25;
  export let sortKey = '';
  export let sortDirection: 'asc' | 'desc' = 'asc';
  export let onRowClick: ((row: Record<string, unknown>) => void) | undefined =
    undefined;
  export let onSort: ((key: string, dir: 'asc' | 'desc') => void) | undefined =
    undefined;
  export let onPageChange: (page: number) => void = () => {};

  $: colSpan = columns.length + ($$slots['row-actions'] ? 1 : 0);

  function valueFor(row: Record<string, unknown>, key: string) {
    return key.split('.').reduce<unknown>((current, part) => {
      if (current && typeof current === 'object' && part in current) {
        return (current as Record<string, unknown>)[part];
      }
      return undefined;
    }, row);
  }

  function displayValue(row: Record<string, unknown>, column: TableColumn) {
    const value = valueFor(row, column.key);
    return column.format ? column.format(value, row) : (value ?? '-');
  }

  function alignClass(align: TableColumn['align']) {
    if (align === 'right') return 'text-right';
    if (align === 'center') return 'text-center';
    return 'text-left';
  }

  function sort(column: TableColumn) {
    if (!column.sortable || !onSort) return;
    const nextDirection =
      sortKey === column.key && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(column.key, nextDirection);
  }
</script>

<div class="table-wrapper">
  <div class="overflow-auto">
    <table>
      <thead class="sticky top-0 z-10">
        <tr>
          {#each columns as column}
            <th
              class={`th ${alignClass(column.align)}`}
              style={column.width ? `width:${column.width}` : undefined}
            >
              {#if column.sortable}
                <button
                  class={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide transition-colors hover:text-body ${alignClass(column.align)}`}
                  type="button"
                  on:click={() => sort(column)}
                >
                  <span>{column.label}</span>
                  {#if sortKey === column.key && sortDirection === 'asc'}
                    <ArrowUp size={13} />
                  {:else if sortKey === column.key && sortDirection === 'desc'}
                    <ArrowDown size={13} />
                  {:else}
                    <ChevronsUpDown size={13} />
                  {/if}
                </button>
              {:else}
                {column.label}
              {/if}
            </th>
          {/each}
          {#if $$slots['row-actions']}
            <th class="th text-right">Actions</th>
          {/if}
        </tr>
      </thead>
      <tbody>
        {#if loading}
          <SkeletonRow cols={colSpan} rows={Math.min(pageSize, 6)} />
        {:else if rows.length === 0}
          <tr>
            <td class="td border-b-0" colspan={colSpan}>
              {#if $$slots.empty}
                <slot name="empty" />
              {:else}
                <EmptyState />
              {/if}
            </td>
          </tr>
        {:else}
          {#each rows as row}
            <tr
              class:tr-hover={Boolean(onRowClick)}
              on:click={() => onRowClick?.(row)}
            >
              {#each columns as column}
                {@const value = valueFor(row, column.key)}
                <td class={`td ${alignClass(column.align)}`}>
                  {#if $$slots.cell}
                    <slot name="cell" {row} {column} {value}>
                      {displayValue(row, column)}
                    </slot>
                  {:else}
                    {displayValue(row, column)}
                  {/if}
                </td>
              {/each}
              {#if $$slots['row-actions']}
                <td class="td text-right" on:click|stopPropagation>
                  <slot name="row-actions" {row} />
                </td>
              {/if}
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  {#if total > pageSize}
    <Pagination {page} {total} {pageSize} onChange={onPageChange} />
  {/if}
</div>
