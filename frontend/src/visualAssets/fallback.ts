// Typed per-family fallbacks: a primitive glyph (Canvas rectangles, like the Live Map's own drawing) plus a text label.
// They keep the critical fact of a cell, WHICH ROLE it shows, without the image and without relying on hue: each family has its own
// shape and its own letter, drawn in neutral light-on-dark. The HUD does not participate in this rehearsal (no HUD fallback is defined).
import { CELL_SIZE } from './cell'
import type { FallbackReason, FallbackResult, Resolution } from './resolver'

export type Glyph = 'diamond' | 'disc' | 'frame' | 'cross'

export interface FamilyFallback {
  readonly glyph: Glyph
  readonly letter: string
  readonly name: string
}

// Every family the rehearsal fixtures use (item, terrain, ui) has its own; anything else gets the generic one.
export const FAMILY_FALLBACKS: Readonly<Record<string, FamilyFallback>> = Object.freeze({
  item: { glyph: 'diamond', letter: 'I', name: 'item' },
  terrain: { glyph: 'disc', letter: 'T', name: 'terrain' },
  ui: { glyph: 'frame', letter: 'U', name: 'interface element' },
})
export const GENERIC_FALLBACK: FamilyFallback = Object.freeze({ glyph: 'cross', letter: '?', name: 'unknown visual' })

export function fallbackFor(family: string | null): FamilyFallback {
  return (family !== null && FAMILY_FALLBACKS[family]) || GENERIC_FALLBACK
}

const REASON_TEXT: Readonly<Record<FallbackReason, string>> = {
  unknown_key: 'not in this release',
  missing_image: 'image missing',
  decode_failed: 'image could not be decoded',
  manifest_invalid: 'manifest invalid',
  late_result_dropped: 'late image dropped (newer release shown)',
}

/** The text alternative of a resolution: what the cell shows, readable without seeing it. */
export function describeResolution(result: Resolution): { name: string; detail: string } {
  if (result.kind === 'image') return { name: `${result.visualKey} (${result.family})`, detail: `image ${result.width}x${result.height}` }
  const fallback = fallbackFor(result.family)
  return { name: `${result.visualKey} (${fallback.name})`, detail: `fallback glyph ${fallback.glyph} "${fallback.letter}": ${REASON_TEXT[result.reason]}` }
}

/** The glyph as a CELL_SIZE x CELL_SIZE mask (row-major), so tests can compare shapes and the renderer can paint them. */
export function glyphMask(glyph: Glyph): boolean[] {
  const half = (CELL_SIZE - 1) / 2
  const out: boolean[] = []
  for (let y = 0; y < CELL_SIZE; y++) {
    for (let x = 0; x < CELL_SIZE; x++) {
      const dx = x - half
      const dy = y - half
      const edge = Math.max(Math.abs(dx), Math.abs(dy))
      if (glyph === 'diamond') out.push(Math.abs(dx) + Math.abs(dy) <= half - 0.5)
      else if (glyph === 'disc') out.push(dx * dx + dy * dy <= half * half)
      else if (glyph === 'frame') out.push(edge <= half && edge >= half - 2)
      else out.push(Math.abs(dx) <= 1 || Math.abs(dy) <= 1)
    }
  }
  return out
}

// What drawing needs from a 2D context (a plain CanvasRenderingContext2D satisfies it; tests pass a recorder).
export type Ctx2D = Pick<
  CanvasRenderingContext2D,
  'fillRect' | 'clearRect' | 'drawImage' | 'fillText' | 'fillStyle' | 'font' | 'textAlign' | 'textBaseline' | 'imageSmoothingEnabled'
>

const GLYPH_COLOR = '#d1d5db'
const GLYPH_BACKDROP = '#1f2937'
const LABEL_COLOR = '#111827'

export function drawFallback(ctx: Ctx2D, fallback: FallbackResult, x: number, y: number): void {
  const spec = fallbackFor(fallback.family)
  ctx.fillStyle = GLYPH_BACKDROP
  ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE)
  ctx.fillStyle = GLYPH_COLOR
  const mask = glyphMask(spec.glyph)
  for (let row = 0; row < CELL_SIZE; row++) {
    let start = -1
    for (let col = 0; col <= CELL_SIZE; col++) {
      const on = col < CELL_SIZE && mask[row * CELL_SIZE + col]
      if (on && start < 0) start = col
      if (!on && start >= 0) {
        ctx.fillRect(x + start, y + row, col - start, 1)
        start = -1
      }
    }
  }
  // The letter sits at the cell's centre: dark on a filled glyph, light on the backdrop where the glyph is hollow (the frame), so it is always readable.
  const centreOn = mask[Math.floor(CELL_SIZE / 2) * CELL_SIZE + Math.floor(CELL_SIZE / 2)]
  ctx.fillStyle = centreOn ? LABEL_COLOR : GLYPH_COLOR
  ctx.font = 'bold 9px monospace'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(spec.letter, x + CELL_SIZE / 2, y + CELL_SIZE / 2 + 1)
}
