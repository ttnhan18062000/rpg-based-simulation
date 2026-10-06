import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { TILE_NAMES } from '@/constants/colors'
import {
  BORDER_DEPTH,
  CRISP_TERRAINS,
  MASK_KEYS,
  TERRAIN_PRIORITY,
  TILE_PIXELS,
  borderOverlays,
  composeCell,
  maskCapViolation,
  rankOf,
  rotate,
  type BorderOverlay,
  type MaskAvailability,
  type Rgba,
} from '../terrainBorders'
import { TERRAIN_CODES } from '../terrainDrafts'


const WATER = 2
const SHALLOW = 18
const DESERT = 7
const GRASS = 15
const FOREST = 6
const WALL = 1

const ALL_MASKS: MaskAvailability = { variants: () => ['v1', 'v2', 'v3'] }
const NO_MASKS: MaskAvailability = { variants: () => [] }
const only = (...kinds: (keyof typeof MASK_KEYS)[]): MaskAvailability => ({ variants: (key) => (kinds.some((k) => MASK_KEYS[k] === key) ? ['v1'] : []) })

/** A map from rows of codes; off the map is undefined. */
const mapOf = (rows: number[][]) => (x: number, y: number) => rows[y]?.[x]
const summary = (o: BorderOverlay[]) => o.map((p) => `${p.neighbour}:${p.kind}:${p.rotation}`)

describe('the priority table equals the documented one', () => {
  const doc = readFileSync(resolve(__dirname, '../../../../docs/assets/pilot_terrain_m5_criteria.md'), 'utf8')
  const section = doc.split('### AM5-B: the priority order')[1].split('### AM5-B: fringe rules')[0]

  it('lists the same codes in the same order as the AM5-B table', () => {
    const rows = [...section.matchAll(/^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([a-z_]+)\s*\|$/gm)].map((m) => ({ rank: Number(m[1]), code: Number(m[2]), name: m[3] }))
    expect(rows.map((r) => r.rank)).toEqual(rows.map((_, i) => i + 1))
    expect(rows.map((r) => r.code)).toEqual([...TERRAIN_PRIORITY])
    for (const r of rows) expect(TILE_NAMES[r.code].toLowerCase().replace(/ /g, '_')).toBe(r.name)
  })

  it('lists the same crisp set', () => {
    const line = section.split('`crisp`:')[1].split('.')[0]
    const names = [...line.matchAll(/([a-z_]+) \((\d+)\)/g)].map((m) => [m[1], Number(m[2])] as const)
    expect(new Set(names.map(([, code]) => code))).toEqual(CRISP_TERRAINS)
    for (const [name, code] of names) expect(TILE_NAMES[code].toLowerCase().replace(/ /g, '_')).toBe(name)
  })

  it('is a total order over the fringing terrains: every code has exactly one place, ranked or crisp, none both', () => {
    expect(new Set(TERRAIN_PRIORITY).size).toBe(TERRAIN_PRIORITY.length)
    for (const code of TERRAIN_CODES) expect([rankOf(code) !== undefined, CRISP_TERRAINS.has(code)]).not.toEqual([true, true])
    for (const code of TERRAIN_CODES) expect(rankOf(code) !== undefined || CRISP_TERRAINS.has(code)).toBe(true)
  })
})

