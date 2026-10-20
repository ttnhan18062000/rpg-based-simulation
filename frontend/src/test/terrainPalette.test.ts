import { describe, expect, it } from 'vitest'
import { TILE_COLORS, TILE_NAMES } from '@/constants/colors'
import { UNKNOWN_TERRAIN_COLOR, buildTerrainPalette, terrainKey } from '@/constants/terrainPalette'
import type { Manifest } from '@/types/api'

const manifest = (terrain_types: Record<string, string>): Manifest => ({ protocol_version: '1.0.0', dictionary_version: 'x', terrain_types, entity_kinds: {}, building_types: {} })

describe('terrain colour follows the terrain meaning from the manifest, not the numeric code', () => {
  it('colours the same meaning the same whichever code a world gave it', () => {
    const a = buildTerrainPalette(manifest({ '0': 'Plain', '1': 'Forest', '2': 'Swamp' }))
    const b = buildTerrainPalette(manifest({ '0': 'Forest', '1': 'Swamp', '2': 'Plain' }))
    expect(a.fill(1)).toBe(b.fill(0)) // forest
    expect(a.fill(2)).toBe(b.fill(1)) // swamp
    expect(a.fill(0)).toBe(b.fill(2)) // plain
    expect(new Set([a.fill(0), a.fill(1), a.fill(2)]).size).toBe(3)
  })

  it('does not paint by the old fixed code table (code 1 is not WALL when the manifest says Forest)', () => {
    const p = buildTerrainPalette(manifest({ '1': 'Forest', '2': 'Plain', '3': 'Swamp' }))
    expect(p.fill(1)).not.toBe(TILE_COLORS[1]) // WALL
    expect(p.fill(2)).not.toBe(TILE_COLORS[2]) // WATER
    expect(p.fill(3)).not.toBe(TILE_COLORS[3]) // TOWN
    expect(p.fill(1)).toBe(TILE_COLORS[Number(Object.keys(TILE_NAMES).find((k) => TILE_NAMES[Number(k)] === 'Forest'))])
  })

  it('draws an unknown terrain, a code the manifest lacks, and a missing manifest as the visible unknown swatch, never FLOOR', () => {
    expect(buildTerrainPalette(manifest({ '0': 'Plain' })).fill(9)).toBe(UNKNOWN_TERRAIN_COLOR)
    expect(buildTerrainPalette(manifest({ '0': 'Moon Dust' })).fill(0)).toBe(UNKNOWN_TERRAIN_COLOR)
    expect(buildTerrainPalette(null).fill(0)).toBe(UNKNOWN_TERRAIN_COLOR)
    expect(UNKNOWN_TERRAIN_COLOR).not.toBe(TILE_COLORS[0])
  })

  it('names a tile from the manifest, and says so when it does not know the code', () => {
    const p = buildTerrainPalette(manifest({ '0': 'Plain', '2': 'Ruin' }))
    expect(p.name(2)).toBe('Ruin')
    expect(p.name(7)).toBe('Unknown terrain (code 7)')
  })

  it('resolves every terrain name the engine content uses to a colour (none falls to the unknown swatch)', () => {
    const names = ['Plain', 'Forest', 'Swamp', 'Cave', 'Mountain', 'Ruin', 'Road', 'Snow', 'Volcanic', 'River', 'Grass', 'Floor']
    const p = buildTerrainPalette(manifest(Object.fromEntries(names.map((n, i) => [String(i), n]))))
    names.forEach((n, i) => expect(p.fill(i), n).not.toBe(UNKNOWN_TERRAIN_COLOR))
  })

  it('dims a colour for explored fog and keys names without case or spacing', () => {
    const p = buildTerrainPalette(manifest({ '0': 'Shallow Water' }))
    expect(p.fill(0)).toBe(TILE_COLORS[18])
    expect(p.dim(0)).not.toBe(p.fill(0))
    expect(terrainKey(' Shallow  Water ')).toBe('shallow_water')
  })
})
