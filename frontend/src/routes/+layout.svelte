<script lang="ts">
  import { onMount } from 'svelte';
  import { applyDarkChartDefaults } from '$lib/utils/chartDefaults';
  import { applyTheme, readTheme } from '$lib/stores/theme';
  import '../app.css';

  onMount(() => {
    applyTheme(readTheme());
    applyDarkChartDefaults();
  });
</script>

<slot />
