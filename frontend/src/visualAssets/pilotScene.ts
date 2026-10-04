// The pilot terrain role (AM-U21, docs/assets/pilot_terrain_m5_criteria.md): one Live Map terrain cell, tile code 6 (Forest), 16 x 16 at x1.
// Preserved fact = the terrain type, carried by the flat fill and the hover text; the image is decoration. Fallback = exactly the fill.
// The colours, names and markers below are COPIES of the Live Map's own constants (this module imports nothing from outside
// src/visualAssets/); tests assert each equals the original, read-only. Pure functions over a 2D context, so tests drive them with a recorder.
import { CELL_SIZE } from './cell'
import type { View } from './loader'
import type { Cell } from './resolver'

export const PILOT_KEY = 'terrain.forest'
export const FOREST_CODE = 6

export const TILE_COLORS_COPY: Readonly<Record<number, string>> = Object.freeze({
  6: '#1b3a1b', 7: '#3a3420', 8: '#2a2a3a', 9: '#3a3a3a', 15: '#4a6030', 17: '#0a4a0a',
})
export const TILE_NAMES_COPY: Readonly<Record<number, string>> = Object.freeze({
  6: 'Forest', 7: 'Desert', 8: 'Swamp', 9: 'Mountain', 15: 'Grassland', 17: 'Jungle',
})

export const PILOT_COLUMNS = 12
export const PILOT_ROWS = 8
const TERRAIN_CYCLE = [6, 6, 8, 9, 6, 7, 6, 17, 15, 6] as const

/** Terrain code of cell (x, y): the predeclared layout. */
export const terrainAt = (x: number, y: number): number => TERRAIN_CYCLE[(x + 3 * y) % TERRAIN_CYCLE.length]

export type MarkerKind = 'hero' | 'goblin' | 'wolf' | 'goblin_warrior' | 'store' | 'inn'
export interface Marker {
  readonly kind: MarkerKind
  readonly x: number
  readonly y: number
}
// Predeclared: six on forest cells, two on other terrain (control).
export const MARKERS: readonly Marker[] = Object.freeze([
  { kind: 'hero', x: 1, y: 0 }, { kind: 'goblin', x: 4, y: 0 }, { kind: 'wolf', x: 9, y: 0 },
  { kind: 'store', x: 6, y: 1 }, { kind: 'inn', x: 0, y: 2 }, { kind: 'goblin_warrior', x: 1, y: 3 },
  { kind: 'goblin', x: 2, y: 0 }, { kind: 'hero', x: 7, y: 2 },
])

export const KIND_COLORS_COPY: Readonly<Record<string, string>> = Object.freeze({
  hero: '#4a9eff', goblin: '#f87171', wolf: '#a0a0a0', goblin_warrior: '#dc2626',
})
export const BUILDING_COLORS_COPY: Readonly<Record<string, string>> = Object.freeze({ store: '#38bdf8', inn: '#fb923c' })
export const BUILDING_LABELS_COPY: Readonly<Record<string, string>> = Object.freeze({ store: 'S', inn: 'I' })
export const STATE_COLOR_COPY = '#34d399' // STATE_COLORS.WANDER

export type PilotCtx = Pick<
  CanvasRenderingContext2D,
  | 'fillRect' | 'strokeRect' | 'clearRect' | 'drawImage' | 'fillText' | 'fillStyle' | 'strokeStyle' | 'lineWidth' | 'globalAlpha' | 'font'
  | 'textAlign' | 'textBaseline' | 'imageSmoothingEnabled' | 'save' | 'restore' | 'beginPath' | 'moveTo' | 'lineTo' | 'closePath' | 'arc'
  | 'fill' | 'stroke' | 'shadowColor' | 'shadowBlur'
>

/** The hover text of a terrain cell: what the Live Map shows, whatever the cell looks like. */
export const hoverText = (code: number): string => TILE_NAMES_COPY[code] ?? 'Unknown'

