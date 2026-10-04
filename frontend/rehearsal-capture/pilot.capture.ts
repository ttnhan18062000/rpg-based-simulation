import { mkdirSync, writeFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const FILL = [0x1b, 0x3a, 0x1b];
const CELL = 16;
// The predeclared layout (docs/assets/pilot_terrain_m5_criteria.md): forest cells with no marker on or next to them, from the layout formula.
const MARKERS: [number, number][] = [[1, 0], [4, 0], [9, 0], [6, 1], [0, 2], [1, 3], [2, 0], [7, 2]];
// a hero's glow (shadow blur) spills into the neighbouring cells, so cells next to a marker are not "clean" either
const nearMarker = (x: number, y: number) => MARKERS.some(([mx, my]) => Math.abs(mx - x) <= 1 && Math.abs(my - y) <= 1);
const terrain = (x: number, y: number) => [6, 6, 8, 9, 6, 7, 6, 17, 15, 6][(x + 3 * y) % 10];
const CLEAN_FOREST: [number, number][] = [];
for (let y = 0; y < 8; y++) for (let x = 0; x < 12; x++) if (terrain(x, y) === 6 && !nearMarker(x, y)) CLEAN_FOREST.push([x, y]);

test('pilot terrain: native-scale captures, tile pixels equal the export, flat control equals the fill', async ({ page, browser }, info) => {
  const out = `e2e-artifacts/pilot/${info.project.name}`;
  mkdirSync(out, { recursive: true });
  await page.goto('/rehearsal-pilot.html');
  await expect(page.getByTestId('pilot')).toHaveAttribute('data-settled', 'true');
  const generation = await page.getByTestId('pilot').getAttribute('data-generation');
  expect(generation).toMatch(/^sha256:/);

  const canvases = page.locator('canvas');
  await expect(canvases).toHaveCount(2);
  await canvases.nth(0).screenshot({ path: `${out}/pilot-image-scene.png` });
  await canvases.nth(1).screenshot({ path: `${out}/pilot-flat-control.png` });

  const evidence = await page.evaluate(async ({ cell, cleanForest }) => {
    const manifest = await (await fetch('/src/visualAssets/__fixtures__/pilot/runtime_manifest.json')).json();
    const entry = manifest.entries[0];
    const bitmap = await createImageBitmap(await (await fetch(`/src/visualAssets/__fixtures__/pilot/${entry.file}`)).blob());
    const reference = new OffscreenCanvas(cell, cell).getContext('2d')!;
    reference.drawImage(bitmap, 0, 0);
    const ref = reference.getImageData(0, 0, cell, cell).data;
    const [image, flat] = Array.from(document.querySelectorAll('canvas'));
    const ictx = image.getContext('2d')!;
    const fctx = flat.getContext('2d')!;
    // Forest cells hold the tile's pixels; the markers sit on some forest cells, so compare only forest cells without a marker.
    let tileDiffs = 0;
    let flatDiffs = 0;
    for (const [x, y] of cleanForest) {
      const a = ictx.getImageData(x * cell, y * cell, cell, cell).data;
      const b = fctx.getImageData(x * cell, y * cell, cell, cell).data;
      for (let p = 0; p < ref.length; p += 4) {
        if (a[p] !== ref[p] || a[p + 1] !== ref[p + 1] || a[p + 2] !== ref[p + 2] || a[p + 3] !== 255) tileDiffs++;
        if (b[p] !== 0x1b || b[p + 1] !== 0x3a || b[p + 2] !== 0x1b || b[p + 3] !== 255) flatDiffs++;
      }
    }
    return { cleanForestCellsChecked: cleanForest.length, tileDifferingPixels: tileDiffs, flatDifferingPixels: flatDiffs, devicePixelRatio: window.devicePixelRatio, userAgent: navigator.userAgent, canvasCss: [image.clientWidth, image.clientHeight] };
  }, { cell: CELL, cleanForest: CLEAN_FOREST });
  expect(evidence.cleanForestCellsChecked).toBe(CLEAN_FOREST.length);
  expect(CLEAN_FOREST.length).toBeGreaterThanOrEqual(15);
  expect(evidence.tileDifferingPixels).toBe(0);
  expect(evidence.flatDifferingPixels).toBe(0);
  expect(evidence.devicePixelRatio).toBe(info.project.use.deviceScaleFactor);

  writeFileSync(`${out}/evidence.json`, JSON.stringify({ project: info.project.name, browser: browser.browserType().name(), version: browser.version(), generation, ...evidence }, null, 2) + '\n');
});

for (const inject of ['missing', 'corrupt', 'invalid']) {
  test(`pilot failure injection ${inject}: the forest cells show exactly the flat fill`, async ({ page }, info) => {
    const out = `e2e-artifacts/pilot/${info.project.name}`;
    mkdirSync(out, { recursive: true });
    await page.goto(`/rehearsal-pilot.html?inject=${inject}`);
    await expect(page.getByTestId('pilot')).toHaveAttribute('data-settled', 'true');
    await page.locator('canvas').nth(0).screenshot({ path: `${out}/pilot-image-scene-${inject}.png` });
    const differing = await page.evaluate(({ fill, cells }) => {
      const ctx = (document.querySelectorAll('canvas')[0] as HTMLCanvasElement).getContext('2d')!;
      let count = 0;
      for (const [x, y] of cells) {
        const d = ctx.getImageData(x * 16, y * 16, 16, 16).data;
        for (let p = 0; p < d.length; p += 4) if (d[p] !== fill[0] || d[p + 1] !== fill[1] || d[p + 2] !== fill[2] || d[p + 3] !== 255) count++;
      }
      return count;
    }, { fill: FILL, cells: CLEAN_FOREST });
    expect(differing).toBe(0);
    if (inject === 'invalid') await expect(page.getByRole('alert')).toBeVisible();
  });
}
