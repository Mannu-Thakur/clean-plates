import { defaults } from 'chart.js';

/**
 * Apply Binance-reference dark theme defaults to all Chart.js instances.
 * Call once in the root +layout.svelte on mount.
 */
export function applyDarkChartDefaults() {
  defaults.color                              = '#707a8a';   // muted — axis labels
  defaults.borderColor                        = '#2b3139';   // border — grid lines
  defaults.font.family                        = 'Inter, ui-sans-serif, system-ui, sans-serif';
  defaults.plugins.legend.labels.color        = '#eaecef';   // body — legend text
  // @ts-expect-error Chart.js type gap for scale defaults
  defaults.scale = {
    ...(defaults.scale ?? {}),
    grid:  { color: '#2b3139' },
    ticks: { color: '#707a8a' },
  };
}

/** Standard dataset color palette — Binance reference */
export const CHART_COLORS = {
  primary: '#fcd535',
  up:      '#0ecb81',
  down:    '#f6465d',
  info:    '#3b82f6',
  muted:   '#707a8a',
  series:  ['#fcd535', '#0ecb81', '#3b82f6', '#f6465d', '#707a8a', '#929aa5'],
} as const;

/** Returns a 20% opacity fill color from a hex stroke color */
export function fillOf(hex: string): string {
  return `${hex}33`;
}
