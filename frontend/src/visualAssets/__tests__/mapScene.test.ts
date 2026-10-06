import { describe, expect, it } from 'vitest'
import { CELL_SIZE } from '../cell'
import { SnapshotLoader, type Bitmap, type Decode } from '../loader'
import { parseManifest } from '../manifest'
import { FOREST, layoutFacts, mapMarkers, drawMapScene, type MapCtx } from '../mapScene'
import { terrainsetManifestText, terrainsetUrlFor } from '../terrainsetSource'
import { MAP_COLUMNS, MAP_ROWS, TERRAIN_CODES, TERRAIN_DRAFT_KEYS, TILE_COLORS_COPY, mapCodes, terrainAt } from '../terrainDrafts'
import { TILE_PIXELS, type Rgba } from '../terrainBorders'
import { Recorder } from './pilotHelpers'

type Tagged = Bitmap & { url: string }
const decode: Decode = async (url) => ({ width: TILE_PIXELS, height: TILE_PIXELS, url } as Tagged)

class MapRecorder extends Recorder {
  puts: [number, number][] = []
  order: string[] = []
  putImageData(_: unknown, x: number, y: number) { this.puts.push([x, y]); this.order.push('put') }
  drawImage(...a: unknown[]) { super.drawImage(...a); this.order.push('image') }
  arc(...a: number[]) { super.arc(...a); this.order.push('marker') }
  asMap(): MapCtx { return this as unknown as MapCtx }
}

type Raw = { entries: { visual_key: string; detail?: string; file: string }[]; details?: { visual_key: string; values: string[]; default: string }[] }
async function viewOf(change: (raw: Raw) => void = () => undefined) {
  const raw = JSON.parse(terrainsetManifestText) as Raw
  change(raw)
  const view = new SnapshotLoader(decode, terrainsetUrlFor).mount(parseManifest(JSON.stringify(raw)))
  await view.ready
  return view
}

// Tiles: a flat colour per file; masks (border.* files) are opaque everywhere so the cap is what limits them.
const makeImage = (pixels: Rgba) => ({ data: pixels }) as unknown as ImageData
const rasterize = (bitmap: Bitmap): Rgba => {
  const url = (bitmap as Tagged).url
  const out = new Uint8ClampedArray(TILE_PIXELS * TILE_PIXELS * 4)
  const seed = [...url].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 251, 7)
  for (let i = 0; i < TILE_PIXELS * TILE_PIXELS; i++) out.set([seed, (seed * 3) % 251, (seed * 7) % 251, 255], i * 4)
  return out
}

const fillOf = (code: number) => TILE_COLORS_COPY[code]
const cellsOf = (code: number) => mapCodes().flat().filter((c) => c === code).length

describe('the predeclared whole-map layout (AM5-W03-SET)', () => {
  it('uses every one of the 23 Live Map codes and gives each a patch of at least 3 x 3 cells', () => {
    const facts = layoutFacts()
    expect(facts.codes).toEqual([...TERRAIN_CODES])
    expect(TERRAIN_CODES).toHaveLength(23)
    for (const code of TERRAIN_CODES) expect(facts.patchSide.get(code), `code ${code}`).toBeGreaterThanOrEqual(3)
  })

  it('shows plain, bush and tree on forest cells, through the detail pick', async () => {
    const { outcomes } = drawMapScene(new MapRecorder().asMap(), await viewOf(), 'image')
    const forest = outcomes.filter((o) => o.code === FOREST)
    expect(forest.length).toBeGreaterThan(30)
    expect(new Set(forest.map((o) => o.detail))).toEqual(new Set(['plain', 'bush', 'tree']))
  })

  it('puts the predeclared markers: the first six forest cells (row-major), a goblin on the first swamp cell and a hero on the first mountain cell', () => {
    const markers = mapMarkers()
    expect(markers).toHaveLength(8)
    const forestCells: [number, number][] = []
    for (let y = 0; y < MAP_ROWS; y++) for (let x = 0; x < MAP_COLUMNS; x++) if (terrainAt(x, y) === FOREST && forestCells.length < 6) forestCells.push([x, y])
    expect(markers.slice(0, 6).map((m) => [m.kind, m.x, m.y])).toEqual(['hero', 'goblin', 'wolf', 'store', 'inn', 'goblin_warrior'].map((kind, i) => [kind, ...forestCells[i]]))
    expect(markers.slice(6).map((m) => [m.kind, terrainAt(m.x, m.y)])).toEqual([['goblin', 8], ['hero', 9]])
  })
})

