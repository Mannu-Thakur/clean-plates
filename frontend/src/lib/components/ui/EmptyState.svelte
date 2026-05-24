<script lang="ts">
  import { Inbox } from '@lucide/svelte';

  export let title = 'No records yet';
  export let message = 'Records will appear here when data is available.';
</script>

<div
  class="flex min-h-48 flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-10 text-center"
>
  <Inbox class="text-muted" size={28} />
  <h3 class="mt-3 text-sm font-semibold text-body">{title}</h3>
  <p class="mt-1 max-w-md text-sm text-muted">{message}</p>
  <slot />
</div>
