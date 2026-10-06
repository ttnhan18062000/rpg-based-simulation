import { defineConfig } from '@playwright/test';

// LOCAL ONLY, never in CI (AM-M5 whole-map terrain-set rehearsal, AM5-W03-SET / AM5-W07): opens the dev-only page frontend/rehearsal-map.html on a plain Vite dev server
// (not `make dev`: no backend, no simulation) in each client of the matrix the user approved on 2026-10-04 (docs/assets/pilot_terrain_m5_results.md):
// Playwright Chromium and the system Google Chrome, each at device pixel ratio 1 and 2. Firefox is NOT in the matrix and is not run.
//
//   npx playwright test -c playwright.map.config.ts
//
// PILOT_CHROMIUM: path of an installed Playwright Chromium when the build this Playwright expects is not installed (an older cached build); its exact
// version is recorded in each evidence JSON, so nothing is claimed beyond what ran. Without it the Playwright default is used.//
// Output goes to e2e-artifacts/map/<project>/ (gitignored): native-scale captures for a human plus an evidence JSON per client.
export default defineConfig({
  testDir: './rehearsal-capture',
  testMatch: '**/map.capture.ts',
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5176',
    viewport: { width: 700, height: 1000 },
    launchOptions: { args: ['--no-sandbox'] },
  },
  projects: [
    { name: 'chromium-dpr1', use: { browserName: 'chromium', deviceScaleFactor: 1, launchOptions: { args: ['--no-sandbox'], executablePath: process.env.PILOT_CHROMIUM || undefined } } },
    { name: 'chromium-dpr2', use: { browserName: 'chromium', deviceScaleFactor: 2, launchOptions: { args: ['--no-sandbox'], executablePath: process.env.PILOT_CHROMIUM || undefined } } },
    { name: 'chrome-dpr1', use: { browserName: 'chromium', channel: 'chrome', deviceScaleFactor: 1 } },
    { name: 'chrome-dpr2', use: { browserName: 'chromium', channel: 'chrome', deviceScaleFactor: 2 } },
  ],
  webServer: {
    command: 'npx vite --port 5176 --strictPort',
    url: 'http://localhost:5176/rehearsal-map.html',
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
