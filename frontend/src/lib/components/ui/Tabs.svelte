<script lang="ts" context="module">
  export type TabItem = {
    id: string;
    label: string;
    icon?: any;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  export let tabs: TabItem[] = [];
  export let active = '';
  export let onChange: (id: string) => void = () => {};
</script>

<div class="border-b border-border" role="tablist">
  <div class="flex gap-5 overflow-x-auto">
    {#each tabs as tab}
      <button
        class={`inline-flex h-11 shrink-0 items-center gap-2 border-b-2 text-sm font-semibold transition-colors ${
          active === tab.id
            ? 'border-primary text-body'
            : 'border-transparent text-muted hover:text-body'
        }`}
        type="button"
        role="tab"
        aria-selected={active === tab.id}
        disabled={tab.disabled}
        on:click={() => onChange(tab.id)}
      >
        {#if tab.icon}
          <svelte:component this={tab.icon} size={16} />
        {/if}
        {tab.label}
      </button>
    {/each}
  </div>
</div>
