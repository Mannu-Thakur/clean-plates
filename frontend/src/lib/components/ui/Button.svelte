<script lang="ts">
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  export let size: 'sm' | 'md' = 'md';
  export let disabled = false;
  let klass = '';
  export { klass as class };

  $: baseClass =
    variant === 'primary'
      ? 'btn-primary'
      : variant === 'danger'
        ? 'btn-danger'
        : variant === 'ghost'
          ? 'btn-ghost'
          : 'btn-secondary';

  $: sizeExtra = size === 'sm' ? 'btn-sm' : '';
</script>

<button
  {type}
  {disabled}
  class={`${baseClass} ${sizeExtra} ${klass}`}
  on:click
  {...$$restProps}
>
  <slot />
</button>
