import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { KIND_COLORS, STATE_COLORS, TILE_COLORS, TILE_NAMES } from '@/constants/colors'
import { CELL_SIZE } from '../cell'
import { SnapshotLoader, type Decode } from '../loader'
import { parseManifest } from '../manifest'
import { pilotManifestText, pilotUrlFor } from '../pilotSource'
import {
  BUILDING_COLORS_COPY, BUILDING_LABELS_COPY, FOREST_CODE, KIND_COLORS_COPY, MARKERS, PILOT_COLUMNS, PILOT_ROWS, PILOT_KEY, STATE_COLOR_COPY,
  TILE_COLORS_COPY, TILE_NAMES_COPY, drawPilotScene, drawTerrainCell, hoverText, terrainAt,
} from '../pilotScene'
import { bitmap, controlledDecode } from './helpers'
import { Recorder } from './pilotHelpers'

const FILL = '#1b3a1b'

const snapshot = parseManifest(pilotManifestText)
const okDecode: Decode = async () => bitmap()

async function viewWith(decode: Decode, urlFor: (f: string) => string | undefined = pilotUrlFor) {
  const view = new SnapshotLoader(decode, urlFor).mount(snapshot)
  await view.ready
  return view
}

describe('the pilot export', () => {
  it('holds exactly terrain.forest (16 x 16, family terrain)', () => {
    expect([...snapshot.entries.keys()]).toEqual([PILOT_KEY])
    const entry = snapshot.entries.get(PILOT_KEY)!
    expect([entry.family, entry.width, entry.height]).toEqual(['terrain', 16, 16])
  })
})

describe('copies of the Live Map constants equal the originals', () => {
  it('tile fills and names used by the pilot scene', () => {
    for (const [code, color] of Object.entries(TILE_COLORS_COPY)) expect(TILE_COLORS[Number(code)], `fill ${code}`).toBe(color)
    for (const [code, name] of Object.entries(TILE_NAMES_COPY)) expect(TILE_NAMES[Number(code)], `name ${code}`).toBe(name)
    expect(TILE_COLORS[FOREST_CODE]).toBe(FILL)
    expect(TILE_NAMES[FOREST_CODE]).toBe('Forest')
  })

  it('entity kind colours and the state colour of the markers', () => {
    for (const [kind, color] of Object.entries(KIND_COLORS_COPY)) expect(KIND_COLORS[kind], kind).toBe(color)
    expect(STATE_COLORS.WANDER).toBe(STATE_COLOR_COPY)
  })

  it('building colours and letters, read from the Live Map source without importing it', () => {
    const source = readFileSync(path.join(process.cwd(), 'src', 'hooks', 'useCanvas.ts'), 'utf8')
    for (const [type, color] of Object.entries(BUILDING_COLORS_COPY)) expect(source, type).toContain(`${type}: '${color}'`)
    for (const [type, letter] of Object.entries(BUILDING_LABELS_COPY)) expect(source, type).toContain(`${type}: '${letter}'`)
  })
})

