// The draft preview page's map (TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE): a deterministic sample map that uses EVERY Live Map terrain code in patches, drawn from a draft
// set so it can be judged as a whole. Isolated rehearsal code: it imports nothing from outside src/visualAssets/. The colours and names are COPIES of the Live Map's own
// constants (tests assert each equals the original, read-only), as in pilotScene.ts.
import { CELL_SIZE } from './cell'
import type { DraftSnapshot } from './draftManifest'
import type { View } from './loader'
import type { Cell } from './resolver'

export const TILE_NAMES_COPY: Readonly<Record<number, string>> = Object.freeze({
  0: 'Floor', 1: 'Wall', 2: 'Water', 3: 'Town', 4: 'Camp', 5: 'Sanctuary', 6: 'Forest', 7: 'Desert', 8: 'Swamp', 9: 'Mountain', 10: 'Road', 11: 'Bridge',
  12: 'Ruins', 13: 'Dungeon Entrance', 14: 'Lava', 15: 'Grassland', 16: 'Snow', 17: 'Jungle', 18: 'Shallow Water', 19: 'Farmland', 20: 'Cave', 21: 'Volcanic', 22: 'Graveyard',
})
export const TILE_COLORS_COPY: Readonly<Record<number, string>> = Object.freeze({
  0: '#1a1d27', 1: '#555b73', 2: '#1e3a5f', 3: '#2d4a3e', 4: '#4a2d2d', 5: '#2d3a4a', 6: '#1b3a1b', 7: '#3a3420', 8: '#2a2a3a', 9: '#3a3a3a', 10: '#5a5040', 11: '#4a6050',
  12: '#4a4035', 13: '#6a3040', 14: '#8a3000', 15: '#4a6030', 16: '#c8d8e8', 17: '#0a4a0a', 18: '#2a5070', 19: '#6a7a40', 20: '#3a3040', 21: '#5a2a1a', 22: '#4a4050',
})

/**
 * The visual key each Live Map terrain code is drafted under: `terrain.` plus the snake_case of its name. ONE explicit table, tested for full and unique coverage of
 * every code. The terrain draft set (TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET) registers and draws exactly these keys.
 */
export const TERRAIN_DRAFT_KEYS: Readonly<Record<number, string>> = Object.freeze({
  0: 'terrain.floor', 1: 'terrain.wall', 2: 'terrain.water', 3: 'terrain.town', 4: 'terrain.camp', 5: 'terrain.sanctuary', 6: 'terrain.forest', 7: 'terrain.desert',
  8: 'terrain.swamp', 9: 'terrain.mountain', 10: 'terrain.road', 11: 'terrain.bridge', 12: 'terrain.ruins', 13: 'terrain.dungeon_entrance', 14: 'terrain.lava',
  15: 'terrain.grassland', 16: 'terrain.snow', 17: 'terrain.jungle', 18: 'terrain.shallow_water', 19: 'terrain.farmland', 20: 'terrain.cave', 21: 'terrain.volcanic',
  22: 'terrain.graveyard',
})
export const TERRAIN_CODES: readonly number[] = Object.freeze(Object.keys(TILE_NAMES_COPY).map(Number).sort((a, b) => a - b))

export const MAP_COLUMNS = 40
export const MAP_ROWS = 24

const noise = (x: number, y: number, k: number): number => Math.abs(((x * 73856093) ^ (y * 19349663) ^ (k * 83492791)) | 0) % 1000 / 1000

/**
 * Terrain code of cell (x, y): the grid is split into one patch per code (a nearest-seed partition over a jittered 6 x 4 lattice, the seeds in a fixed order) with a
 * little noise on the borders, so every code has a patch of several cells and neighbours meet along irregular edges. Pure and deterministic: the same map every time.
 */
const SEED_COLUMNS = 6
const SEED_ROWS = 4
const seeds: readonly { code: number; x: number; y: number }[] = TERRAIN_CODES.map((code, i) => ({
  code,
  x: ((i % SEED_COLUMNS) + 0.5) * (MAP_COLUMNS / SEED_COLUMNS) + (noise(i, 1, 11) - 0.5) * 3,
  y: (Math.floor(i / SEED_COLUMNS) + 0.5) * (MAP_ROWS / SEED_ROWS) + (noise(i, 2, 12) - 0.5) * 2,
}))

export function terrainAt(x: number, y: number): number {
  let best = seeds[0]
  let bestDistance = Infinity
  for (const seed of seeds) {
    const distance = Math.hypot(x - seed.x, y - seed.y) + (noise(x, y, seed.code + 31) - 0.5) * 1.6
    if (distance < bestDistance) {
      best = seed
      bestDistance = distance
    }
  }
  return best.code
}

