import { mkdirSync, writeFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const OUT = 'e2e-artifacts/rehearsal';
const SINGLE_FILES = ['gem', 'rock', 'frame'];

test.beforeAll(() => mkdirSync(OUT, { recursive: true }));

test('native-scale captures and a pixel comparison of the drawn cells with the fixture PNGs', async ({ page, browser }) => {
  await page.goto('/rehearsal.html');
  await expect(page.getByTestId('rehearsal')).toHaveAttribute('data-settled', 'true');
  const generation = await page.getByTestId('rehearsal').getAttribute('data-generation');
  expect(generation).toMatch(/^sha256:/);

  const canvases = page.locator('canvas');
  await expect(canvases).toHaveCount(5);
  for (let i = 0; i < 4; i++) await canvases.nth(i).screenshot({ path: `${OUT}/cell-${i}.png` });
  await canvases.nth(4).screenshot({ path: `${OUT}/crowded-scene.png` });

  // The three image cells must hold exactly the fixture PNG's pixels (decoded by the browser, drawn 1:1, smoothing off).
  const comparison = await page.evaluate(async () => {
    const manifest = await (await fetch('/src/visualAssets/__fixtures__/rehearsal/runtime_manifest.json')).json();
    const cells = Array.from(document.querySelectorAll('canvas')).slice(0, 3);
    const keys = ['gem', 'rock', 'frame'].map((name) => `fixture.rehearsal.${name}`);
    const out: Record<string, { identical: boolean; differingPixels: number }> = {};
    for (let i = 0; i < 3; i++) {
      const entry = manifest.entries.find((e: { visual_key: string }) => e.visual_key === keys[i]);
      const bitmap = await createImageBitmap(await (await fetch(`/src/visualAssets/__fixtures__/rehearsal/${entry.file}`)).blob());
      const reference = new OffscreenCanvas(16, 16).getContext('2d')!;
      reference.drawImage(bitmap, 0, 0);
      const a = reference.getImageData(0, 0, 16, 16).data;
      const b = cells[i].getContext('2d')!.getImageData(0, 0, 16, 16).data;
      let differing = 0;
      for (let p = 0; p < a.length; p += 4) {
        const same = a[p + 3] === b[p + 3] && (a[p + 3] === 0 || (a[p] === b[p] && a[p + 1] === b[p + 1] && a[p + 2] === b[p + 2]));
        if (!same) differing++;
      }
      out[keys[i]] = { identical: differing === 0, differingPixels: differing };
    }
    return { cells: out, devicePixelRatio: window.devicePixelRatio, userAgent: navigator.userAgent };
  });
  for (const key of Object.keys(comparison.cells)) expect(comparison.cells[key].identical, key).toBe(true);
  expect(comparison.devicePixelRatio).toBe(1);

  writeFileSync(`${OUT}/evidence.json`, JSON.stringify({ browser: browser.browserType().name(), version: browser.version(), generation, singleFiles: SINGLE_FILES, ...comparison }, null, 2) + '\n');
});

for (const inject of ['missing', 'corrupt', 'invalid']) {
  test(`failure injection ${inject}: every affected cell shows its typed fallback, not an image`, async ({ page }) => {
    await page.goto(`/rehearsal.html?inject=${inject}`);
    await expect(page.getByTestId('rehearsal')).toHaveAttribute('data-settled', 'true');
    await page.locator('canvas').nth(4).screenshot({ path: `${OUT}/crowded-scene-${inject}.png` });
    const text = await page.getByTestId('cell-text').allTextContents();
    expect(text.join('\n')).toMatch(inject === 'missing' ? /image missing/ : inject === 'corrupt' ? /could not be decoded/ : /manifest invalid/);
  });
}
