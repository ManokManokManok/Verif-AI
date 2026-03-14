import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    open: true,
    headers: {
      // Clickjacking protection
      'X-Frame-Options': 'DENY',
      // MIME-sniffing protection
      'X-Content-Type-Options': 'nosniff',
      // Content Security Policy (dev-mode friendly)
      'Content-Security-Policy': [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  // unsafe-* needed for Vite HMR
        "style-src 'self' 'unsafe-inline'",
        "connect-src 'self' ws://localhost:* http://localhost:8000",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "frame-ancestors 'none'",
      ].join('; '),
    },
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

