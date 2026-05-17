import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        // ── Binance-reference dark palette ─────────────────────────
        canvas: '#0b0e11', // page background — flat, NO gradient
        card: '#1e2329', // cards, panels, modals, aside nav
        elevated: '#2b3139', // table headers, dropdowns, dividers
        primary: '#fcd535', // ALL CTAs, active nav, brand
        'primary-hover': '#f0b90b', // button hover/active
        'primary-disabled': '#3a3a1f', // disabled CTA background
        ink: '#181a20', // text ON primary (on yellow buttons)
        body: '#eaecef', // primary text on dark surfaces
        muted: '#707a8a', // labels, secondary text, placeholders
        'muted-strong': '#929aa5', // strong muted, icon hints
        border: '#2b3139', // all borders on dark (hairline)
        up: '#0ecb81', // success, online, positive delta
        down: '#f6465d', // error, offline, negative delta
        info: '#3b82f6', // info badges, help indicators
        'on-primary': '#181a20', // same as ink — text on yellow
        'on-dark': '#ffffff' // white text
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
        // ONLY focus rings — NO surface shadows
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
