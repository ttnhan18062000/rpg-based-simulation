import { defineConfig } from '@playwright/test';

// Live, real-browser end-to-end check of the live map through the exact `make dev` golden path
// (TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX fixed the WS-proxy/auth/metadata-block bugs
// this suite exists to guard against regressing). Headless Chromium is the only browser this
// project verifies against -- no Firefox/WebKit projects are configured, since this is a
// same-origin-proxy dev-server smoke check, not cross-browser compatibility testing.
//
// Environment note (this sandbox, and possibly others behind a TLS-intercepting proxy): the
// default `chromium-headless-shell` binary `npx playwright install` tries to fetch may fail with
// `UNABLE_TO_VERIFY_LEAF_SIGNATURE` unless NODE_EXTRA_CA_CERTS points at the system CA bundle,
// e.g. `NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt npx playwright install chromium`.
// Once installed, running the tests needs no special env.
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
    launchOptions: {
      // --no-sandbox: this sandbox has no user-namespace support for Chromium's setuid
      // sandbox; harmless to keep everywhere since this suite never opens untrusted content.
      args: ['--no-sandbox'],
    },
  },
  webServer: {
    // Reuses the exact same golden path this suite is guarding -- not a parallel/simplified
    // start-up sequence that could drift from what a real developer actually runs.
    command: 'cd .. && make dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
