// @vitest-environment node
// The pure data of the icon preview page, pinned to its sources of truth: the registry's icon keys, the Python colour-vision matrices, today's grade chips, tile fills and Lucide paths.
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  GLYPH_KEY, GRADE_CHIPS, ICON_KEYS, ICON_SIZES, LUCIDE_PATHS, MACHADO, MARKER_LAYERS, PLATE_KEY, SCENE_COLUMNS, SCENE_MARKERS, SCENE_ROWS, SCENE_ROW_COUNT, TIERS, TILE_FILLS, VISION_FILTERS,
  fallbackFor, sceneKey, tierKey,
} from '../iconScene'

const FRONTEND = process.cwd()
const REPO = path.join(FRONTEND, '..')
const read = (...parts: string[]) => readFileSync(path.join(REPO, ...parts), 'utf8')

describe('the key list matches the registry', () => {
  const yaml = read('visual_assets', 'catalog', 'definitions', 'visual_keys.yaml')
  const registered = yaml.split('\n  - key: ').slice(1).map((block) => [block.split('\n')[0], /description: (.*)/.exec(block)![1]] as const).filter(([k]) => k.startsWith('icon.'))

  it('every drawn key of the page (ICON_SIZES) is in the registry with the size its description states; the 22 icon set v2 keys are registered but not drawn yet', () => {
    const drawn = registered.filter(([k]) => k in ICON_SIZES)
    expect(drawn.map(([k]) => k).sort()).toEqual([...ICON_KEYS])
    for (const [key, description] of drawn) {
      const size = ICON_SIZES[key]
      expect(description, key).toContain(`${size}x${size}`)
    }
    expect(ICON_KEYS).toHaveLength(14)
    expect(registered).toHaveLength(14 + 22) // the key set plus icon set v2 (TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC)
  })

  it('the 22 icon set v2 keys each have a declared fallback that matches the registry description', () => {
    const v2 = registered.filter(([k]) => !(k in ICON_SIZES))
    expect(v2).toHaveLength(22)
    for (const [key, description] of v2) {
      const fb = fallbackFor(key)
      expect(fb.note, key).toMatch(/^identifying/)
      const shown = fb.kind === 'text' ? fb.text : fb.kind === 'chip' ? `${fb.letter} ${fb.color}` : ''
      expect(shown, key).not.toBe('')
      const hex = /#[0-9a-f]{6}/.exec(description)?.[0]
      if (hex) expect(shown, key).toContain(hex) // the colour the registry names is the colour the page shows
    }
  })

  it('plate is drawn first and the glyph over it', () => {
    expect(MARKER_LAYERS).toEqual([PLATE_KEY, GLYPH_KEY])
  })

  it('every key has a declared fallback', () => {
    for (const key of ICON_KEYS) expect(fallbackFor(key).note.length).toBeGreaterThan(0)
    expect(() => fallbackFor('icon.nope')).toThrow()
  })
})

describe('the scene', () => {
  it('is rectangular, uses only known tiles and every marker cell is inside it', () => {
    expect(SCENE_ROWS.every((r) => r.length === SCENE_COLUMNS)).toBe(true)
    for (let y = 0; y < SCENE_ROW_COUNT; y += 1) for (let x = 0; x < SCENE_COLUMNS; x += 1) expect(TILE_FILLS[sceneKey(x, y)], `${x},${y}`).toBeDefined()
    for (const [x, y] of SCENE_MARKERS) expect(x >= 0 && x < SCENE_COLUMNS && y >= 0 && y < SCENE_ROW_COUNT).toBe(true)
  })

  it('puts markers over the darkest tile, snow, grass and water', () => {
    expect(SCENE_MARKERS.map(([x, y]) => sceneKey(x, y)).sort()).toEqual(['terrain.floor', 'terrain.grassland', 'terrain.snow', 'terrain.water'])
  })
})

describe('copies equal their sources', () => {
  it('the colour-vision matrices equal visual_assets/review/pilot_colour_vision.py', () => {
    const source = read('visual_assets', 'review', 'pilot_colour_vision.py')
    for (const vision of ['protan', 'deutan', 'tritan'] as const) {
      const row = new RegExp(`"${vision}": \\(\\((.+?)\\), \\((.+?)\\), \\((.+?)\\)\\)`).exec(source)!
      const parsed = [row[1], row[2], row[3]].map((r) => r.split(',').map((v) => parseFloat(v)))
      expect(MACHADO[vision]).toEqual(parsed)
    }
  })

  it('every filter has a 4x5 matrix (20 numbers) except the unfiltered colour column', () => {
    expect(VISION_FILTERS.map((f) => f.id)).toEqual(['colour', 'grey', 'protan', 'deutan', 'tritan'])
    for (const f of VISION_FILTERS.filter((v) => v.values)) expect(f.values.split(' ')).toHaveLength(20)
    expect(VISION_FILTERS[0].values).toBe('')
  })

  it("the grade chips equal ClassHallPanel's GRADE_COLORS", () => {
    const source = read('frontend', 'src', 'components', 'ClassHallPanel.tsx')
    const block = /const GRADE_COLORS[^{]*\{([^}]+)\}/.exec(source)![1]
    const parsed = Object.fromEntries([...block.matchAll(/'([A-Z]+)':\s*'(#[0-9a-f]{6})'/g)].map((m) => [m[1].toLowerCase(), m[2]]))
    expect(GRADE_CHIPS).toEqual(parsed)
    expect(TIERS.map((t) => tierKey(t))).toHaveLength(8)
  })

  it("the tile fills equal the Live Map's TILE_COLORS for the same terrain codes", () => {
    const colors = read('frontend', 'src', 'constants', 'colors.ts')
    const terrainDrafts = read('frontend', 'src', 'visualAssets', 'terrainDrafts.ts')
    const codeOf = (key: string) => new RegExp(`(\\d+):\\s*'${key.replace('.', '\\.')}'`).exec(terrainDrafts)![1]
    const tileColors = colors.split('export const TILE_COLORS: Record<number, string> = {')[1].split('};')[0]
    for (const [key, fill] of Object.entries(TILE_FILLS)) {
      const found = new RegExp(`\\b${codeOf(key)}:\\s*'(#[0-9a-fA-F]{6})'`).exec(tileColors)![1].toLowerCase()
      expect(found, key).toBe(fill)
    }
  })

  it("the Lucide paths equal the installed lucide-react icons' (ISC)", () => {
    for (const name of ['hammer', 'shield'] as const) {
      const source = readFileSync(path.join(FRONTEND, 'node_modules', 'lucide-react', 'dist', 'esm', 'icons', `${name}.js`), 'utf8')
      const found = [...source.matchAll(/d:\s*"([^"]+)"/g)].map((m) => m[1])
      expect(LUCIDE_PATHS[name]).toEqual(found)
    }
  })
})
