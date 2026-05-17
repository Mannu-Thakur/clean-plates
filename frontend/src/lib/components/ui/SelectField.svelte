<script lang="ts" context="module">
  export type SelectOption = {
    value: string;
    label: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  export let value = '';
  export let options: SelectOption[] = [];
  export let placeholder = '';
  export let disabled = false;
  export let onChange: (value: string) => void = () => {};
  let klass = '';
  export { klass as class };

  function handleChange() {
    onChange(value);
  }
</script>

<select
  bind:value
  {disabled}
  class={`select-field ${klass}`}
  on:change={handleChange}
  {...$$restProps}
>
  {#if placeholder}
    <option value="" disabled>{placeholder}</option>
  {/if}
  {#each options as option}
    <option value={option.value} disabled={option.disabled}
      >{option.label}</option
    >
  {/each}
</select>
