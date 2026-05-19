import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const backend = process.env.CLEANPLATES_BACKEND_URL ?? 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: backend
      },
      '/static': {
        target: backend
      },
      '/health': {
        target: backend
      },
      '/ws': {
        target: backend.replace(/^http/, 'ws'),
        ws: true
      }
    }
  }
});