describe('borderOverlays', () => {
  it('draws nothing between equal codes or on an all-equal map', () => {
    const map = mapOf([[GRASS, GRASS, GRASS], [GRASS, GRASS, GRASS], [GRASS, GRASS, GRASS]])
    expect(borderOverlays(map, 1, 1, ALL_MASKS)).toEqual([])
  })

  it('fringes the higher neighbour onto the lower cell only', () => {
    const map = mapOf([[WATER, DESERT]])
    expect(summary(borderOverlays(map, 0, 0, ALL_MASKS))).toEqual([`${DESERT}:edge:90`]) // water takes desert's fringe on its east side
    expect(borderOverlays(map, 1, 0, ALL_MASKS)).toEqual([]) // desert takes nothing from water
  })

  it('a crisp terrain neither gives nor takes', () => {
    const map = mapOf([[WATER, WALL]])
    expect(borderOverlays(map, 0, 0, ALL_MASKS)).toEqual([]) // wall gives nothing
    expect(borderOverlays(map, 1, 0, ALL_MASKS)).toEqual([]) // wall takes nothing
    const other = mapOf([[WALL, FOREST]])
    expect(borderOverlays(other, 0, 0, ALL_MASKS)).toEqual([])
  })

  it('maps north, east, south and west to rotations 0, 90, 180 and 270', () => {
    const grid = (nx: number, ny: number) => mapOf([[SHALLOW, SHALLOW, SHALLOW], [SHALLOW, SHALLOW, SHALLOW], [SHALLOW, SHALLOW, SHALLOW]].map((row, y) => row.map((c, x) => (x === nx && y === ny ? FOREST : c))))
    expect(summary(borderOverlays(grid(1, 0), 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:0`])
    expect(summary(borderOverlays(grid(2, 1), 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:90`])
    expect(summary(borderOverlays(grid(1, 2), 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:180`])
    expect(summary(borderOverlays(grid(0, 1), 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:270`])
  })

  it('four matching sides become two inner corners, not four edges', () => {
    const map = mapOf([[WATER, FOREST, WATER], [FOREST, WATER, FOREST], [WATER, FOREST, WATER]])
    expect(summary(borderOverlays(map, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:inner_corner:0`, `${FOREST}:inner_corner:180`])
  })

  it('draws an outer corner for a higher diagonal neighbour whose adjacent sides are not that terrain', () => {
    const map = mapOf([[WATER, WATER, FOREST], [WATER, WATER, WATER], [WATER, WATER, WATER]])
    expect(summary(borderOverlays(map, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:outer_corner:0`]) // (2,0) is the north-east diagonal of (1,1)
    const south = mapOf([[WATER, WATER, WATER], [WATER, WATER, WATER], [FOREST, WATER, WATER]])
    expect(summary(borderOverlays(south, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:outer_corner:180`]) // south-west
    const withSide = mapOf([[WATER, WATER, FOREST], [WATER, WATER, FOREST], [WATER, WATER, WATER]])
    expect(summary(borderOverlays(withSide, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:90`]) // the side already covers the diagonal
  })

  it('replaces two adjacent edges of the same higher terrain with one inner corner', () => {
    const map = mapOf([[WATER, FOREST, WATER], [WATER, WATER, FOREST], [WATER, WATER, WATER]])
    expect(summary(borderOverlays(map, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:inner_corner:0`]) // N and E are forest: one NE inner corner
    expect(summary(borderOverlays(map, 1, 1, only('edge')))).toEqual([`${FOREST}:edge:0`, `${FOREST}:edge:90`]) // inner corner mask missing: its two edges
  })

  it('does not use the same side twice when three sides match', () => {
    const map = mapOf([[WATER, FOREST, WATER], [WATER, WATER, FOREST], [WATER, FOREST, WATER]])
    expect(summary(borderOverlays(map, 1, 1, ALL_MASKS))).toEqual([`${FOREST}:edge:180`, `${FOREST}:inner_corner:0`])
  })

  it('draws lower-ranked neighbours first', () => {
    const map = mapOf([[WATER, FOREST, WATER], [DESERT, WATER, GRASS], [WATER, WATER, WATER]])
    const order = borderOverlays(map, 1, 1, ALL_MASKS).map((p) => p.neighbour)
    expect(order).toEqual([...order].sort((a, b) => (rankOf(a) as number) - (rankOf(b) as number)))
    expect(order).toEqual([DESERT, GRASS, FOREST])
  })

  it('gives nothing off the map, for an unknown code, or without a mask', () => {
    expect(borderOverlays(mapOf([[WATER]]), 0, 0, ALL_MASKS)).toEqual([]) // map edge is not a neighbour
    expect(borderOverlays(mapOf([[WATER]]), 5, 5, ALL_MASKS)).toEqual([])
    expect(borderOverlays(mapOf([[999, FOREST]]), 0, 0, ALL_MASKS)).toEqual([])
    expect(borderOverlays(mapOf([[WATER, DESERT]]), 0, 0, NO_MASKS)).toEqual([]) // a missing mask is today's hard edge
    expect(summary(borderOverlays(mapOf([[WATER, DESERT]]), 0, 0, only('outer_corner')))).toEqual([])
  })

  it('is deterministic per cell and picks only declared variants', () => {
    const map = mapOf([[WATER, FOREST, WATER, FOREST, WATER, FOREST]])
    const first = [0, 2, 4].map((x) => borderOverlays(map, x, 0, ALL_MASKS))
    expect([0, 2, 4].map((x) => borderOverlays(map, x, 0, ALL_MASKS))).toEqual(first)
    for (const overlays of first) for (const o of overlays) expect(['v1', 'v2', 'v3']).toContain(o.detail)
    expect(new Set(Array.from({ length: 40 }, (_, i) => borderOverlays(mapOf([[WATER, FOREST]]), i * 2, 0, ALL_MASKS)).flat().map((o) => o.detail)).size).toBeGreaterThan(0)
  })
})

const px = (fill: (x: number, y: number) => [number, number, number, number]): Rgba => {
  const out = new Uint8ClampedArray(TILE_PIXELS * TILE_PIXELS * 4)
  for (let y = 0; y < TILE_PIXELS; y++) for (let x = 0; x < TILE_PIXELS; x++) out.set(fill(x, y), (y * TILE_PIXELS + x) * 4)
  return out
}
const solid = (r: number, g: number, b: number): Rgba => px(() => [r, g, b, 255])
const at = (p: Rgba, x: number, y: number) => Array.from(p.subarray((y * TILE_PIXELS + x) * 4, (y * TILE_PIXELS + x) * 4 + 4))

describe('rotate', () => {
  const marker = px((x, y) => (x === 15 && y === 0 ? [255, 0, 0, 255] : [0, 0, 0, 0]))
  it('turns a north-east pixel clockwise to south-east, south-west, north-west', () => {
    expect(at(rotate(marker, 90), 15, 15)).toEqual([255, 0, 0, 255])
    expect(at(rotate(marker, 180), 0, 15)).toEqual([255, 0, 0, 255])
    expect(at(rotate(marker, 270), 0, 0)).toEqual([255, 0, 0, 255])
    expect(rotate(marker, 0)).toEqual(marker)
  })
})

describe('the depth cap', () => {
  it('is the approved 4 px, as the criteria doc states', () => {
    expect(BORDER_DEPTH).toBe(4)
    expect(readFileSync(resolve(__dirname, '../../../../docs/assets/pilot_terrain_m5_criteria.md'), 'utf8')).toContain('**Depth cap: 4 px.**')
  })

  const deepEdge = px((_, y) => (y < 6 ? [0, 0, 0, 255] : [0, 0, 0, 0]))
  const okEdge = px((_, y) => (y < BORDER_DEPTH ? [0, 0, 0, 255] : [0, 0, 0, 0]))
  const centre = px((x, y) => (x === 8 && y === 8 ? [0, 0, 0, 255] : [0, 0, 0, 0]))

  it('flags a mask pixel beyond the cap or in the wrong place for its kind', () => {
    expect(maskCapViolation('edge', okEdge)).toBeNull()
    expect(maskCapViolation('edge', deepEdge)).toEqual({ x: 0, y: BORDER_DEPTH })
    expect(maskCapViolation('edge', centre)).not.toBeNull()
    expect(maskCapViolation('outer_corner', okEdge)).not.toBeNull() // a corner mask may not run along the whole edge
    expect(maskCapViolation('inner_corner', okEdge)).toBeNull()
  })

  it('composeCell never draws beyond 4 px, whatever the mask holds, in any rotation', () => {
    const base = solid(10, 10, 10)
    const tile = solid(200, 200, 200)
    const full = solid(0, 0, 0) // a mask that is opaque everywhere
    for (const rotation of [0, 90, 180, 270] as const) {
      for (const kind of ['edge', 'outer_corner', 'inner_corner'] as const) {
        const out = composeCell(base, [{ neighbour: FOREST, kind, rotation, maskKey: MASK_KEYS[kind], detail: 'v1' }], () => tile, () => full)
        expect(at(out, 7, 7)).toEqual([10, 10, 10, 255]) // the cell centre is always its own terrain
        expect(at(out, 8, 8)).toEqual([10, 10, 10, 255])
        for (let y = 0; y < TILE_PIXELS; y++) for (let x = 0; x < TILE_PIXELS; x++) {
          if (at(out, x, y)[0] === 200) expect(Math.min(x, y, TILE_PIXELS - 1 - x, TILE_PIXELS - 1 - y)).toBeLessThan(4) // the approved cap (user, 2026-10-06), not the constant under test
        }
      }
    }
  })

  it('shows the neighbour tile pixels (not a colour) where the rotated mask is opaque, and the base elsewhere', () => {
    const base = solid(10, 10, 10)
    const tile = px((x, y) => [x * 10, y * 10, 5, 255])
    const edgeMask = px((x, y) => (y < 2 && x % 2 === 0 ? [0, 0, 0, 255] : [0, 0, 0, 0]))
    const north = composeCell(base, [{ neighbour: FOREST, kind: 'edge', rotation: 0, maskKey: 'border.edge', detail: 'v1' }], () => tile, () => edgeMask)
    expect(at(north, 4, 1)).toEqual([40, 10, 5, 255])
    expect(at(north, 5, 1)).toEqual([10, 10, 10, 255])
    expect(at(north, 4, 2)).toEqual([10, 10, 10, 255])
    const east = composeCell(base, [{ neighbour: FOREST, kind: 'edge', rotation: 90, maskKey: 'border.edge', detail: 'v1' }], () => tile, () => edgeMask)
    expect(at(east, 14, 4)).toEqual([140, 40, 5, 255])
    expect(at(east, 14, 5)).toEqual([10, 10, 10, 255])
  })

  it('leaves its inputs untouched and skips an overlay whose tile or mask is unavailable', () => {
    const base = solid(10, 10, 10)
    const copy = new Uint8ClampedArray(base)
    const out = composeCell(base, [{ neighbour: FOREST, kind: 'edge', rotation: 0, maskKey: 'border.edge', detail: 'v1' }], () => undefined, () => solid(0, 0, 0))
    expect(base).toEqual(copy)
    expect(out).toEqual(base)
  })
})
