import { defineConfig } from '@playwright/test';

// LOCAL ONLY, never in CI (AM-M5 surface rehearsal): opens the dev-only page frontend/rehearsal.html on a plain Vite dev server
// (not `make dev`: no backend, no simulation) and saves native-scale captures for a human to look at, plus a small evidence JSON
// (browser version, device pixel ratio, pixel comparison of the drawn cells against the fixture PNGs).
//
//   npx playwright test -c playwright.rehearsal.config.ts
//
// Output goes to e2e-artifacts/rehearsal/ (gitignored). Same environment notes as playwright.config.ts for installing Chromium.
export default defineConfig({
  testDir: './rehearsal-capture',
  testMatch: '**/*.capture.ts',
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5174',
    viewport: { width: 480, height: 480 },
    deviceScaleFactor: 1, // native scale: one canvas pixel is one device pixel
    // REHEARSAL_CHROMIUM: path of an installed Chromium when the one this Playwright expects is not (e.g. an older cached build)
    launchOptions: { args: ['--no-sandbox'], executablePath: process.env.REHEARSAL_CHROMIUM || undefined },
  },
  webServer: {
    command: 'npx vite --port 5174 --strictPort',
    url: 'http://localhost:5174/rehearsal.html',
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
