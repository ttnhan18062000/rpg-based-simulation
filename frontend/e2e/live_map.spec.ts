import { test, expect } from '@playwright/test';

// Real, headless-browser confirmation that the live map actually renders through the exact
// `make dev` golden path -- the gap TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX's own fixes
// (Vite WS proxy, dev API key, non-blocking metadata fallback) could only be verified for up to
// the browser boundary (component tests + raw WS/curl clients), never by an actual page load.
// This closes that gap and is meant to be re-run any time the live-map golden path needs live
// re-confirmation, not a one-shot investigation script -- see playwright.config.ts's header
// comment for the NODE_EXTRA_CA_CERTS environment note this sandbox needed to install Chromium.

test('live map renders real terrain and live ticking data through make dev', async ({ page }) => {
  await page.goto('/');

  // Neither blocking screen (the loading gate, or the pre-fix metadata hard-block) should be
  // stuck once the app has had a real chance to load -- both must clear.
  await expect(page.getByText('Loading game data…')).toHaveCount(0, { timeout: 15_000 });
  await expect(page.getByText(/Failed to load game metadata/)).toHaveCount(0);

  // The terrain grid canvas must exist and actually have non-blank pixel content -- this is the
  // real assertion that GameCanvas received and rendered mapData, not just that the DOM node
  // exists (a canvas with zero draws is indistinguishable from a broken one by presence alone).
  const gridCanvas = page.locator('canvas').first();
  await expect(gridCanvas).toBeVisible({ timeout: 15_000 });

  const hasNonBlankPixels = await gridCanvas.evaluate((canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d');
    if (!ctx || canvas.width === 0 || canvas.height === 0) return false;
    const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
    // Any non-zero-alpha, non-uniform-black pixel is enough to prove a real draw happened --
    // terrain tiles are colored, an untouched canvas is fully transparent/black.
    for (let i = 0; i < data.length; i += 4) {
      if (data[i] !== 0 || data[i + 1] !== 0 || data[i + 2] !== 0 || data[i + 3] !== 0) {
        return true;
      }
    }
    return false;
  });
  expect(hasNonBlankPixels).toBe(true);

  // Live-ticking proof: the Header's "Tick: N" must actually increase over time, not just
  // display a static initial value -- this is the WS delta stream reaching the UI for real.
  const tickText = page.getByText(/^Tick:/);
  await expect(tickText).toBeVisible({ timeout: 15_000 });

  async function readTick(): Promise<number> {
    const text = await tickText.textContent();
    const match = text?.match(/Tick:\s*(\d+)/);
    if (!match) throw new Error(`could not parse tick from "${text}"`);
    return parseInt(match[1], 10);
  }

  const firstTick = await readTick();
  await expect
    .poll(readTick, { timeout: 15_000, message: 'tick count never advanced past its initial value' })
    .toBeGreaterThan(firstTick);

  await page.screenshot({ path: 'e2e-artifacts/live_map_render.png' });
});