/**
 * Draw one terrain cell. Only Forest may show an image, and only when the view has it decoded; every other case shows the flat fill.
 * `cell` is the Live Map cell (column, row), which a key with a detail axis uses to pick its look; without it the key's default is drawn.
 */
export function drawTerrainCell(ctx: PilotCtx, view: View | null, code: number, x: number, y: number, cell?: Cell): void {
  ctx.imageSmoothingEnabled = false
  if (code === FOREST_CODE && view !== null) {
    const result = view.resolve(PILOT_KEY, cell)
    if (result.kind === 'image') {
      const bitmap = view.bitmapFor(result.file)
      if (bitmap) {
        ctx.drawImage(bitmap as unknown as CanvasImageSource, x, y)
        return
      }
    }
  }
  ctx.fillStyle = TILE_COLORS_COPY[code] ?? TILE_COLORS_COPY[FOREST_CODE]
  ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE)
}

/** One marker, drawn the way the Live Map draws it (building: tinted square, outline, letter; hero: diamond with ring; other: disc with ring). */
export function drawMarker(ctx: PilotCtx, marker: Marker): void {
  const bx = marker.x * CELL_SIZE
  const by = marker.y * CELL_SIZE
  const cx = bx + CELL_SIZE / 2
  const cy = by + CELL_SIZE / 2
  if (marker.kind === 'store' || marker.kind === 'inn') {
    const color = BUILDING_COLORS_COPY[marker.kind]
    ctx.fillStyle = color
    ctx.globalAlpha = 0.35
    ctx.fillRect(bx, by, CELL_SIZE, CELL_SIZE)
    ctx.globalAlpha = 1.0
    ctx.strokeStyle = color
    ctx.lineWidth = 1.5
    ctx.strokeRect(bx + 1, by + 1, CELL_SIZE - 2, CELL_SIZE - 2)
    ctx.fillStyle = '#fff'
    ctx.font = 'bold 9px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(BUILDING_LABELS_COPY[marker.kind], cx, cy)
    return
  }
  const color = KIND_COLORS_COPY[marker.kind]
  if (marker.kind === 'hero') {
    const size = CELL_SIZE * 0.45
    ctx.save()
    ctx.shadowColor = '#fbbf24'
    ctx.shadowBlur = 6
    ctx.beginPath()
    ctx.moveTo(cx, cy - size)
    ctx.lineTo(cx + size, cy)
    ctx.lineTo(cx, cy + size)
    ctx.lineTo(cx - size, cy)
    ctx.closePath()
    ctx.fillStyle = color
    ctx.fill()
    ctx.restore()
    ctx.beginPath()
    ctx.moveTo(cx, cy - size - 1.5)
    ctx.lineTo(cx + size + 1.5, cy)
    ctx.lineTo(cx, cy + size + 1.5)
    ctx.lineTo(cx - size - 1.5, cy)
    ctx.closePath()
    ctx.strokeStyle = STATE_COLOR_COPY
    ctx.lineWidth = 1.5
    ctx.stroke()
    return
  }
  const radius = CELL_SIZE * 0.35
  ctx.beginPath()
  ctx.arc(cx, cy, radius, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.beginPath()
  ctx.arc(cx, cy, radius + 1.5, 0, Math.PI * 2)
  ctx.strokeStyle = STATE_COLOR_COPY
  ctx.lineWidth = 1.5
  ctx.stroke()
}

/** The crowded pilot scene. `mode` 'image' draws forest cells with the tile when the view has it; 'flat' is the control (fill everywhere). */
export function drawPilotScene(ctx: PilotCtx, view: View | null, mode: 'image' | 'flat'): void {
  for (let y = 0; y < PILOT_ROWS; y++) {
    for (let x = 0; x < PILOT_COLUMNS; x++) drawTerrainCell(ctx, mode === 'image' ? view : null, terrainAt(x, y), x * CELL_SIZE, y * CELL_SIZE, { x, y })
  }
  for (const marker of MARKERS) drawMarker(ctx, marker)
  ctx.textBaseline = 'alphabetic'
}
