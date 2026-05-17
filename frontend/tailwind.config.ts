import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#172026',
        panel: '#ffffff',
        muted: '#667085',
        line: '#d8e0e8',
        field: '#f6f8fb',
        fresh: '#188a6b',
        lime: '#84a83b',
        amber: '#c77700',
        coral: '#d95d54',
        sky: '#1677a8'
      },
      boxShadow: {
        soft: '0 18px 60px rgba(23, 32, 38, 0.08)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
} satisfies Config;
