import { defineConfig, configDefaults } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
      '/openapi.json': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/redoc': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    // e2e/ holds Playwright specs (run via `npx playwright test`, its own runner) -- Vitest's
    // default include glob otherwise picks up *.spec.ts anywhere in the project and tries to
    // execute them itself, which fails hard: @playwright/test's own test() aborts when it isn't
    // invoked from inside Playwright's own runner ("Playwright Test did not expect test() to be
    // called here"), live-confirmed on TCK-20260825-LIVE-VERIFICATION-TOOLING's own CI run.
    exclude: [...configDefaults.exclude, 'e2e/**'],
  }
})
