<script lang="ts">
  import { onMount } from 'svelte';
  import { applyDarkChartDefaults } from '$lib/utils/chartDefaults';
  import '../app.css';

  onMount(() => {
    applyDarkChartDefaults();
  });
</script>

<slot />
