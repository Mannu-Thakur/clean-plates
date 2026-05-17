<script lang="ts">
  import { statusTone, titleCase } from '$lib/utils/format';

  export let value: string | boolean | null | undefined;
  export let compact = false;

  $: tone = statusTone(value);
  $: label =
    typeof value === 'boolean'
      ? value ? 'Active' : 'Inactive'
      : titleCase(value ?? 'unknown');

  $: toneClass =
    tone === 'good'    ? 'bg-up/10 text-up ring-up/20' :
    tone === 'warn'    ? 'bg-primary/10 text-primary ring-primary/20' :
    tone === 'bad'     ? 'bg-down/10 text-down ring-down/20' :
    tone === 'hot'     ? 'bg-primary/15 text-primary ring-primary/20' :
                         'bg-elevated text-muted ring-border';
</script>

<span
  class={`inline-flex max-w-full items-center gap-1.5 rounded-full font-semibold ring-1 ${toneClass} ${compact ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'}`}
>
  <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-current"></span>
  <span class="truncate">{label}</span>
</span>