describe('the predeclared pilot scene', () => {
  it('is 12 x 8, 49 forest cells of 96, with the documented codes and the same layout every time', () => {
    const codes: number[] = []
    for (let y = 0; y < PILOT_ROWS; y++) for (let x = 0; x < PILOT_COLUMNS; x++) codes.push(terrainAt(x, y))
    expect(codes).toHaveLength(96)
    expect(codes.filter((c) => c === FOREST_CODE)).toHaveLength(49)
    expect(new Set(codes)).toEqual(new Set([6, 7, 8, 9, 15, 17]))
    expect(terrainAt(0, 0)).toBe(6)
    expect(terrainAt(2, 0)).toBe(8)
  })

  it('has six markers on forest cells and two control markers on other terrain, as documented', () => {
    expect(MARKERS).toHaveLength(8)
    const onForest = MARKERS.filter((m) => terrainAt(m.x, m.y) === FOREST_CODE)
    expect(onForest.map((m) => `${m.kind}@${m.x},${m.y}`)).toEqual(['hero@1,0', 'goblin@4,0', 'wolf@9,0', 'store@6,1', 'inn@0,2', 'goblin_warrior@1,3'])
    expect(MARKERS.filter((m) => terrainAt(m.x, m.y) !== FOREST_CODE).map((m) => [terrainAt(m.x, m.y), m.kind])).toEqual([[8, 'goblin'], [9, 'hero']])
  })

  it('draws forest cells 1:1 with the tile and every other cell with its flat fill, then the markers, smoothing off', async () => {
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await viewWith(okDecode), 'image')
    expect(ctx.imageSmoothingEnabled).toBe(false)
    const images = ctx.of('drawImage') as unknown as [string, unknown, number, number, ...unknown[]][]
    expect(images).toHaveLength(49)
    for (const [, , x, y, ...rest] of images) {
      expect(rest).toEqual([]) // no destination size: 1:1
      expect(terrainAt(x / CELL_SIZE, y / CELL_SIZE)).toBe(FOREST_CODE)
    }
    expect(ctx.of('fillText').map((c) => c[1])).toEqual(['S', 'I'])
    expect(ctx.of('arc').length).toBeGreaterThan(0)
  })

  it('the flat control draws no image at all and uses the fill for forest cells', async () => {
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await viewWith(okDecode), 'flat')
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.fills.filter((c) => c === FILL).length).toBeGreaterThanOrEqual(49)
  })
})

describe('AM-U21: every failure shows exactly the flat fill, never an image, a glyph or another colour', () => {
  const shownFill = (ctx: Recorder) => {
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.of('fillText')).toHaveLength(0)
    expect(ctx.fills).toEqual([FILL])
    expect(ctx.of('fillRect')).toEqual([['fillRect', 0, 0, CELL_SIZE, CELL_SIZE]])
  }

  it('image missing from the build', async () => {
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), await viewWith(okDecode, () => undefined), FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('image corrupt (decode fails)', async () => {
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), await viewWith(async () => { throw new Error('corrupt') }), FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('image of the wrong size', async () => {
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), await viewWith(async () => bitmap(32, 32)), FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('image still loading', () => {
    const { decode } = controlledDecode()
    const view = new SnapshotLoader(decode, pilotUrlFor).mount(snapshot)
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), view, FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('late: the image arrives after the view was superseded', async () => {
    const releases: (() => void)[] = []
    const decode: Decode = () => new Promise((resolve) => releases.push(() => resolve(bitmap())))
    const loader = new SnapshotLoader(decode, pilotUrlFor)
    const first = loader.mount(snapshot)
    loader.mount(snapshot) // supersedes the first
    releases.forEach((release) => release())
    await first.ready
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), first, FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('the key is not in the manifest', async () => {
    const raw = JSON.parse(pilotManifestText) as { entries: { visual_key: string }[] }
    raw.entries = []
    const view = new SnapshotLoader(okDecode, pilotUrlFor).mount(parseManifest(JSON.stringify(raw)))
    await view.ready
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), view, FOREST_CODE, 0, 0)
    shownFill(ctx)
  })

  it('the manifest is invalid (no view at all)', () => {
    const ctx = new Recorder()
    drawTerrainCell(ctx.asCtx(), null, FOREST_CODE, 0, 0)
    shownFill(ctx)
    const scene = new Recorder()
    drawPilotScene(scene.asCtx(), null, 'image')
    expect(scene.of('drawImage')).toHaveLength(0)
    expect(scene.fills.filter((c) => c === FILL).length).toBeGreaterThanOrEqual(49)
  })

  it('a cell whose terrain is not Forest never gets the image, even when the view has it', async () => {
    const view = await viewWith(okDecode)
    for (const code of [7, 8, 9, 15, 17]) {
      const ctx = new Recorder()
      drawTerrainCell(ctx.asCtx(), view, code, 0, 0)
      expect(ctx.of('drawImage'), `code ${code}`).toHaveLength(0)
      expect(ctx.fills).toEqual([TILE_COLORS[code]])
    }
  })

  it('the hover text is the terrain name whatever the cell shows', () => {
    for (const code of [6, 7, 8, 9, 15, 17]) expect(hoverText(code)).toBe(TILE_NAMES[code])
  })
})
