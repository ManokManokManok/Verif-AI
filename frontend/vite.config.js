import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    open: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.js'],
    css: true,
    include: ['tests/**/*.{test,spec}.{js,jsx}'],
    watch: false, // Disable watch mode by default - use --watch to enable
  },
});

