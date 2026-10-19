// Terrain colour and name for the Live Map, read by MEANING from the manifest (`terrain_types`, code -> display name), never by the numeric code:
// /api/v1/map numbers terrain per world, so the same code means different terrain in different worlds. The single hand-kept table is colors.ts
// (TILE_NAMES + TILE_COLORS); this module derives a by-name table from it and adds the names the engine's content uses. An unknown terrain draws a
// visible magenta swatch, never FLOOR.
import { TILE_COLORS, TILE_NAMES } from '@/constants/colors';
import type { Manifest } from '@/types/api';

export const UNKNOWN_TERRAIN_COLOR = '#ff00ff';
const DIM_FACTOR = 0.7;

/** `Shallow Water` -> `shallow_water`: the key a terrain name is looked up by. */
export function terrainKey(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, '_');
}

const COLOR_BY_MEANING: Record<string, string> = (() => {
  const table: Record<string, string> = {};
  for (const [code, name] of Object.entries(TILE_NAMES)) table[terrainKey(name)] = TILE_COLORS[Number(code)];
  // Names the engine's content and compiler use for a meaning the table above already has.
  table.plain = table.grassland;
  table.grass = table.grassland;
  table.ruin = table.ruins;
  table.river = table.shallow_water;
  return table;
})();

function dim(hex: string): string {
  if (!/^#[0-9a-f]{6}$/i.test(hex)) return hex;
  const channel = (i: number) => Math.round(parseInt(hex.slice(1 + 2 * i, 3 + 2 * i), 16) * DIM_FACTOR).toString(16).padStart(2, '0');
  return `#${channel(0)}${channel(1)}${channel(2)}`;
}

export interface TerrainPalette {
  /** Full-brightness fill for a tile code. */
  fill: (code: number) => string;
  /** Dimmed fill (explored fog) for a tile code. */
  dim: (code: number) => string;
  /** The terrain's display name from the manifest, or an explicit unknown label. */
  name: (code: number) => string;
}

/** The palette for one world: codes resolve through the manifest to a terrain name, then to a colour. */
export function buildTerrainPalette(manifest: Manifest | null | undefined): TerrainPalette {
  const names = manifest?.terrain_types ?? {};
  const fill = (code: number): string => {
    const name = names[String(code)];
    return (name !== undefined && COLOR_BY_MEANING[terrainKey(name)]) || UNKNOWN_TERRAIN_COLOR;
  };
  return {
    fill,
    dim: (code) => dim(fill(code)),
    name: (code) => names[String(code)] ?? `Unknown terrain (code ${code})`,
  };
}
