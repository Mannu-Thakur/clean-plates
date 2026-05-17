<script lang="ts">
  import { afterUpdate, onDestroy, onMount, tick } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { ChartDataset, ChartType } from 'chart.js';
  import { Maximize2 } from '@lucide/svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Modal from '$lib/components/ui/Modal.svelte';
  import { CHART_COLORS, fillOf } from '$lib/utils/chartDefaults';

  export let title: string;
  export let description = '';
  export let chartType: ChartType = 'line';
  export let labels: string[] = [];
  export let datasets: ChartDataset[] = [];
  export let height = 280;
  export let expandable = false;
  export let horizontal = false;

  let canvas: HTMLCanvasElement;
  let expandedCanvas: HTMLCanvasElement;
  let chart: Chart | null = null;
  let expandedChart: Chart | null = null;
  let signature = '';
  let expanded = false;

  function chartConfig() {
    return {
      type: chartType,
      data: {
        labels,
        datasets: datasets.map((dataset, i) => ({
          borderColor: CHART_COLORS.series[i % CHART_COLORS.series.length],
          backgroundColor:
            chartType === 'doughnut' || chartType === 'pie'
              ? [...CHART_COLORS.series]
              : fillOf(CHART_COLORS.series[i % CHART_COLORS.series.length]),
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          ...dataset
        }))
      },
      options: {
        indexAxis: horizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, usePointStyle: true, color: '#eaecef' }
          }
        },
        scales:
          chartType === 'doughnut' || chartType === 'pie'
            ? {}
            : {
                x: {
                  grid: { display: horizontal },
                  ticks: { color: '#707a8a' },
                  border: { color: '#2b3139' }
                },
                y: {
                  beginAtZero: true,
                  grid: { color: '#2b3139', display: !horizontal },
                  ticks: { color: '#707a8a' },
                  border: { color: '#2b3139' }
                }
              }
      }
    } as const;
  }

  function render() {
    if (!canvas) return;
    chart?.destroy();
    chart = new Chart(canvas, chartConfig());
  }

  function renderExpanded() {
    if (!expandedCanvas) return;
    expandedChart?.destroy();
    expandedChart = new Chart(expandedCanvas, chartConfig());
  }

  async function openExpanded() {
    expanded = true;
    await tick();
    renderExpanded();
  }

  function closeExpanded() {
    expanded = false;
    expandedChart?.destroy();
    expandedChart = null;
  }

  onMount(render);

  afterUpdate(() => {
    const next = JSON.stringify({ chartType, labels, datasets });
    if (canvas && next !== signature) {
      signature = next;
      render();
      if (expanded) renderExpanded();
    }
  });

  onDestroy(() => {
    chart?.destroy();
    expandedChart?.destroy();
  });
</script>

<Card {title} {description}>
  <svelte:fragment slot="actions">
    {#if expandable}
      <button
        class="icon-btn"
        type="button"
        aria-label={`Expand ${title}`}
        title="Expand chart"
        on:click={openExpanded}
      >
        <Maximize2 size={16} />
      </button>
    {/if}
  </svelte:fragment>
  <div class="relative" style={`height:${height}px`}>
    <canvas bind:this={canvas} aria-label={title}></canvas>
  </div>
</Card>

<Modal open={expanded} {title} {description} wide on:close={closeExpanded}>
  <div class="relative" style="height:400px">
    <canvas bind:this={expandedCanvas} aria-label={`${title} expanded`}
    ></canvas>
  </div>
</Modal>
