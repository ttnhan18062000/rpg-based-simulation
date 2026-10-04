import { describe, expect, it } from 'vitest'
import { SnapshotLoader, type Decode } from '../loader'
import { parseManifest, slotKey, type RuntimeSnapshot } from '../manifest'
import { DETAIL_SEED, pickDetail } from '../pickDetail'
import { PILOT_COLUMNS, PILOT_KEY, PILOT_ROWS, FOREST_CODE, drawPilotScene, drawTerrainCell, terrainAt } from '../pilotScene'
import { pilotManifestText, pilotUrlFor } from '../pilotSource'
import { resolveVisual } from '../resolver'
import { Recorder } from './pilotHelpers'
import { bitmap } from './helpers'

const VALUES = ['plain', 'bush', 'tree']
const hex = (c: string) => c.repeat(64)
const FILE = { plain: `${hex('a')}.png`, bush: `${hex('b')}.png`, tree: `${hex('c')}.png` } as const
const slot = (detail: string) => ({
  family: 'terrain', file: FILE[detail as keyof typeof FILE], height: 16, pixel_hash: `pixels-v1:${FILE[detail as keyof typeof FILE].slice(0, 64)}`,
  visual_key: PILOT_KEY, width: 16, detail,
})

/** A runtime manifest for terrain.forest that declares [plain, bush, tree] and holds art only for `have` (the pilot's own manifest, widened). */
function snapshotWith(have: readonly string[]): RuntimeSnapshot {
  const raw = JSON.parse(pilotManifestText)
  raw.entries = [...have].sort().map(slot)
  raw.details = [{ visual_key: PILOT_KEY, values: VALUES, default: 'plain' }]
  return parseManifest(JSON.stringify(raw))
}

const urls = (missing: readonly string[] = []) => (file: string) => (missing.includes(file) ? undefined : `/build/${file}`)
const forestCells = () => {
  const cells: { x: number; y: number }[] = []
  for (let y = 0; y < PILOT_ROWS; y++) for (let x = 0; x < PILOT_COLUMNS; x++) if (terrainAt(x, y) === FOREST_CODE) cells.push({ x, y })
  return cells
}
const picks = (cells: { x: number; y: number }[]) => cells.map((c) => pickDetail(PILOT_KEY, c.x, c.y, DETAIL_SEED, VALUES))

