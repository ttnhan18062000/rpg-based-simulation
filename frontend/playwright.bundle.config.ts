import { defineConfig } from '@playwright/test';

// LOCAL ONLY, never in CI (`make visual-assets-bundle-capture`): the rehearsal harness pages captured from the BUILT bundle (`vite build` with
// vite.rehearsal-bundle.config.ts, then `vite preview`), not the dev server, so every image URL is the hashed `/assets/<name>-<hash>.png` a real build serves.
//
//   npx playwright test -c playwright.bundle.config.ts
//
// REHEARSAL_BUNDLE_PLANTED_DIR (set by tools/visual_assets_bundle_capture.py for the planted-asset proof) previews an already-built copy whose one fixture PNG was
// changed by one pixel, instead of building; the same spec must then FAIL its pixel check. Output goes to e2e-artifacts/ (gitignored).
const planted = process.env.REHEARSAL_BUNDLE_PLANTED_DIR;
const port = planted ? 5178 : 5177;

export default defineConfig({
  testDir: './rehearsal-capture',
  testMatch: '**/bundle.check.ts',
  timeout: 90_000,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${port}`,
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 1, // pinned: a HiDPI host must not turn one canvas pixel into several device pixels and fake a failure
    // REHEARSAL_CHROMIUM: path of an installed Chromium/Chrome when the one this Playwright expects is not installed
    launchOptions: { args: ['--no-sandbox'], executablePath: process.env.REHEARSAL_CHROMIUM || undefined },
  },
  webServer: {
    command: planted
      ? `npx vite preview --outDir ${planted} --port ${port} --strictPort`
      : `npx vite build -c vite.rehearsal-bundle.config.ts && npx vite preview --outDir e2e-artifacts/rehearsal-bundle --port ${port} --strictPort`,
    url: `http://localhost:${port}/rehearsal.html`,
    reuseExistingServer: false,
    timeout: 180_000,
  },
});
