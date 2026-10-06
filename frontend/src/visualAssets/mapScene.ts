// The whole-map scene of the terrain-set M5 rerun (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, docs/assets/pilot_terrain_m5_criteria.md "AM5-W03-SET"): the predeclared 40 x 24 layout (`terrainAt`,
// every one of the 23 Live Map codes in patches), drawn from a RUNTIME view (the rc-0005 export, i.e. the real path adopted art -> release -> client) with the terrain borders on or off, and as the
// flat-fill control. Markers are drawn the way the Live Map draws them (pilotScene copies) and sit on top of the fringes. Isolated rehearsal code: nothing here is the Live Map.
import { composeBorderedCells, drawComposedCells, type ComposedCell, type Rasterize } from './borderRender'
import type { Rgba } from './terrainBorders'
import { CELL_SIZE } from './cell'
import type { View } from './loader'
import { drawMarker, type Marker, type MarkerKind, type PilotCtx } from './pilotScene'
import { MAP_COLUMNS, MAP_ROWS, TERRAIN_CODES, TERRAIN_DRAFT_KEYS, TILE_COLORS_COPY, mapCodes, terrainAt } from './terrainDrafts'


export const FOREST = 6
export const SWAMP = 8
export const MOUNTAIN = 9
// Predeclared: in row-major order the first six Forest cells carry these markers; the first Swamp cell a goblin and the first Mountain cell a hero.
const FOREST_MARKERS: readonly MarkerKind[] = ['hero', 'goblin', 'wolf', 'store', 'inn', 'goblin_warrior']

export function mapMarkers(): Marker[] {
  const first = (code: number, count: number): [number, number][] => {
    const out: [number, number][] = []
    for (let y = 0; y < MAP_ROWS && out.length < count; y++) for (let x = 0; x < MAP_COLUMNS && out.length < count; x++) if (terrainAt(x, y) === code) out.push([x, y])
    return out
  }
  return [
    ...first(FOREST, FOREST_MARKERS.length).map(([x, y], i) => ({ kind: FOREST_MARKERS[i], x, y })),
    ...first(SWAMP, 1).map(([x, y]) => ({ kind: 'goblin' as const, x, y })),
    ...first(MOUNTAIN, 1).map(([x, y]) => ({ kind: 'hero' as const, x, y })),
  ]
}

/** Facts the criteria doc promises about the layout: every code present, the largest square patch per code, and which forest slots the cells show. */
export function layoutFacts(): { codes: number[]; patchSide: Map<number, number>; cellsPerCode: Map<number, number> } {
  const grid = mapCodes()
  const patchSide = new Map<number, number>()
  const cellsPerCode = new Map<number, number>()
  for (const row of grid) for (const code of row) cellsPerCode.set(code, (cellsPerCode.get(code) ?? 0) + 1)
  for (let y = 0; y < MAP_ROWS; y++) {
    for (let x = 0; x < MAP_COLUMNS; x++) {
      const code = grid[y][x]
      let side = 1
      while (x + side < MAP_COLUMNS && y + side < MAP_ROWS) {
        let all = true
        for (let i = 0; i <= side && all; i++) all = grid[y + side][x + i] === code && grid[y + i][x + side] === code
        if (!all) break
        side++
      }
      patchSide.set(code, Math.max(patchSide.get(code) ?? 0, side))
    }
  }
  return { codes: [...cellsPerCode.keys()].sort((a, b) => a - b), patchSide, cellsPerCode }
}

export type MapCtx = PilotCtx & Pick<CanvasRenderingContext2D, 'putImageData'>
export type MapMode = 'image' | 'flat'

/** What was drawn for one cell of the image scene: the tile of a key (with its picked forest slot) or the flat fill (the key's image was not available). */
export interface MapCellOutcome {
  readonly x: number
  readonly y: number
  readonly code: number
  readonly kind: 'tile' | 'fill'
  readonly detail: string | null
}

/**
 * The scene. 'flat' is the control: every cell is its flat fill. 'image' draws each terrain's tile from the view (a code whose key is missing from the release, or whose image is
 * unavailable, shows its flat fill: the role's own fallback), then the fringes when `borders` (a missing mask means no fringe), then the markers. Returns the per-cell outcomes and the fringed cells.
 */
export function drawMapScene(
  ctx: MapCtx, view: View | null, mode: MapMode, options: { borders: boolean; rasterize?: Rasterize; makeImage?: (pixels: Rgba) => ImageData } = { borders: false },
): { outcomes: MapCellOutcome[]; fringed: ComposedCell[] } {
  const outcomes: MapCellOutcome[] = []
  ctx.imageSmoothingEnabled = false
  for (let y = 0; y < MAP_ROWS; y++) {
    for (let x = 0; x < MAP_COLUMNS; x++) {
      const code = terrainAt(x, y)
      const px = x * CELL_SIZE
      const py = y * CELL_SIZE
      let outcome: MapCellOutcome = { x, y, code, kind: 'fill', detail: null }
      if (mode === 'image' && view !== null) {
        const key = TERRAIN_DRAFT_KEYS[code]
        const result = key === undefined ? null : view.resolve(key, { x, y })
        const bitmap = result?.kind === 'image' ? view.bitmapFor(result.file) : undefined
        if (result?.kind === 'image' && bitmap) {
          ctx.drawImage(bitmap as unknown as CanvasImageSource, px, py)
          outcome = { x, y, code, kind: 'tile', detail: result.detail ?? null }
        }
      }
      if (outcome.kind === 'fill') {
        ctx.fillStyle = TILE_COLORS_COPY[code]
        ctx.fillRect(px, py, CELL_SIZE, CELL_SIZE)
      }
      outcomes.push(outcome)
    }
  }
  let fringed: ComposedCell[] = []
  if (mode === 'image' && view !== null && options.borders && options.rasterize !== undefined) {
    fringed = composeBorderedCells(view, new Map(), options.rasterize)
    drawComposedCells(ctx, view, new Map(), fringed, options.makeImage)
  }
  for (const marker of mapMarkers()) drawMarker(ctx, marker)
  ctx.textBaseline = 'alphabetic'
  return { outcomes, fringed }
}

export { TERRAIN_CODES }
