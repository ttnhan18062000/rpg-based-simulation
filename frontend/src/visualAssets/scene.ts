// Native-scale drawing of the rehearsal scenes. Pure functions over a 2D context, so tests drive them with a recorder.
import { CELL_SIZE } from './cell'
import { drawFallback, type Ctx2D } from './fallback'
import type { View } from './loader'

export const SINGLE_KEYS = ['fixture.rehearsal.gem', 'fixture.rehearsal.rock', 'fixture.rehearsal.frame', 'fixture.rehearsal.absent'] as const

export const SCENE_COLUMNS = 12
export const SCENE_ROWS = 8
const PATTERN = ['fixture.rehearsal.gem', 'fixture.rehearsal.rock', 'fixture.rehearsal.frame'] as const
// Predeclared crowded scene: all three keys in a repeating pattern, plus two keys the release does not contain.
const ABSENT_AT = new Set(['3,2', '8,5'])

export function crowdedLayout(): string[] {
  const keys: string[] = []
  for (let y = 0; y < SCENE_ROWS; y++) {
    for (let x = 0; x < SCENE_COLUMNS; x++) {
      keys.push(ABSENT_AT.has(`${x},${y}`) ? 'fixture.rehearsal.absent' : PATTERN[(x + 2 * y) % PATTERN.length])
    }
  }
  return keys
}

/** Draw one cell of `view` at (x, y), 1:1 with smoothing off; an image that is not (or not yet) available shows its typed fallback or nothing. */
export function drawCell(ctx: Ctx2D, view: View | null, visualKey: string, x: number, y: number): void {
  ctx.imageSmoothingEnabled = false
  if (view === null) {
    drawFallback(ctx, { kind: 'fallback', visualKey, family: null, reason: 'manifest_invalid' }, x, y)
    return
  }
  const result = view.resolve(visualKey)
  if (result.kind === 'fallback') {
    drawFallback(ctx, result, x, y)
    return
  }
  const bitmap = view.bitmapFor(result.file)
  if (bitmap) ctx.drawImage(bitmap as unknown as CanvasImageSource, x, y)
  else ctx.clearRect(x, y, CELL_SIZE, CELL_SIZE) // still loading: an empty cell, never a stale image
}

export function drawScene(ctx: Ctx2D, view: View | null, keys: readonly string[] = crowdedLayout()): void {
  keys.forEach((key, index) => drawCell(ctx, view, key, (index % SCENE_COLUMNS) * CELL_SIZE, Math.floor(index / SCENE_COLUMNS) * CELL_SIZE))
}