describe('the image scene from the rc-0005 export', () => {
  it('draws every cell from its terrain tile when the release has every key', async () => {
    const ctx = new MapRecorder()
    const { outcomes } = drawMapScene(ctx.asMap(), await viewOf(), 'image')
    expect(outcomes.every((o) => o.kind === 'tile')).toBe(true)
    expect(ctx.of('drawImage')).toHaveLength(MAP_COLUMNS * MAP_ROWS)
  })

  it('shows the flat fill of EACH of the 22 non-forest terrain keys when that key is missing from the release, and the tile everywhere else', async () => {
    for (const code of TERRAIN_CODES.filter((c) => c !== FOREST)) {
      const key = TERRAIN_DRAFT_KEYS[code]
      const ctx = new MapRecorder()
      const { outcomes } = drawMapScene(ctx.asMap(), await viewOf((raw) => { raw.entries = raw.entries.filter((e) => e.visual_key !== key) }), 'image')
      const missing = outcomes.filter((o) => o.code === code)
      expect(missing.length, key).toBe(cellsOf(code))
      expect(missing.every((o) => o.kind === 'fill'), key).toBe(true)
      expect(outcomes.filter((o) => o.code !== code).every((o) => o.kind === 'tile'), key).toBe(true)
      expect(ctx.fills.filter((f) => f === fillOf(code)).length, key).toBe(cellsOf(code))
    }
  })

  it('a missing forest variant falls back to plain, and a missing plain to the role fallback (the flat fill)', async () => {
    const noBush = drawMapScene(new MapRecorder().asMap(), await viewOf((raw) => { raw.entries = raw.entries.filter((e) => !(e.visual_key === 'terrain.forest' && e.detail === 'bush')) }), 'image')
    const forest = noBush.outcomes.filter((o) => o.code === FOREST)
    expect(new Set(forest.map((o) => o.detail))).toEqual(new Set(['plain', 'tree'])) // bush cells show the default slot, plain
    const noPlain = drawMapScene(new MapRecorder().asMap(), await viewOf((raw) => { raw.entries = raw.entries.filter((e) => !(e.visual_key === 'terrain.forest' && e.detail === 'plain')) }), 'image')
    const cells = noPlain.outcomes.filter((o) => o.code === FOREST)
    expect(cells.some((o) => o.kind === 'fill')).toBe(true) // a cell whose picked slot (or the default) is gone shows the fill
    expect(cells.filter((o) => o.kind === 'tile').every((o) => o.detail !== 'plain')).toBe(true)
  })

  it('draws no fringe and no putImageData when borders are off, and the same tiles as with borders on', async () => {
    const off = new MapRecorder()
    drawMapScene(off.asMap(), await viewOf(), 'image', { borders: false, rasterize, makeImage })
    expect(off.puts).toHaveLength(0)
    const on = new MapRecorder()
    const { fringed } = drawMapScene(on.asMap(), await viewOf(), 'image', { borders: true, rasterize, makeImage })
    expect(fringed.length).toBeGreaterThan(100)
    expect(on.puts).toEqual(fringed.map((c) => [c.x * CELL_SIZE, c.y * CELL_SIZE]))
    expect(on.of('drawImage')).toEqual(off.of('drawImage')) // the base tiles are identical; fringes are added on top
  })

  it('a missing border mask gives today\'s hard edge: no fringe, never a blank or broken cell', async () => {
    const noMasks = new MapRecorder()
    const view = await viewOf((raw) => { raw.entries = raw.entries.filter((e) => !e.visual_key.startsWith('border.')); raw.details = raw.details?.filter((d) => !d.visual_key.startsWith('border.')) })
    const { outcomes, fringed } = drawMapScene(noMasks.asMap(), view, 'image', { borders: true, rasterize, makeImage })
    expect(fringed).toEqual([])
    expect(noMasks.puts).toHaveLength(0)
    expect(outcomes.every((o) => o.kind === 'tile')).toBe(true)
    expect(noMasks.of('drawImage')).toHaveLength(MAP_COLUMNS * MAP_ROWS) // every cell still drawn
    // only the edge mask missing: corners can still fringe, edges leave a hard side
    const edgeless = await viewOf((raw) => { raw.entries = raw.entries.filter((e) => e.visual_key !== 'border.edge'); raw.details = raw.details?.filter((d) => d.visual_key !== 'border.edge') })
    const partial = drawMapScene(new MapRecorder().asMap(), edgeless, 'image', { borders: true, rasterize, makeImage })
    expect(partial.fringed.length).toBeGreaterThan(0)
  })

  it('masks whose images are missing from the build or undecodable are no masks: the page reports and draws no fringe, and every cell is still drawn', async () => {
    const maskFiles = new Set((JSON.parse(terrainsetManifestText) as Raw).entries.filter((e) => e.visual_key.startsWith('border.')).map((e) => e.file))
    for (const mode of ['missing', 'corrupt'] as const) {
      const ctx = new MapRecorder()
      const urlFor = (file: string) => (mode === 'missing' && maskFiles.has(file) ? undefined : terrainsetUrlFor(file))
      const failing: Decode = async (url) => {
        if (mode === 'corrupt' && [...maskFiles].some((f) => url === terrainsetUrlFor(f))) throw new Error('corrupt')
        return { width: TILE_PIXELS, height: TILE_PIXELS, url } as Tagged
      }
      const view = new SnapshotLoader(failing, urlFor).mount(parseManifest(terrainsetManifestText))
      await view.ready
      const { outcomes, fringed } = drawMapScene(ctx.asMap(), view, 'image', { borders: true, rasterize, makeImage })
      expect(fringed, mode).toEqual([])
      expect(ctx.puts, mode).toHaveLength(0)
      expect(outcomes.every((o) => o.kind === 'tile'), mode).toBe(true)
    }
  })

  it('draws the markers after the fringes', async () => {
    const ctx = new MapRecorder()
    drawMapScene(ctx.asMap(), await viewOf(), 'image', { borders: true, rasterize, makeImage })
    const lastPut = ctx.order.lastIndexOf('put')
    const firstMarker = ctx.order.indexOf('marker')
    expect(lastPut).toBeGreaterThan(-1)
    expect(firstMarker).toBeGreaterThan(lastPut)
  })
})

describe('the flat control', () => {
  it('draws every cell as its flat fill and no image, with the same markers', async () => {
    const ctx = new MapRecorder()
    const { outcomes, fringed } = drawMapScene(ctx.asMap(), await viewOf(), 'flat', { borders: true, rasterize, makeImage })
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.puts).toHaveLength(0)
    expect(fringed).toEqual([])
    expect(outcomes.every((o) => o.kind === 'fill')).toBe(true)
    for (const code of TERRAIN_CODES) expect(ctx.fills.filter((f) => f === fillOf(code)).length).toBeGreaterThanOrEqual(cellsOf(code))
    expect(ctx.of('arc').length).toBeGreaterThan(0)
  })
})
