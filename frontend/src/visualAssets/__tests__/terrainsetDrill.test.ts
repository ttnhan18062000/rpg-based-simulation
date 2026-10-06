// Rollback drill for the terrain-set release (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, AM5-W09 / AM-C06), under Profile A (ADR D8): a release is a whole frontend build.
// "Previous release" = the rc-0004 pilot export (forest only); "new" = the rc-0005 terrain-set export (34 slots). Whatever the combination, a cell shows its role or its fallback,
// never a mixed snapshot. Pairs run: new client + new release, new client + old release, old client (pilot scene) + new release, new client + recalled release. Not run: none left in the matrix
// (the old client is the pilot rehearsal scene, the only older client that exists).
import { describe, expect, it } from 'vitest'
import { SnapshotLoader, type Bitmap, type Decode } from '../loader'
import { parseManifest } from '../manifest'
import { drawMapScene } from '../mapScene'
import { pilotManifestText, pilotUrlFor } from '../pilotSource'
import { PILOT_COLUMNS, PILOT_ROWS, PILOT_KEY, drawPilotScene, terrainAt as pilotTerrainAt } from '../pilotScene'
import { terrainsetManifestText, terrainsetUrlFor } from '../terrainsetSource'
import { MAP_COLUMNS, MAP_ROWS, TILE_COLORS_COPY, mapCodes } from '../terrainDrafts'
import { TILE_PIXELS, type Rgba } from '../terrainBorders'
import { Recorder } from './pilotHelpers'

const decode: Decode = async () => ({ width: TILE_PIXELS, height: TILE_PIXELS }) as Bitmap
const oldRelease = { name: 'previous release (pilot/rc-0004: forest only)', manifestText: pilotManifestText, urlFor: pilotUrlFor }
const newRelease = { name: 'new release (pilot/rc-0005: 34 slots)', manifestText: terrainsetManifestText, urlFor: terrainsetUrlFor }
const makeImage = (pixels: Rgba) => ({ data: pixels }) as unknown as ImageData
const rasterize = (): Rgba => new Uint8ClampedArray(TILE_PIXELS * TILE_PIXELS * 4).fill(200)

async function view(release: { manifestText: string; urlFor: (f: string) => string | undefined }) {
  const v = new SnapshotLoader(decode, release.urlFor).mount(parseManifest(release.manifestText))
  await v.ready
  return v
}

const FOREST_CELLS_MAP = mapCodes().flat().filter((c) => c === 6).length
const FOREST_CELLS_PILOT = Array.from({ length: PILOT_ROWS * PILOT_COLUMNS }, (_, i) => pilotTerrainAt(i % PILOT_COLUMNS, Math.floor(i / PILOT_COLUMNS))).filter((c) => c === 6).length

describe('terrain-set rollback drill', () => {
  it('the two releases are different generations of the same registry, the new one a superset of the old', () => {
    const [old, now] = [parseManifest(oldRelease.manifestText), parseManifest(newRelease.manifestText)]
    expect(old.generation).not.toBe(now.generation)
    expect(old.entries.size).toBe(3)
    expect(now.entries.size).toBe(34)
    for (const key of old.entries.keys()) expect(now.entries.has(key)).toBe(true)
  })

  it('new client + new release: every cell shows its tile, with fringes', async () => {
    const ctx = new Recorder() as unknown as Parameters<typeof drawMapScene>[0] & Recorder
    ;(ctx as unknown as { putImageData: () => void }).putImageData = () => undefined
    const { outcomes, fringed } = drawMapScene(ctx, await view(newRelease), 'image', { borders: true, rasterize, makeImage })
    expect(outcomes.every((o) => o.kind === 'tile')).toBe(true)
    expect(fringed.length).toBeGreaterThan(100)
  })

  it('new client + old release: the 22 other terrain keys are unknown so their cells show the flat fills, forest keeps its tile, and no fringe is drawn (no masks)', async () => {
    const ctx = new Recorder()
    ;(ctx as unknown as { putImageData: () => void }).putImageData = () => undefined
    const { outcomes, fringed } = drawMapScene(ctx as never, await view(oldRelease), 'image', { borders: true, rasterize, makeImage })
    expect(fringed).toEqual([])
    expect(outcomes.filter((o) => o.code === 6).every((o) => o.kind === 'tile')).toBe(true)
    expect(outcomes.filter((o) => o.code !== 6).every((o) => o.kind === 'fill')).toBe(true)
    expect(ctx.of('drawImage')).toHaveLength(FOREST_CELLS_MAP)
    for (const code of new Set(outcomes.map((o) => o.code))) if (code !== 6) expect(ctx.fills).toContain(TILE_COLORS_COPY[code])
  })

  it('old client (the pilot scene) + new release: it reads only the forest key, ignores the 31 extra slots and draws the same forest cells', async () => {
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await view(newRelease), 'image')
    expect(ctx.of('drawImage')).toHaveLength(FOREST_CELLS_PILOT)
    expect(PILOT_KEY).toBe('terrain.forest')
  })

  it('new client + a recalled release (no entries): every cell shows its flat fill, never a blank cell', async () => {
    const raw = JSON.parse(newRelease.manifestText) as { entries: unknown[]; details?: unknown }
    raw.entries = []
    delete raw.details
    const ctx = new Recorder()
    const v = new SnapshotLoader(decode, newRelease.urlFor).mount(parseManifest(JSON.stringify(raw)))
    await v.ready
    const { outcomes } = drawMapScene(ctx as never, v, 'image', { borders: true, rasterize, makeImage })
    expect(outcomes).toHaveLength(MAP_COLUMNS * MAP_ROWS)
    expect(outcomes.every((o) => o.kind === 'fill')).toBe(true)
    expect(ctx.of('drawImage')).toHaveLength(0)
  })

  it('no mixed snapshot: a view only ever carries the generation of the manifest it was mounted from', async () => {
    const [a, b] = [await view(oldRelease), await view(newRelease)]
    expect(a.snapshot.generation).toBe(parseManifest(oldRelease.manifestText).generation)
    expect(b.snapshot.generation).toBe(parseManifest(newRelease.manifestText).generation)
    expect(a.snapshot.generation).not.toBe(b.snapshot.generation)
  })
})