describe('resolveVisual for a key with a detail axis', () => {
  const all = snapshotWith(VALUES)
  const cell = (want: string) => forestCells().find((c) => pickDetail(PILOT_KEY, c.x, c.y, DETAIL_SEED, VALUES) === want)!

  it('keys the manifest by slot, so the plain key alone is not an image', () => {
    expect([...all.entries.keys()]).toEqual([slotKey(PILOT_KEY, 'bush'), slotKey(PILOT_KEY, 'plain'), slotKey(PILOT_KEY, 'tree')])
    expect(all.entries.has(PILOT_KEY)).toBe(false)
  })

  it('step 1: the picked value\'s image, recording what was picked and shown', () => {
    for (const want of VALUES) {
      const c = cell(want)
      expect(resolveVisual(all, PILOT_KEY, { urlFor: urls() }, c)).toMatchObject({ kind: 'image', file: FILE[want as keyof typeof FILE], picked: want, detail: want })
      expect(resolveVisual(all, PILOT_KEY, { urlFor: urls() }, c)).not.toHaveProperty('detailFallback')
    }
  })

  it('step 2: the picked value has no art (no entry, a missing file, a failed decode, a late result) so the default\'s image is shown, with the reason', () => {
    const bush = cell('bush')
    const noBush = snapshotWith(['plain', 'tree'])
    expect(resolveVisual(noBush, PILOT_KEY, { urlFor: urls() }, bush)).toMatchObject({
      kind: 'image', file: FILE.plain, picked: 'bush', detail: 'plain', detailFallback: 'missing_image',
    })
    expect(resolveVisual(all, PILOT_KEY, { urlFor: urls([FILE.bush]) }, bush)).toMatchObject({ kind: 'image', file: FILE.plain, detail: 'plain', detailFallback: 'missing_image' })
    for (const [status, reason] of [['decode_failed', 'decode_failed'], ['late', 'late_result_dropped']] as const) {
      const statusOf = (file: string) => (file === FILE.bush ? status : 'ok')
      expect(resolveVisual(all, PILOT_KEY, { urlFor: urls(), statusOf }, bush)).toMatchObject({ kind: 'image', file: FILE.plain, picked: 'bush', detail: 'plain', detailFallback: reason })
    }
  })

  it('step 3: neither the picked nor the default image is available, so the role fallback (a typed fallback, the caller\'s flat fill), with the default\'s reason', () => {
    const bush = cell('bush')
    expect(resolveVisual(snapshotWith(['tree']), PILOT_KEY, { urlFor: urls() }, bush)).toEqual({
      kind: 'fallback', visualKey: PILOT_KEY, family: 'terrain', reason: 'missing_image', picked: 'bush',
    })
    expect(resolveVisual(all, PILOT_KEY, { urlFor: urls([FILE.bush, FILE.plain]) }, bush)).toMatchObject({ kind: 'fallback', reason: 'missing_image', picked: 'bush', family: 'terrain' })
    expect(resolveVisual(all, PILOT_KEY, { urlFor: urls(), statusOf: (f) => (f === FILE.tree ? 'ok' : 'decode_failed') }, bush)).toMatchObject({ kind: 'fallback', reason: 'decode_failed', picked: 'bush' })
  })

  it('a picked default that is unavailable goes straight to the role fallback', () => {
    expect(resolveVisual(all, PILOT_KEY, { urlFor: urls([FILE.plain]) }, cell('plain'))).toEqual({
      kind: 'fallback', visualKey: PILOT_KEY, family: 'terrain', reason: 'missing_image', picked: 'plain',
    })
  })

  it('with no cell the default value is used; a key without an axis ignores the cell', () => {
    expect(resolveVisual(all, PILOT_KEY, { urlFor: urls() })).toMatchObject({ kind: 'image', file: FILE.plain, picked: 'plain', detail: 'plain' })
    const old = parseManifest(pilotManifestText)
    const result = resolveVisual(old, PILOT_KEY, { urlFor: pilotUrlFor }, { x: 3, y: 4 })
    expect(result).toMatchObject({ kind: 'image', visualKey: PILOT_KEY })
    expect(result).not.toHaveProperty('picked')
    expect(resolveVisual(old, 'terrain.nothing', { urlFor: pilotUrlFor }, { x: 1, y: 1 })).toMatchObject({ kind: 'fallback', reason: 'unknown_key' })
  })
})

describe('the pilot scene with a detail axis', () => {
  const decode: Decode = async (url) => Object.assign(bitmap(), { url })
  async function scene(have: readonly string[]) {
    const view = new SnapshotLoader(decode, urls()).mount(snapshotWith(have))
    await view.ready
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), view, 'image')
    return ctx
  }
  const drawn = (ctx: Recorder) => ctx.of('drawImage').map((c) => (c[1] as { url: string }).url)

  it('with only `plain` adopted every forest cell still shows plain, through the default step', async () => {
    const urlsDrawn = drawn(await scene(['plain']))
    expect(urlsDrawn).toHaveLength(49)
    expect(new Set(urlsDrawn)).toEqual(new Set([`/build/${FILE.plain}`]))
    // and the picks really did differ: the plain look here is the fallback, not luck
    expect(new Set(picks(forestCells()))).toEqual(new Set(VALUES))
  })

  it('draws the same pixels as the pilot scene without an axis: same calls, same positions', async () => {
    const view = new SnapshotLoader(decode, pilotUrlFor).mount(parseManifest(pilotManifestText))
    await view.ready
    const old = new Recorder()
    drawPilotScene(old.asCtx(), view, 'image')
    const widened = await scene(['plain'])
    expect(widened.of('drawImage').map((c) => c.slice(2))).toEqual(old.of('drawImage').map((c) => c.slice(2)))
    expect(widened.of('fillRect')).toEqual(old.of('fillRect'))
  })

  it('with all three adopted each forest cell shows its own pick, and the picks are repeatable', async () => {
    const first = drawn(await scene(VALUES))
    expect(first).toEqual(picks(forestCells()).map((v) => `/build/${FILE[v as keyof typeof FILE]}`))
    expect(drawn(await scene(VALUES))).toEqual(first)
    expect(new Set(first).size).toBe(3)
  })

  it('a cell drawn without a cell position shows the default (the caller did not say where it is)', async () => {
    const view = new SnapshotLoader(decode, urls()).mount(snapshotWith(VALUES))
    await view.ready
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), view, FOREST_CODE, 0, 0)
    expect(drawn(ctx)).toEqual([`/build/${FILE.plain}`])
  })
})
