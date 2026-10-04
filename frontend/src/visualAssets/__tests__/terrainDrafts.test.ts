import { describe, expect, it, vi } from 'vitest'
import { TILE_COLORS, TILE_NAMES } from '@/constants/colors'
import { VISUAL_KEY } from '../manifest'
import { MAP_COLUMNS, MAP_ROWS, TERRAIN_CODES, TERRAIN_DRAFT_KEYS, TILE_COLORS_COPY, TILE_NAMES_COPY, mapCodes, terrainAt } from '../terrainDrafts'

describe('the Live Map constants the page copies', () => {
  it('equal the originals, which the page does not import', () => {
    expect(TILE_NAMES_COPY).toEqual(TILE_NAMES)
    expect(TILE_COLORS_COPY).toEqual(TILE_COLORS)
  })
})

describe('the terrain code to visual key table', () => {
  it('covers every Live Map terrain code exactly once, with a valid, unique key that is terrain. plus the snake_case of the name', () => {
    expect(TERRAIN_CODES).toHaveLength(23)
    expect(Object.keys(TERRAIN_DRAFT_KEYS).map(Number).sort((a, b) => a - b)).toEqual([...TERRAIN_CODES])
    const keys = TERRAIN_CODES.map((code) => TERRAIN_DRAFT_KEYS[code])
    expect(new Set(keys).size).toBe(keys.length)
    for (const code of TERRAIN_CODES) {
      expect(TERRAIN_DRAFT_KEYS[code]).toMatch(VISUAL_KEY)
      expect(TERRAIN_DRAFT_KEYS[code]).toBe(`terrain.${TILE_NAMES[code].toLowerCase().replace(/ /g, '_')}`)
    }
  })
})

describe('the sample map', () => {
  it('is deterministic: the same codes every time, including after a fresh module load', async () => {
    const first = mapCodes()
    expect(mapCodes()).toEqual(first)
    expect(first).toHaveLength(MAP_ROWS)
    expect(first.every((row) => row.length === MAP_COLUMNS)).toBe(true)
    expect(terrainAt(3, 4)).toBe(first[4][3])
    vi.resetModules()
    const fresh = await import('../terrainDrafts')
    expect(fresh.mapCodes()).toEqual(first)
  })

  it('uses every terrain code in a patch of several cells', () => {
    const counts = new Map<number, number>()
    for (const row of mapCodes()) for (const code of row) counts.set(code, (counts.get(code) ?? 0) + 1)
    expect([...counts.keys()].sort((a, b) => a - b)).toEqual([...TERRAIN_CODES])
    for (const code of TERRAIN_CODES) expect(counts.get(code)!, `${TILE_NAMES[code]} patch`).toBeGreaterThanOrEqual(6)
  })

  it('has real patches: most cells have a same-code neighbour', () => {
    const rows = mapCodes()
    let alone = 0
    for (let y = 0; y < MAP_ROWS; y++) for (let x = 0; x < MAP_COLUMNS; x++) {
      const same = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => rows[y + dy]?.[x + dx] === rows[y][x])
      if (!same) alone++
    }
    expect(alone / (MAP_ROWS * MAP_COLUMNS)).toBeLessThan(0.05)
  })
})
