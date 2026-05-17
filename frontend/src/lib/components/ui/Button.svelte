<script lang="ts">
  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  export let size: 'sm' | 'md' = 'md';
  export let disabled = false;
  let klass = '';
  export { klass as class };

  $: variantClass =
    variant === 'primary'
      ? 'border-fresh bg-fresh text-white hover:bg-fresh/90'
      : variant === 'danger'
        ? 'border-coral bg-coral text-white hover:bg-coral/90'
        : variant === 'ghost'
          ? 'border-transparent bg-transparent text-ink hover:bg-slate-100'
          : 'border-line bg-white text-ink hover:border-fresh hover:text-fresh';

  $: sizeClass = size === 'sm' ? 'h-9 px-3 text-xs' : 'h-10 px-4 text-sm';
</script>

<button
  {type}
  {disabled}
  class={`inline-flex items-center justify-center gap-2 rounded-md border font-semibold transition disabled:cursor-not-allowed disabled:opacity-55 ${variantClass} ${sizeClass} ${klass}`}
  {...$$restProps}
>
  <slot />
</button>
