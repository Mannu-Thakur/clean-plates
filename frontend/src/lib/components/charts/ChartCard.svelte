<script lang="ts">
  import { afterUpdate, onDestroy, onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { ChartDataset, ChartType } from 'chart.js';
  import Card from '$lib/components/ui/Card.svelte';
  import { CHART_COLORS, fillOf } from '$lib/utils/chartDefaults';

  export let title: string;
  export let description = '';
  export let chartType: ChartType = 'line';
  export let labels: string[] = [];
  export let datasets: ChartDataset[] = [];
  export let height = 280;

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;
  let signature = '';

  function render() {
    if (!canvas) return;
    chart?.destroy();
    chart = new Chart(canvas, {
      type: chartType,
      data: {
        labels,
        datasets: datasets.map((dataset, i) => ({
          borderColor:     CHART_COLORS.series[i % CHART_COLORS.series.length],
          backgroundColor:
            chartType === 'doughnut' || chartType === 'pie'
              ? [...CHART_COLORS.series]
              : fillOf(CHART_COLORS.series[i % CHART_COLORS.series.length]),
          tension:     0.35,
          borderWidth: 2,
          pointRadius: 3,
          ...dataset,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, usePointStyle: true, color: '#eaecef' },
          },
        },
        scales:
          chartType === 'doughnut' || chartType === 'pie'
            ? {}
            : {
                x: {
                  grid:  { display: false },
                  ticks: { color: '#707a8a' },
                  border: { color: '#2b3139' },
                },
                y: {
                  beginAtZero: true,
                  grid:  { color: '#2b3139' },
                  ticks: { color: '#707a8a' },
                  border: { color: '#2b3139' },
                },
              },
      },
    });
  }

  onMount(render);

  afterUpdate(() => {
    const next = JSON.stringify({ chartType, labels, datasets });
    if (canvas && next !== signature) {
      signature = next;
      render();
    }
  });

  onDestroy(() => chart?.destroy());
</script>

<Card {title} {description}>
  <div class="relative" style={`height:${height}px`}>
    <canvas bind:this={canvas} aria-label={title}></canvas>
  </div>
</Card>
