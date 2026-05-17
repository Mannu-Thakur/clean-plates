<script lang="ts">
  import { statusTone, titleCase } from '$lib/utils/format';

  export let value: string | boolean | null | undefined;
  export let compact = false;

  $: tone = statusTone(value);
  $: label =
    typeof value === 'boolean'
      ? value
        ? 'Active'
        : 'Inactive'
      : titleCase(value ?? 'unknown');
  $: toneClass =
    tone === 'good'
      ? 'bg-fresh/10 text-fresh ring-fresh/20'
      : tone === 'warn'
        ? 'bg-amber/10 text-amber ring-amber/20'
        : tone === 'bad'
          ? 'bg-coral/10 text-coral ring-coral/20'
          : tone === 'hot'
            ? 'bg-orange-100 text-orange-700 ring-orange-200'
            : 'bg-slate-100 text-slate-600 ring-slate-200';
</script>

<span
  class={`inline-flex max-w-full items-center gap-1.5 rounded-full font-semibold ring-1 ${toneClass} ${compact ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'}`}
>
  <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-current"></span>
  <span class="truncate">{label}</span>
</span>
