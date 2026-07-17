import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// The dashboard backend's confirmed serve port (8420) is AGENTOPS-BUILD-SERVE's
// to wire up; this dev-only default is a placeholder, override with
// VITE_DASHBOARD_API_TARGET for local development against a real backend.
const dashboardApiTarget = process.env.VITE_DASHBOARD_API_TARGET ?? 'http://127.0.0.1:8471'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: dashboardApiTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
