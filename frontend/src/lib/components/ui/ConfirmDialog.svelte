<script lang="ts">
  import { tick } from 'svelte';
  import Modal from './Modal.svelte';

  export let open = false;
  export let title = 'Confirm action';
  export let message = '';
  export let confirmLabel = 'Confirm';
  export let danger = false;
  export let onConfirm: () => void = () => {};
  export let onCancel: () => void = () => {};

  let cancelButton: HTMLButtonElement;
  let confirmButton: HTMLButtonElement;

  $: if (open) focusCancel();

  async function focusCancel() {
    await tick();
    cancelButton?.focus();
  }

  function handleKeydown(event: KeyboardEvent) {
    if (!open) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      onCancel();
    }
    if (event.key === 'Tab') {
      const active = document.activeElement;
      if (event.shiftKey && active === cancelButton) {
        event.preventDefault();
        confirmButton?.focus();
      } else if (!event.shiftKey && active === confirmButton) {
        event.preventDefault();
        cancelButton?.focus();
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<Modal {open} {title} on:close={onCancel}>
  <div class="space-y-5">
    <p class="text-sm leading-6 text-muted-strong">{message}</p>
    <div class="flex flex-wrap justify-end gap-2">
      <button
        bind:this={cancelButton}
        class="btn-secondary"
        type="button"
        on:click={onCancel}>Cancel</button
      >
      <button
        bind:this={confirmButton}
        class={danger ? 'btn-danger' : 'btn-primary'}
        type="button"
        on:click={onConfirm}
      >
        {confirmLabel}
      </button>
    </div>
  </div>
</Modal>
