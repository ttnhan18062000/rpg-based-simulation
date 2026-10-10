import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { pixelsV1Hash } from '../src/visualAssets/pixelsV1';

// LOCAL ONLY (never in CI): the dev-only rehearsal pages captured from the BUILT bundle (`vite build` + `vite preview`).
// Per page it records that every image loaded from a hashed `/assets/<64 hex>-<hash>.png` URL (and nothing from the dev server's /src), and for rehearsal.html ONLY it hashes what the
// three image cells really drew with the store's own `pixels-v1` hash (src/visualAssets/pixelsV1.ts, proven equal to the Python hash on known vectors) and compares it with the
// committed fixture manifest's pixel hashes. The other pages carry no pixel verdict: they are asset-loading evidence only. No gate result moves.
//
// The evidence is written BEFORE the assertions so a failing run (the planted-asset proof) still leaves what it saw.
const FIXTURES = 'src/visualAssets/__fixtures__';
const OUT = process.env.REHEARSAL_BUNDLE_EVIDENCE_OUT || 'e2e-artifacts/rehearsal-bundle-evidence/evidence.json';
const HASHED_PNG = /^\/assets\/([0-9a-f]{64})-[A-Za-z0-9_-]{8}\.png$/;
const DEV_SERVER_PATH = /^\/(src\/|@vite|@react-refresh|node_modules\/)/;

interface PageSpec { name: string; path: string; settle: { testId: string } | { images: true }; pixelCells?: string[] }
const PAGES: PageSpec[] = [
  { name: 'rehearsal', path: '/rehearsal.html', settle: { testId: 'rehearsal' }, pixelCells: ['gem', 'rock', 'frame'] },
  { name: 'pilot', path: '/rehearsal-pilot.html', settle: { testId: 'pilot' } },
  { name: 'map', path: '/rehearsal-map.html', settle: { testId: 'map' } },
  { name: 'icons', path: '/rehearsal-icons.html', settle: { images: true } },
  { name: 'draft', path: '/rehearsal-draft.html', settle: { testId: 'draft-page' } },
];

// every committed fixture PNG name (`<64 hex>.png`), across all the fixture folders
const knownFixtureFiles = new Set<string>();
for (const dir of readdirSync(FIXTURES, { withFileTypes: true })) {
  if (dir.isDirectory()) for (const f of readdirSync(path.join(FIXTURES, dir.name))) if (f.endsWith('.png')) knownFixtureFiles.add(f);
}
const rehearsalManifest = JSON.parse(readFileSync(`${FIXTURES}/rehearsal/runtime_manifest.json`, 'utf8')) as { entries: { visual_key: string; file: string; width: number; height: number; pixel_hash: string }[] };

interface PixelVerdict { expected: string; drawn: string; identical: boolean; scale: number | null; note?: string }
interface PageEvidence {
  page: string; settled: string; image_urls: string[]; all_images_hashed: boolean; unknown_fixture_files: string[]; dev_server_requests: string[]; failed_requests: string[]; data_url_images: number;
  pixel_verified: boolean; pixel_verdicts: Record<string, PixelVerdict> | null;
}

