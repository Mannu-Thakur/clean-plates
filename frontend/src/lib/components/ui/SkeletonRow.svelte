<script lang="ts">
  export let cols = 4;
  export let rows = 6;
</script>

{#each Array(rows) as _, rowIndex}
  <tr aria-hidden="true">
    {#each Array(cols) as _, colIndex}
      <td class="td">
        <div
          class={`skeleton h-4 ${colIndex === 0 ? 'w-10/12' : 'w-8/12'} ${rowIndex % 2 === 1 ? 'opacity-70' : ''}`}
        ></div>
      </td>
    {/each}
  </tr>
{/each}
