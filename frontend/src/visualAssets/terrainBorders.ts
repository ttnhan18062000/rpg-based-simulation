// Terrain borders, contract version 1 (TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT). Layered fringes in the style of Battle for Wesnoth: each terrain has a rank; where two
// terrains meet, the higher one draws a ragged fringe of its own texture onto the lower one, through ONE shared set of mask shapes (no per-pair art). Pure and deterministic: no I/O,
// no clock, no `Math.random`, nothing from the simulation. Look only: a fringe never changes what a cell IS, so it is capped to the outer BORDER_DEPTH pixels and a missing
// mask means no fringe (today's hard edge). The order below is the one in docs/assets/pilot_terrain_m5_criteria.md ("AM5-B"); a test asserts they are equal.
import { DETAIL_SEED, pickDetail } from './pickDetail'

export const BORDER_CONTRACT_VERSION = 1
/** A fringe covers at most this many pixels from the cell edge, so the cell centre always shows its own terrain. */
export const BORDER_DEPTH = 4
export const TILE_PIXELS = 16

/** Lowest first. A terrain draws a fringe only onto a terrain of lower rank. Codes are the Live Map's tile codes. */
export const TERRAIN_PRIORITY: readonly number[] = Object.freeze([
  2, // water
  18, // shallow_water
  14, // lava
  0, // floor
  20, // cave
  21, // volcanic
  8, // swamp
  7, // desert
  16, // snow
  10, // road
  19, // farmland
  15, // grassland
  9, // mountain
  17, // jungle
  6, // forest
])
/** Built, hard-edged terrains: they neither draw a fringe nor receive one. Wall, town, camp, sanctuary, bridge, ruins, dungeon entrance, graveyard. */
export const CRISP_TERRAINS: ReadonlySet<number> = new Set([1, 3, 4, 5, 11, 12, 13, 22])

const RANK = new Map<number, number>(TERRAIN_PRIORITY.map((code, index) => [code, index + 1]))
/** Rank of a code (1 = lowest), or undefined for a crisp or unknown code. */
export function rankOf(code: number): number | undefined {
  return RANK.get(code)
}

export type MaskKind = 'edge' | 'outer_corner' | 'inner_corner'
export const MASK_KEYS: Readonly<Record<MaskKind, string>> = Object.freeze({
  edge: 'border.edge',
  outer_corner: 'border.outer_corner',
  inner_corner: 'border.inner_corner',
})
/** Quarter turns clockwise, in degrees. Authored orientation is 0: `edge` on the north side, both corners at the north-east. */
export type Rotation = 0 | 90 | 180 | 270

/** One mask piece to draw over a cell's own tile. `detail` is the variant picked for this cell and piece. */
export interface BorderOverlay {
  readonly neighbour: number // the higher terrain whose tile pixels the fringe shows
  readonly kind: MaskKind
  readonly rotation: Rotation
  readonly maskKey: string
  readonly detail: string
}

/** What the compositor needs to know about the masks: the declared variants of a mask key, in declared order; an empty list means the mask is not available. */
export interface MaskAvailability {
  variants(maskKey: string): readonly string[]
}

type Side = 'N' | 'E' | 'S' | 'W'
type Corner = 'NE' | 'SE' | 'SW' | 'NW'
const SIDES: readonly Side[] = ['N', 'E', 'S', 'W']
const SIDE_DELTA: Readonly<Record<Side, readonly [number, number]>> = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] }
const SIDE_ROTATION: Readonly<Record<Side, Rotation>> = { N: 0, E: 90, S: 180, W: 270 }
// Corner, its diagonal offset, the two sides next to it (first, second clockwise) and the rotation of the corner masks.
const CORNERS: readonly { corner: Corner; delta: readonly [number, number]; sides: readonly [Side, Side]; rotation: Rotation }[] = [
  { corner: 'NE', delta: [1, -1], sides: ['N', 'E'], rotation: 0 },
  { corner: 'SE', delta: [1, 1], sides: ['E', 'S'], rotation: 90 },
  { corner: 'SW', delta: [-1, 1], sides: ['S', 'W'], rotation: 180 },
  { corner: 'NW', delta: [-1, -1], sides: ['W', 'N'], rotation: 270 },
]

