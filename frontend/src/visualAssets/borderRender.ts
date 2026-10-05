// Draws terrain borders on the draft preview page's map (TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS). Isolated rehearsal code: it reads only the mounted draft View, composes with the
// pure compositor in terrainBorders.ts and puts finished cells on a canvas. Nothing here is the Live Map. Decorative: a missing tile or mask leaves the cell exactly as it was drawn.
import { CELL_SIZE } from './cell'
import type { Bitmap, View } from './loader'
import { slotKey } from './manifest'
import { ADOPTED_MARK, MAP_COLUMNS, MAP_ROWS, TERRAIN_DRAFT_KEYS, terrainAt, type FileInfo } from './terrainDrafts'
import { TILE_PIXELS, borderOverlays, composeCell, MASK_KEYS, type MaskAvailability, type Rgba } from './terrainBorders'

/** A 16 x 16 RGBA raster of a preview bitmap drawn at 1/scale with smoothing off, or undefined when none can be made. Injected so tests need no canvas. */
export type Rasterize = (bitmap: Bitmap, scale: number) => Rgba | undefined

export function browserRasterize(bitmap: Bitmap, scale: number): Rgba | undefined {
  if (typeof document === 'undefined') return undefined
  const canvas = document.createElement('canvas')
  canvas.width = TILE_PIXELS
  canvas.height = TILE_PIXELS
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  const read = (ctx as CanvasRenderingContext2D | null)?.getImageData
  if (!ctx || typeof read !== 'function') return undefined
  ctx.imageSmoothingEnabled = false
  ctx.drawImage(bitmap as unknown as CanvasImageSource, 0, 0, bitmap.width / scale, bitmap.height / scale)
  const data = ctx.getImageData(0, 0, TILE_PIXELS, TILE_PIXELS)?.data
  return data === undefined ? undefined : new Uint8ClampedArray(data)
}

export interface ComposedCell {
  readonly x: number
  readonly y: number
  readonly overlays: number
  readonly pixels: Rgba
}

/** The cells of the sample map that get at least one fringe, composed. Pure given `rasterize`; cells without an available tile or mask are left out. */
export function composeBorderedCells(view: View, files: ReadonlyMap<string, FileInfo>, rasterize: Rasterize, seed?: number): ComposedCell[] {
  const cache = new Map<string, Rgba | undefined>()
  const raster = (file: string): Rgba | undefined => {
    if (!cache.has(file)) {
      const bitmap = view.bitmapFor(file)
      cache.set(file, bitmap === undefined ? undefined : rasterize(bitmap, files.get(file)?.scale ?? 1))
    }
    return cache.get(file)
  }
  const tileAt = (code: number, x: number, y: number): Rgba | undefined => {
    const key = TERRAIN_DRAFT_KEYS[code]
    if (key === undefined) return undefined
    const result = view.resolve(key, { x, y })
    return result.kind === 'image' ? raster(result.file) : undefined
  }
  const available = (maskKey: string): string[] => (view.snapshot.details.get(maskKey)?.values ?? []).filter((v) => view.snapshot.entries.has(slotKey(maskKey, v)))
  const masks: MaskAvailability = { variants: available }
  const maskOf = (maskKey: string, detail: string): Rgba | undefined => {
    const entry = view.snapshot.entries.get(slotKey(maskKey, detail))
    return entry === undefined ? undefined : raster(entry.file)
  }
  const codeAt = (x: number, y: number): number | undefined => (x >= 0 && y >= 0 && x < MAP_COLUMNS && y < MAP_ROWS ? terrainAt(x, y) : undefined)
  const out: ComposedCell[] = []
  if (Object.values(MASK_KEYS).every((key) => available(key).length === 0)) return out
  for (let y = 0; y < MAP_ROWS; y++) {
    for (let x = 0; x < MAP_COLUMNS; x++) {
      const overlays = borderOverlays(codeAt, x, y, masks, seed)
      if (overlays.length === 0) continue
      const base = tileAt(codeAt(x, y) as number, x, y)
      if (base === undefined) continue
      const pixels = composeCell(base, overlays, (neighbour) => tileAt(neighbour, x, y), maskOf)
      out.push({ x, y, overlays: overlays.length, pixels })
    }
  }
  return out
}

export type BorderCtx = Pick<CanvasRenderingContext2D, 'putImageData' | 'fillRect' | 'fillStyle'>

const toImage = (pixels: Rgba): ImageData => new ImageData(pixels as Uint8ClampedArray<ArrayBuffer>, TILE_PIXELS, TILE_PIXELS)

/** Put composed cells on the map canvas (over what `drawDraftMap` drew) and re-mark adopted reference cells. */
export function drawComposedCells(ctx: BorderCtx, view: View, files: ReadonlyMap<string, FileInfo>, cells: readonly ComposedCell[], makeImage: (pixels: Rgba) => ImageData = toImage): void {
  for (const cell of cells) {
    ctx.putImageData(makeImage(cell.pixels), cell.x * CELL_SIZE, cell.y * CELL_SIZE)
    const key = TERRAIN_DRAFT_KEYS[terrainAt(cell.x, cell.y)]
    const result = key === undefined ? null : view.resolve(key, { x: cell.x, y: cell.y })
    if (result?.kind === 'image' && files.get(result.file)?.adopted) {
      ctx.fillStyle = ADOPTED_MARK // the mark of a reference to adopted art stays visible under a fringe
      ctx.fillRect(cell.x * CELL_SIZE + 1, cell.y * CELL_SIZE + 1, 3, 3)
    }
  }
}
