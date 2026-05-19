import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        canvas: 'rgb(var(--color-canvas) / <alpha-value>)',
        card: 'rgb(var(--color-card) / <alpha-value>)',
        elevated: 'rgb(var(--color-elevated) / <alpha-value>)',
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        'primary-hover': 'rgb(var(--color-primary-hover) / <alpha-value>)',
        'primary-disabled':
          'rgb(var(--color-primary-disabled) / <alpha-value>)',
        ink: 'rgb(var(--color-ink) / <alpha-value>)',
        body: 'rgb(var(--color-body) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        'muted-strong': 'rgb(var(--color-muted-strong) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        up: 'rgb(var(--color-up) / <alpha-value>)',
        down: 'rgb(var(--color-down) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
        'on-primary': 'rgb(var(--color-ink) / <alpha-value>)',
        'on-dark': 'rgb(var(--color-on-dark) / <alpha-value>)'
      },
      borderRadius: {
        xs: '2px',
        sm: '4px',
        md: '6px',
        lg: '8px',
        xl: '12px',
        pill: '9999px'
      },
      boxShadow: {
        'ring-primary': '0 0 0 2px rgba(252,213,53,0.25)',
        'ring-up': '0 0 0 2px rgba(14,203,129,0.25)',
        'ring-down': '0 0 0 2px rgba(246,70,93,0.25)',
        'ring-info': '0 0 0 2px rgba(59,130,246,0.25)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      }
    }
  },
  plugins: []
} satisfies Config;