/** Terrain code at a map cell, or undefined off the map. */
export type CodeAt = (x: number, y: number) => number | undefined

function higher(code: number, neighbour: number | undefined): neighbour is number {
  if (neighbour === undefined || CRISP_TERRAINS.has(code) || CRISP_TERRAINS.has(neighbour)) return false
  const own = RANK.get(code)
  const other = RANK.get(neighbour)
  return own !== undefined && other !== undefined && other > own
}

/**
 * The mask pieces to draw over cell (x, y), in draw order: neighbours by ascending rank (lower first), and per neighbour the edges (N E S W), then inner corners, then outer corners
 * (NE SE SW NW). Two adjacent sides with the same higher neighbour give one inner corner instead of two edges (greedy in corner order NE SE SW NW; a side is used once). A piece whose mask
 * is not available is left out, except that a missing inner corner falls back to its two edges. Nothing is drawn between equal codes, onto a higher cell, or from or onto a crisp terrain.
 */
export function borderOverlays(codeAt: CodeAt, x: number, y: number, masks: MaskAvailability, seed: number = DETAIL_SEED): BorderOverlay[] {
  const code = codeAt(x, y)
  if (code === undefined || CRISP_TERRAINS.has(code) || !RANK.has(code)) return []
  const sideCode = new Map<Side, number>()
  for (const side of SIDES) {
    const [dx, dy] = SIDE_DELTA[side]
    const n = codeAt(x + dx, y + dy)
    if (higher(code, n)) sideCode.set(side, n)
  }
  const cornerCode = new Map<Corner, number>()
  for (const { corner, delta } of CORNERS) {
    const n = codeAt(x + delta[0], y + delta[1])
    if (higher(code, n)) cornerCode.set(corner, n)
  }
  const neighbours = [...new Set([...sideCode.values(), ...cornerCode.values()])].sort((a, b) => (RANK.get(a) as number) - (RANK.get(b) as number))
  const out: BorderOverlay[] = []
  const piece = (neighbour: number, kind: MaskKind, rotation: Rotation): boolean => {
    const maskKey = MASK_KEYS[kind]
    const variants = masks.variants(maskKey)
    if (variants.length === 0) return false
    const detail = pickDetail(`border:${maskKey}:${neighbour}:${rotation}`, x, y, seed, variants)
    out.push({ neighbour, kind, rotation, maskKey, detail })
    return true
  }
  for (const h of neighbours) {
    const used = new Set<Side>()
    const edges: Side[] = []
    const inner: (typeof CORNERS)[number][] = []
    for (const c of CORNERS) {
      const [a, b] = c.sides
      if (sideCode.get(a) === h && sideCode.get(b) === h && !used.has(a) && !used.has(b)) {
        inner.push(c)
        used.add(a)
        used.add(b)
      }
    }
    for (const side of SIDES) if (sideCode.get(side) === h && !used.has(side)) edges.push(side)
    // A missing inner corner mask falls back to its two edges (each still a valid fringe).
    const innerAvailable = masks.variants(MASK_KEYS.inner_corner).length > 0
    if (!innerAvailable) for (const c of inner) edges.push(...c.sides)
    for (const side of SIDES.filter((s) => edges.includes(s))) piece(h, 'edge', SIDE_ROTATION[side])
    if (innerAvailable) for (const c of inner) piece(h, 'inner_corner', c.rotation)
    for (const c of CORNERS) {
      if (cornerCode.get(c.corner) === h && sideCode.get(c.sides[0]) !== h && sideCode.get(c.sides[1]) !== h) piece(h, 'outer_corner', c.rotation)
    }
  }
  return out
}

// ---- Pixels -------------------------------------------------------------------------------------------------------------------------------------------------------------------

/** A 16 x 16 RGBA image, row-major, 4 bytes a pixel. */
export type Rgba = Uint8ClampedArray

