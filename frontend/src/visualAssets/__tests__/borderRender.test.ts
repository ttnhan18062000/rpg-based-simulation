import { describe, expect, it } from 'vitest'
import { composeBorderedCells, drawComposedCells, type Rasterize } from '../borderRender'
import { CELL_SIZE } from '../cell'
import { asRuntimeSnapshot, parseDraftPreview } from '../draftManifest'
import { draftManifestText } from '../draftSource'
import { SnapshotLoader, type Bitmap, type Decode } from '../loader'
import { MASK_KEYS, TILE_PIXELS, BORDER_DEPTH } from '../terrainBorders'
import { TERRAIN_DRAFT_KEYS, terrainAt, type FileInfo } from '../terrainDrafts'

const MASK_FILE = 'a'.repeat(64) + '.png'
const raw = JSON.parse(draftManifestText) as { entries: Record<string, unknown>[]; details?: Record<string, unknown>[] }

function manifestWith(kinds: (keyof typeof MASK_KEYS)[]): string {
  const copy = JSON.parse(JSON.stringify(raw)) as typeof raw
  const keys = kinds.map((k) => MASK_KEYS[k])
  keys.forEach((key, i) => {
    copy.entries.push({ visual_key: key, family: 'border', detail: 'v1', source_asset_id: `${key.replace('.', '_')}_v1`, draft_id: `in-${String(i + 1).repeat(16)}`, pixel_hash: `pixels-v1:${'a'.repeat(64)}`, file: MASK_FILE, width: 128, height: 128, scale: 8 })
  })
  copy.details = [...(copy.details ?? []), ...keys.map((key) => ({ visual_key: key, values: ['v1'], default: 'v1' }))].sort((a, b) => String((a as { visual_key: string }).visual_key).localeCompare(String((b as { visual_key: string }).visual_key)))
  copy.entries.sort((a, b) => String(a.visual_key).localeCompare(String(b.visual_key)) || String(a.detail ?? '').localeCompare(String(b.detail ?? '')))
  return JSON.stringify(copy)
}

const decode: Decode = async (url) => ({ width: 128, height: 128, url } as Bitmap & { url: string })
// Tiles: one flat colour per file (derived from the file name); the mask file: opaque everywhere (the cap must still hold).
const rasterize: Rasterize = (bitmap) => {
  const url = (bitmap as Bitmap & { url: string }).url
  const out = new Uint8ClampedArray(TILE_PIXELS * TILE_PIXELS * 4)
  const mask = url.includes('a'.repeat(64))
  const seed = [...url].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 251, 7)
  for (let i = 0; i < TILE_PIXELS * TILE_PIXELS; i++) out.set(mask ? [0, 0, 0, 255] : [seed, (seed * 3) % 251, (seed * 7) % 251, 255], i * 4)
  return out
}
const urlFor = (file: string) => `u/${file}`

async function viewOf(kinds: (keyof typeof MASK_KEYS)[]) {
  const text = manifestWith(kinds)
  const snapshot = parseDraftPreview(text)
  const view = new SnapshotLoader(decode, urlFor).mount(asRuntimeSnapshot(snapshot))
  await view.ready
  const files = new Map<string, FileInfo>(snapshot.entries.map((e) => [e.file, { scale: e.scale, adopted: e.adopted }]))
  return { view, files }
}

describe('composing the bordered sample map', () => {
  it('leaves the map as it was when the set holds no border masks (today\'s hard edge)', async () => {
    const { view, files } = await viewOf([])
    expect(composeBorderedCells(view, files, rasterize)).toEqual([])
  })

  it('fringes only cells that have a draft and a neighbour with a draft, keeps the centre and caps the depth', async () => {
    const { view, files } = await viewOf(['edge', 'outer_corner', 'inner_corner'])
    const cells = composeBorderedCells(view, files, rasterize)
    expect(cells.length).toBeGreaterThan(0)
    const withDraft = new Set([6, 7, 8, 9, 15]) // forest, desert, swamp, mountain, grassland in the fixture
    for (const cell of cells) {
      expect(withDraft.has(terrainAt(cell.x, cell.y))).toBe(true)
      const centre = (8 * TILE_PIXELS + 8) * 4
      const resolved = view.resolve(TERRAIN_DRAFT_KEYS[terrainAt(cell.x, cell.y)], { x: cell.x, y: cell.y })
      expect(resolved.kind).toBe('image')
      const own = rasterize({ width: 128, height: 128, url: urlFor((resolved as { file: string }).file) } as Bitmap & { url: string }, 8)!
      expect(Array.from(cell.pixels.subarray(centre, centre + 4))).toEqual(Array.from(own.subarray(centre, centre + 4))) // the cell centre is always its own terrain
      for (let y = 0; y < TILE_PIXELS; y++) for (let x = 0; x < TILE_PIXELS; x++) {
        const changed = cell.pixels[(y * TILE_PIXELS + x) * 4] !== own[(y * TILE_PIXELS + x) * 4]
        if (changed) expect(Math.min(x, y, TILE_PIXELS - 1 - x, TILE_PIXELS - 1 - y)).toBeLessThan(BORDER_DEPTH)
      }
    }
  })

  it('is deterministic', async () => {
    const { view, files } = await viewOf(['edge', 'outer_corner', 'inner_corner'])
    const a = composeBorderedCells(view, files, rasterize)
    expect(composeBorderedCells(view, files, rasterize)).toEqual(a)
  })

  it('a missing inner-corner mask still draws edges; a set with only an outer-corner mask draws only corners', async () => {
    const edgesOnly = composeBorderedCells((await viewOf(['edge'])).view, (await viewOf(['edge'])).files, rasterize)
    const all = composeBorderedCells((await viewOf(['edge', 'outer_corner', 'inner_corner'])).view, (await viewOf(['edge', 'outer_corner', 'inner_corner'])).files, rasterize)
    expect(edgesOnly.length).toBeGreaterThan(0)
    expect(all.length).toBeGreaterThanOrEqual(edgesOnly.length)
    const cornersOnly = await viewOf(['outer_corner'])
    for (const cell of composeBorderedCells(cornersOnly.view, cornersOnly.files, rasterize)) expect(cell.overlays).toBeGreaterThan(0)
  })

  it('puts each composed cell on the canvas at its map position', async () => {
    const { view, files } = await viewOf(['edge', 'outer_corner', 'inner_corner'])
    const cells = composeBorderedCells(view, files, rasterize)
    const calls: [number, number][] = []
    const ctx = { putImageData: (_: unknown, x: number, y: number) => calls.push([x, y]), fillRect: () => undefined, fillStyle: '' }
    drawComposedCells(ctx as never, view, files, cells, (pixels) => ({ data: pixels }) as unknown as ImageData)
    expect(calls).toEqual(cells.map((c) => [c.x * CELL_SIZE, c.y * CELL_SIZE]))
  })
})
