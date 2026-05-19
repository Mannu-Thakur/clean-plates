<script lang="ts">
  export let value = false;
  export let onChange: (value: boolean) => void = () => {};
  export let disabled = false;
  export let label = '';

  function toggle() {
    if (disabled) return;
    value = !value;
    onChange(value);
  }
</script>

<label
  class={`inline-flex items-center gap-3 ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
>
  <button
    class={`relative h-6 w-11 shrink-0 p-0 rounded-full transition-colors border ${
      value ? 'bg-primary border-primary' : 'bg-elevated border-border'
    }`}
    type="button"
    role="switch"
    aria-checked={value}
    aria-label={label || 'Toggle'}
    {disabled}
    on:click={toggle}
  >
    <span
      class={`absolute left-[3px] top-[3px] h-4 w-4 rounded-full bg-on-dark transition-transform ${
        value ? 'translate-x-5' : 'translate-x-0'
      }`}
    ></span>
  </button>
  {#if label}
    <span class="text-sm font-medium text-body">{label}</span>
  {/if}
</label>