/** `rotation` quarter turns clockwise of a 16 x 16 RGBA image (a new array). */
export function rotate(pixels: Rgba, rotation: Rotation): Rgba {
  const out = new Uint8ClampedArray(pixels.length)
  const turns = rotation / 90
  for (let y = 0; y < TILE_PIXELS; y++) {
    for (let x = 0; x < TILE_PIXELS; x++) {
      let sx = x
      let sy = y
      for (let t = 0; t < turns; t++) {
        // inverse of one clockwise turn: destination (x, y) comes from source (y, N - 1 - x)
        const nx = sy
        const ny = TILE_PIXELS - 1 - sx
        sx = nx
        sy = ny
      }
      const from = (sy * TILE_PIXELS + sx) * 4
      const to = (y * TILE_PIXELS + x) * 4
      out.set(pixels.subarray(from, from + 4), to)
    }
  }
  return out
}

/** True when pixel (x, y) is within `depth` pixels of the cell edge that the authored-orientation mask of `kind` may cover (north edge; north-east corner; north and east edges). */
function allowedAuthored(kind: MaskKind, x: number, y: number, depth: number): boolean {
  const north = y < depth
  const east = x >= TILE_PIXELS - depth
  if (kind === 'edge') return north
  if (kind === 'outer_corner') return north && east
  return north || east
}

/** The first opaque (alpha > 0) pixel of an authored-orientation mask that lies outside what its kind may cover, or null: the cap check for a committed or test mask. */
export function maskCapViolation(kind: MaskKind, mask: Rgba, depth: number = BORDER_DEPTH): { x: number; y: number } | null {
  for (let y = 0; y < TILE_PIXELS; y++) {
    for (let x = 0; x < TILE_PIXELS; x++) {
      if (mask[(y * TILE_PIXELS + x) * 4 + 3] > 0 && !allowedAuthored(kind, x, y, depth)) return { x, y }
    }
  }
  return null
}

/**
 * Compose one cell: the cell's own tile with each overlay's fringe on top. The fringe shows the NEIGHBOUR tile's pixels at the same in-cell coordinates wherever the (rotated) mask is
 * opaque (alpha >= 128, the masks are 1-bit shapes). The depth cap is enforced here, whatever a mask contains: a mask pixel outside what its kind may cover (after rotation) is ignored,
 * so the cell centre always shows its own terrain. Pure; returns a new array and leaves every input untouched.
 */
export function composeCell(base: Rgba, overlays: readonly BorderOverlay[], tileOf: (code: number) => Rgba | undefined, maskOf: (maskKey: string, detail: string) => Rgba | undefined): Rgba {
  const out = new Uint8ClampedArray(base)
  for (const overlay of overlays) {
    const tile = tileOf(overlay.neighbour)
    const mask = maskOf(overlay.maskKey, overlay.detail)
    if (tile === undefined || mask === undefined) continue
    const allowed = new Uint8Array(TILE_PIXELS * TILE_PIXELS)
    for (let y = 0; y < TILE_PIXELS; y++) {
      for (let x = 0; x < TILE_PIXELS; x++) allowed[y * TILE_PIXELS + x] = allowedAuthored(overlay.kind, x, y, BORDER_DEPTH) ? 1 : 0
    }
    const rotatedAllowed = rotateMask(allowed, overlay.rotation)
    const rotated = rotate(mask, overlay.rotation)
    for (let i = 0; i < TILE_PIXELS * TILE_PIXELS; i++) {
      if (rotatedAllowed[i] === 1 && rotated[i * 4 + 3] >= 128) out.set(tile.subarray(i * 4, i * 4 + 4), i * 4)
    }
  }
  return out
}

function rotateMask(flags: Uint8Array, rotation: Rotation): Uint8Array {
  const asRgba = new Uint8ClampedArray(flags.length * 4)
  flags.forEach((v, i) => (asRgba[i * 4 + 3] = v === 1 ? 255 : 0))
  const turned = rotate(asRgba, rotation)
  return Uint8Array.from({ length: flags.length }, (_, i) => (turned[i * 4 + 3] > 0 ? 1 : 0))
}
