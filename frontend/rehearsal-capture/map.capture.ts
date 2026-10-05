import { mkdirSync, writeFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

// LOCAL ONLY (never in CI): native-scale captures of the whole-map terrain-set scene for the owner's W03-SET review, in each client of the AM5-W07 matrix, with borders ON and OFF,
// plus an evidence JSON of what the page really drew. The map is 40 x 24 cells of 16 px (docs/assets/pilot_terrain_m5_criteria.md, AM5-W03-SET).
const CELL = 16;
const COLUMNS = 40;
const ROWS = 24;

test('whole map: captures with borders on and off, fringes stay within 4 px, flat control equals the fills', async ({ page, browser }, info) => {
  const out = `e2e-artifacts/map/${info.project.name}`;
  mkdirSync(out, { recursive: true });
  await page.goto('/rehearsal-map.html');
  await expect(page.getByTestId('map')).toHaveAttribute('data-settled', 'true');
  const generation = await page.getByTestId('map').getAttribute('data-generation');
  expect(generation).toMatch(/^sha256:/);
  const canvases = page.locator('canvas');
  await expect(canvases).toHaveCount(2);

  await expect(page.getByTestId('map')).toHaveAttribute('data-borders', 'true');
  const fringed = Number(await page.getByTestId('map').getAttribute('data-fringed'));
  expect(fringed).toBeGreaterThan(100);
  await canvases.nth(0).screenshot({ path: `${out}/map-image-borders-on.png` });
  await canvases.nth(1).screenshot({ path: `${out}/map-flat-control.png` });
  const on = await page.evaluate(() => { const c = document.querySelectorAll('canvas')[0] as HTMLCanvasElement; return Array.from(c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data); });

  await page.getByTestId('map-borders').uncheck();
  await expect(page.getByTestId('map')).toHaveAttribute('data-borders', 'false');
  await expect(page.getByTestId('map')).toHaveAttribute('data-fringed', '0');
  await canvases.nth(0).screenshot({ path: `${out}/map-image-borders-off.png` });
  const off = await page.evaluate(() => { const c = document.querySelectorAll('canvas')[0] as HTMLCanvasElement; return Array.from(c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data); });
  expect(on.length).toBe(off.length);

  // Fringes only ever change pixels within 4 px of a cell edge (the cell centre always shows its own terrain); markers draw over cells so cells near a marker are skipped.
  const width = COLUMNS * CELL;
  let changedCells = 0;
  let centreDiffs = 0;
  let outerDiffs = 0;
  for (let cy = 0; cy < ROWS; cy++) {
    for (let cx = 0; cx < COLUMNS; cx++) {
      let cellChanged = false;
      for (let y = 0; y < CELL; y++) {
        for (let x = 0; x < CELL; x++) {
          const i = ((cy * CELL + y) * width + cx * CELL + x) * 4;
          const same = on[i] === off[i] && on[i + 1] === off[i + 1] && on[i + 2] === off[i + 2];
          if (same) continue;
          cellChanged = true;
          if (Math.min(x, y, CELL - 1 - x, CELL - 1 - y) < 4) outerDiffs++; else centreDiffs++;
        }
      }
      if (cellChanged) changedCells++;
    }
  }
  expect(centreDiffs).toBe(0);
  expect(outerDiffs).toBeGreaterThan(0);

  const flat = await page.evaluate(() => { const c = document.querySelectorAll('canvas')[1] as HTMLCanvasElement; return Array.from(c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data); });
  const dpr = await page.evaluate(() => window.devicePixelRatio);
  expect(dpr).toBe(info.project.use.deviceScaleFactor);
  writeFileSync(`${out}/evidence.json`, JSON.stringify({
    project: info.project.name, browser: browser.browserType().name(), version: browser.version(), generation, devicePixelRatio: dpr,
    fringedCellsReportedByPage: fringed, cellsWhoseOuterRingChanged: changedCells, pixelsChangedWithin4pxOfEdge: outerDiffs, pixelsChangedInCellCentre: centreDiffs,
    flatControlDistinctColours: new Set(Array.from({ length: flat.length / 4 }, (_, p) => `${flat[p * 4]},${flat[p * 4 + 1]},${flat[p * 4 + 2]}`)).size,
  }, null, 2) + '\n');
});

for (const inject of ['missing', 'corrupt', 'invalid']) {
  test(`map failure injection ${inject}: nothing blank or broken`, async ({ page }, info) => {
    const out = `e2e-artifacts/map/${info.project.name}`;
    mkdirSync(out, { recursive: true });
    await page.goto(`/rehearsal-map.html?inject=${inject}`);
    await expect(page.getByTestId('map')).toHaveAttribute('data-settled', 'true');
    await page.locator('canvas').nth(0).screenshot({ path: `${out}/map-image-${inject}.png` });
    const status = await page.getByTestId('map-status').textContent();
    if (inject === 'missing') expect(status).toMatch(/Borders on: 0 map cells carry a fringe/); // every border mask absent from the build: today's hard edge
    if (inject === 'invalid') await expect(page.getByRole('alert')).toBeVisible();
    // no cell of the image canvas is fully transparent (never a blank cell)
    const blank = await page.evaluate(() => {
      const c = document.querySelectorAll('canvas')[0] as HTMLCanvasElement; const d = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data; let n = 0;
      for (let p = 3; p < d.length; p += 4) if (d[p] === 0) n++;
      return n;
    });
    if (inject !== 'invalid') expect(blank).toBe(0);
  });
}
