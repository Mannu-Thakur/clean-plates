<script lang="ts">
  import { Upload, X } from '@lucide/svelte';
  import { notify } from '$lib/stores/toast';

  export let accept = '';
  export let maxSizeMb = 10;
  export let onSelect: (file: File) => void = () => {};
  export let onClear: () => void = () => {};
  export let label = 'Upload file';
  export let uploading = false;

  let input: HTMLInputElement;
  let dragging = false;
  let selected: File | null = null;

  function validate(file: File) {
    if (file.size > maxSizeMb * 1024 * 1024) {
      notify(`File must be ${maxSizeMb}MB or smaller.`, 'error');
      return false;
    }
    return true;
  }

  function choose(file: File | undefined) {
    if (!file || !validate(file)) return;
    selected = file;
    onSelect(file);
  }

  function handleDrop(event: DragEvent) {
    dragging = false;
    choose(event.dataTransfer?.files?.[0]);
  }

  function clear() {
    selected = null;
    if (input) input.value = '';
    onClear();
  }
</script>

<div class="space-y-3">
  <button
    class={`flex w-full flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-6 text-center transition-colors ${
      dragging
        ? 'border-primary bg-primary/10'
        : 'border-border bg-card hover:bg-elevated'
    }`}
    type="button"
    disabled={uploading}
    on:click={() => input?.click()}
    on:dragenter|preventDefault={() => (dragging = true)}
    on:dragover|preventDefault={() => (dragging = true)}
    on:dragleave|preventDefault={() => (dragging = false)}
    on:drop|preventDefault={handleDrop}
  >
    <span
      class="grid h-10 w-10 place-items-center rounded-md bg-elevated text-primary"
    >
      <Upload size={18} />
    </span>
      <span class="min-w-0">
        <span class="block text-sm font-semibold text-body">{label}</span>
        <span class="mt-1 block text-xs text-muted"
          >Drop a file here or browse. Max {maxSizeMb}MB.</span
      >
    </span>
  </button>

  <input
    bind:this={input}
    class="hidden"
    type="file"
    {accept}
    on:change={(event) =>
      choose((event.currentTarget as HTMLInputElement).files?.[0])}
  />

  {#if selected}
    <div
      class="flex items-center justify-between gap-3 rounded-md border border-border bg-elevated px-3 py-2 text-sm"
    >
      <span class="min-w-0 truncate text-body">{selected.name}</span>
      <button
        class="text-muted transition-colors hover:text-body"
        type="button"
        aria-label="Clear file"
        on:click={clear}
      >
        <X size={16} />
      </button>
    </div>
  {/if}
</div>
