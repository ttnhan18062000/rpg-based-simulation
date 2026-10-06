import { CELL_SIZE } from '@/constants/colors'

// Whole-number pixel scales for pixel art (D20: the Live Map snaps to whole-number scales; docs/assets/icon_research/research_icon_craft.md §1).
// One art pixel must cover a whole number of DEVICE pixels, otherwise some pixels come out wider than others. Pure functions, no DOM.
// A scale is the integer `n` = device pixels per art pixel. In CSS terms the zoom is `n / devicePixelRatio`, so `zoom * dpr` is exactly `n`.

/** The Live Map's world zoom range and default (CSS scale factors before snapping). The old 0.15 step is gone: the reachable levels are `zoomLevels(dpr, min, max)`. */
export const WORLD_MIN_ZOOM = 0.5
export const WORLD_MAX_ZOOM = 3.0
export const WORLD_DEFAULT_ZOOM = 1.0

/** A device pixel ratio the code can divide by: finite and positive, else 1 (a missing or broken `devicePixelRatio`). */
export function normaliseDpr(dpr: number | undefined | null): number {
  return typeof dpr === 'number' && Number.isFinite(dpr) && dpr > 0 ? dpr : 1
}

/**
 * Every reachable zoom (CSS scale factor) between `minZoom` and `maxZoom` inclusive at this device pixel ratio, ascending.
 *
 * **Art levels:** `n / dpr` for integer `n >= 1`. `n` starts at 1 because a fraction of a device pixel per art pixel can never be whole. If the range holds no whole scale the
 * single art level `1 / dpr` is returned.
 *
 * **One overview level at the bottom** (user decision, 2026-10-06: "keep 0.5x as an overview level that draws plain terrain colours instead of pixel art, so it stays crisp"):
 * when `minZoom` is below the first art level, the zoom nearest `minZoom` at which a cell (`CELL_SIZE * zoom`) is a whole number of device pixels is added first. At DPR 1, 1.25 and 1.5 that is
 * 0.5 exactly (8, 10 and 12 device pixels per cell); at DPR 2 the first art level already is 0.5, so nothing is added. Art pixels are NOT whole at the overview level: use
 * `isOverviewZoom` and draw the flat terrain fills there, never the art.
 */
export function zoomLevels(dpr: number, minZoom: number, maxZoom: number): number[] {
  const d = normaliseDpr(dpr)
  const first = Math.max(1, Math.ceil(minZoom * d - 1e-9))
  const last = Math.floor(maxZoom * d + 1e-9)
  const levels: number[] = []
  for (let n = first; n <= last; n += 1) levels.push(n / d)
  if (levels.length === 0) levels.push(1 / d)
  const cellDevicePixels = Math.max(1, Math.round(minZoom * CELL_SIZE * d))
  const overview = cellDevicePixels / (CELL_SIZE * d)
  return overview < levels[0] - 1e-9 ? [overview, ...levels] : levels
}

/**
 * True when one art pixel is not a whole number of device pixels at this zoom: the overview level (and anything below the first art level).
 * The Live Map draws flat `TILE_COLORS` fills at every level today, so nothing changes visibly; the wiring batch's art path MUST check this and draw the fill instead of the art.
 */
export function isOverviewZoom(zoom: number, dpr: number): boolean {
  const devicePixels = zoom * normaliseDpr(dpr)
  return devicePixels < 1 - 1e-9 || Math.abs(devicePixels - Math.round(devicePixels)) > 1e-9
}

/** The level nearest to `zoom` (a tie goes to the larger level). `levels` must be non-empty and ascending. */
export function snapZoom(zoom: number, levels: readonly number[]): number {
  let best = levels[0]
  for (const level of levels) {
    if (Math.abs(level - zoom) <= Math.abs(best - zoom) + 1e-12) best = level
  }
  return best
}

/** One level up (`direction` 1) or down (-1) from the level nearest to `zoom`, clamped to the ends of `levels`. */
export function stepZoom(zoom: number, direction: 1 | -1, levels: readonly number[]): number {
  const at = levels.indexOf(snapZoom(zoom, levels))
  return levels[Math.min(levels.length - 1, Math.max(0, at + direction))]
}

/** Device pixels per art pixel for a zoom: the integer `n` of the level (rounded, so float noise never shows). */
export function deviceScale(zoom: number, dpr: number): number {
  return Math.round(zoom * normaliseDpr(dpr))
}

/** A CSS length rounded to a whole device pixel (for translations: a fractional offset would make pixels uneven again). */
export function snapToDevicePixel(css: number, dpr: number): number {
  const d = normaliseDpr(dpr)
  return Math.round(css * d) / d
}

/**
 * The largest whole-number scale at which a `native` px art image fits a CSS box of `boxCss` px at this device pixel ratio, never fractional.
 * `fits` is false when even scale 1 is larger than the box: the image is then shown at scale 1 (still whole), overflowing, rather than blurred.
 */
export function fitScale(boxCss: number, native: number, dpr: number): { scale: number; cssSize: number; fits: boolean } {
  const d = normaliseDpr(dpr)
  const raw = Math.floor((boxCss * d) / native + 1e-9)
  const scale = Math.max(1, raw)
  return { scale, cssSize: (scale * native) / d, fits: raw >= 1 }
}
