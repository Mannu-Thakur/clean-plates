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
    class={`relative h-6 w-11 rounded-full transition-colors ${value ? 'bg-primary' : 'bg-elevated'}`}
    type="button"
    role="switch"
    aria-checked={value}
    aria-label={label || 'Toggle'}
    {disabled}
    on:click={toggle}
  >
    <span
      class={`absolute top-1 h-4 w-4 rounded-full bg-on-dark transition-transform ${
        value ? 'translate-x-5' : 'translate-x-1'
      }`}
    ></span>
  </button>
  {#if label}
    <span class="text-sm font-medium text-body">{label}</span>
  {/if}
</label>