test('every rehearsal page loads from the built bundle; rehearsal.html draws exactly the stored artifacts', async ({ page, browser }) => {
  const pages: PageEvidence[] = [];
  let devicePixelRatio = 0;
  for (const spec of PAGES) {
    const requests: { pathname: string; status: number }[] = [];
    const listener = (r: import('@playwright/test').Response) => requests.push({ pathname: new URL(r.url()).pathname, status: r.status() });
    page.on('response', listener);
    await page.goto(spec.path);
    let settled: string;
    if ('testId' in spec.settle) {
      await expect(page.getByTestId(spec.settle.testId)).toHaveAttribute('data-settled', 'true');
      settled = `data-settled=true on [data-testid=${spec.settle.testId}]`;
    } else {
      await page.waitForLoadState('networkidle');
      await expect(page.locator('img').first()).toBeVisible();
      settled = 'network idle and an image is visible (this page has no data-settled marker)';
    }
    page.off('response', listener);

    const pngs = [...new Set(requests.filter((r) => r.pathname.endsWith('.png')).map((r) => r.pathname))].sort();
    const stems = pngs.map((p) => HASHED_PNG.exec(p)?.[1]);
    const dataUrlImages = await page.evaluate(() => Array.from(document.querySelectorAll('img')).filter((i) => i.src.startsWith('data:')).length);
    const evidence: PageEvidence = {
      page: spec.name, settled, image_urls: pngs,
      all_images_hashed: pngs.length > 0 && stems.every((s) => s !== undefined),
      unknown_fixture_files: pngs.filter((p, i) => stems[i] !== undefined && !knownFixtureFiles.has(`${stems[i]}.png`)),
      dev_server_requests: [...new Set(requests.map((r) => r.pathname).filter((p) => DEV_SERVER_PATH.test(p)))].sort(),
      failed_requests: requests.filter((r) => r.status >= 400).map((r) => `${r.status} ${r.pathname}`),
      data_url_images: dataUrlImages, pixel_verified: false, pixel_verdicts: null,
    };

    if (spec.pixelCells) {
      devicePixelRatio = await page.evaluate(() => window.devicePixelRatio);
      const drawn = await page.evaluate((count) => Array.from(document.querySelectorAll('canvas')).slice(0, count).map((c) => ({
        width: c.width, height: c.height, rgba: Array.from(c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data),
      })), spec.pixelCells.length);
      const verdicts: Record<string, PixelVerdict> = {};
      for (let i = 0; i < spec.pixelCells.length; i++) {
        const key = `fixture.rehearsal.${spec.pixelCells[i]}`;
        const entry = rehearsalManifest.entries.find((e) => e.visual_key === key)!;
        const cell = drawn[i];
        const scale = cell && cell.width % entry.width === 0 && cell.height % entry.height === 0 && cell.width / entry.width === cell.height / entry.height ? cell.width / entry.width : null;
        if (scale === null) { verdicts[key] = { expected: entry.pixel_hash, drawn: 'none', identical: false, scale: null, note: 'the cell is not a whole-number multiple of the artifact size' }; continue; }
        // sample the page's own integer scale with smoothing off: the top-left pixel of each scale x scale block, and every block must be uniform
        const small: number[] = [];
        let uniform = true;
        for (let y = 0; y < entry.height; y++) for (let x = 0; x < entry.width; x++) {
          const at = (yy: number, xx: number) => (yy * cell.width + xx) * 4;
          const first = at(y * scale, x * scale);
          for (let dy = 0; dy < scale && uniform; dy++) for (let dx = 0; dx < scale; dx++) {
            const o = at(y * scale + dy, x * scale + dx);
            if (cell.rgba[o] !== cell.rgba[first] || cell.rgba[o + 1] !== cell.rgba[first + 1] || cell.rgba[o + 2] !== cell.rgba[first + 2] || cell.rgba[o + 3] !== cell.rgba[first + 3]) { uniform = false; break; }
          }
          small.push(cell.rgba[first], cell.rgba[first + 1], cell.rgba[first + 2], cell.rgba[first + 3]);
        }
        const hash = uniform ? await pixelsV1Hash(entry.width, entry.height, small) : 'not-uniform';
        verdicts[key] = { expected: entry.pixel_hash, drawn: hash, identical: hash === entry.pixel_hash, scale, ...(uniform ? {} : { note: 'a scaled block is not one colour (smoothing is on?)' }) };
      }
      evidence.pixel_verdicts = verdicts;
      evidence.pixel_verified = Object.values(verdicts).every((v) => v.identical);
    }
    pages.push(evidence);
  }

  mkdirSync(path.dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify({ browser: browser.browserType().name(), browser_version: browser.version(), device_pixel_ratio: devicePixelRatio, pages }, null, 2) + '\n');

  expect(devicePixelRatio, 'the config pins deviceScaleFactor 1').toBe(1);
  for (const p of pages) {
    expect(p.image_urls.length, `${p.page}: images were requested`).toBeGreaterThan(0);
    expect(p.all_images_hashed, `${p.page}: every image URL is /assets/<64 hex>-<hash>.png`).toBe(true);
    expect(p.unknown_fixture_files, `${p.page}: every hashed image is a committed fixture`).toEqual([]);
    expect(p.dev_server_requests, `${p.page}: nothing comes from the dev server`).toEqual([]);
    expect(p.failed_requests, `${p.page}: no failed request`).toEqual([]);
    expect(p.data_url_images, `${p.page}: no inlined data: image`).toBe(0);
  }
  const rehearsal = pages.find((p) => p.page === 'rehearsal')!;
  for (const [key, verdict] of Object.entries(rehearsal.pixel_verdicts!)) expect(verdict.identical, `${key}: drawn ${verdict.drawn} expected ${verdict.expected}`).toBe(true);
});
