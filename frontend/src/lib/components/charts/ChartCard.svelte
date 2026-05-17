<script lang="ts">
  import { afterUpdate, onDestroy, onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { ChartDataset, ChartType } from 'chart.js';
  import Card from '$lib/components/ui/Card.svelte';

  export let title: string;
  export let description = '';
  export let chartType: ChartType = 'line';
  export let labels: string[] = [];
  export let datasets: ChartDataset[] = [];
  export let height = 280;

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;
  let signature = '';

  const palette = [
    '#188a6b',
    '#1677a8',
    '#c77700',
    '#d95d54',
    '#84a83b',
    '#475467'
  ];

  function render() {
    if (!canvas) return;
    chart?.destroy();
    chart = new Chart(canvas, {
      type: chartType,
      data: {
        labels,
        datasets: datasets.map((dataset, index) => ({
          borderColor: palette[index % palette.length],
          backgroundColor:
            chartType === 'doughnut'
              ? palette
              : `${palette[index % palette.length]}26`,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          ...dataset
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, usePointStyle: true }
          }
        },
        scales:
          chartType === 'doughnut' || chartType === 'pie'
            ? {}
            : {
                x: { grid: { display: false }, ticks: { color: '#667085' } },
                y: {
                  beginAtZero: true,
                  grid: { color: '#edf2f6' },
                  ticks: { color: '#667085' }
                }
              }
      }
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