export function mapCodes(): number[][] {
  return Array.from({ length: MAP_ROWS }, (_, y) => Array.from({ length: MAP_COLUMNS }, (_, x) => terrainAt(x, y)))
}

export type DraftCtx = Pick<
  CanvasRenderingContext2D,
  'fillRect' | 'drawImage' | 'fillStyle' | 'strokeStyle' | 'lineWidth' | 'imageSmoothingEnabled' | 'beginPath' | 'moveTo' | 'lineTo' | 'stroke' | 'save' | 'restore'
>

/** What was drawn for one cell: a draft image (which slot, and whether it is the picked one), or the labelled role fallback. */
export interface CellOutcome {
  readonly code: number
  readonly kind: 'draft' | 'fallback'
  readonly detail: string | null
  readonly picked: string | null
  readonly detailFallback: string | null
}

/**
 * Draw one terrain cell at pixel (px, py). A code whose key the draft set has shows the draft at its logical size (the preview drawn at 1/scale, smoothing off, so each
 * logical pixel is exact), the detail picked by `pickDetail` for the cell; a missing draft shows the flat fill with a diagonal line across it (the labelled role fallback).
 */
export function drawDraftCell(ctx: DraftCtx, view: View | null, code: number, px: number, py: number, cell: Cell, scales: ReadonlyMap<string, number>): CellOutcome {
  ctx.imageSmoothingEnabled = false
  const key = TERRAIN_DRAFT_KEYS[code]
  if (view !== null && key !== undefined) {
    const result = view.resolve(key, cell)
    if (result.kind === 'image') {
      const bitmap = view.bitmapFor(result.file)
      if (bitmap) {
        const scale = scales.get(result.file) ?? 1
        ctx.drawImage(bitmap as unknown as CanvasImageSource, px, py, bitmap.width / scale, bitmap.height / scale)
        return { code, kind: 'draft', detail: result.detail ?? null, picked: result.picked ?? null, detailFallback: result.detailFallback ?? null }
      }
    }
  }
  ctx.fillStyle = TILE_COLORS_COPY[code]
  ctx.fillRect(px, py, CELL_SIZE, CELL_SIZE)
  if (view !== null) {
    ctx.save()
    ctx.strokeStyle = 'rgba(255,255,255,0.35)' // the mark of a missing draft: a diagonal across the flat fill
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(px, py + CELL_SIZE)
    ctx.lineTo(px + CELL_SIZE, py)
    ctx.stroke()
    ctx.restore()
  }
  return { code, kind: 'fallback', detail: null, picked: null, detailFallback: null }
}

/** The whole sample map: `mode` 'draft' draws the drafts (or the labelled fallback), 'flat' is the plain colour fills side by side for comparison. */
export function drawDraftMap(ctx: DraftCtx, view: View | null, mode: 'draft' | 'flat', scales: ReadonlyMap<string, number>): CellOutcome[] {
  const outcomes: CellOutcome[] = []
  for (let y = 0; y < MAP_ROWS; y++) {
    for (let x = 0; x < MAP_COLUMNS; x++) {
      const code = terrainAt(x, y)
      if (mode === 'flat') {
        ctx.fillStyle = TILE_COLORS_COPY[code]
        ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
      } else {
        outcomes.push(drawDraftCell(ctx, view, code, x * CELL_SIZE, y * CELL_SIZE, { x, y }, scales))
      }
    }
  }
  return outcomes
}

/** Per terrain code: which drafts the set holds for its key (each slot, with its source asset), or that it has none. */
export function statusOf(snapshot: DraftSnapshot | null, code: number): { key: string; text: string; missing: boolean } {
  const key = TERRAIN_DRAFT_KEYS[code]
  const entries = snapshot?.entries.filter((e) => e.visualKey === key) ?? []
  if (entries.length === 0) return { key, text: 'missing: the labelled role fallback (flat fill with a diagonal) is shown', missing: true }
  const axis = snapshot?.details.get(key)
  const shown = entries.map((e) => `${e.detail ?? axis?.default ?? 'draft'}: ${e.sourceAssetId} (${e.draftId})`)
  const absent = axis ? axis.values.filter((v) => !entries.some((e) => (e.detail ?? axis.default) === v)) : []
  return { key, text: [...shown, ...absent.map((v) => `${v}: missing, falls back to the default`)].join('; '), missing: false }
}

