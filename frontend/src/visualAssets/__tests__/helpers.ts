// Test helpers: the fixture as text/objects, a deferred decoder, a recording 2D context and a tiny PNG reader for the fixture's alpha masks.
import { inflateSync } from 'node:zlib'
import { fixtureManifestText } from '../fixtureSource'
import type { Bitmap, Decode } from '../loader'

export type Raw = Record<string, unknown> & { entries: Record<string, unknown>[] }

export function fixtureObject(): Raw {
  return JSON.parse(fixtureManifestText) as Raw
}

export function manifestWith(change: (raw: Raw) => void): string {
  const raw = fixtureObject()
  change(raw)
  return JSON.stringify(raw)
}

/** A decoder whose every completion is released by the test, in any order. */
export function controlledDecode() {
  const pending = new Map<string, { resolve: (b: Bitmap) => void; reject: (e: Error) => void }>()
  const calls: string[] = []
  const decode: Decode = (url) =>
    new Promise<Bitmap>((resolve, reject) => {
      calls.push(url)
      pending.set(url, { resolve, reject })
    })
  return { decode, calls, pending }
}

export function bitmap(width = 16, height = 16): Bitmap & { closed: boolean } {
  const out = { width, height, closed: false, close() { out.closed = true } }
  return out
}

export type Call = [string, ...unknown[]]

export class RecordingContext {
  calls: Call[] = []
  fillStyle: string | CanvasGradient | CanvasPattern = ''
  font = ''
  textAlign: CanvasTextAlign = 'start'
  textBaseline: CanvasTextBaseline = 'alphabetic'
  imageSmoothingEnabled = true
  fillStyles = new Set<string>()
  textColors: string[] = []
  rectColors: string[] = []
  fillRect(...a: number[]) { this.fillStyles.add(String(this.fillStyle)); this.rectColors.push(String(this.fillStyle)); this.calls.push(['fillRect', ...a]) }
  clearRect(...a: number[]) { this.calls.push(['clearRect', ...a]) }
  drawImage(...a: unknown[]) { this.calls.push(['drawImage', ...a]) }
  fillText(...a: unknown[]) { this.textColors.push(String(this.fillStyle)); this.calls.push(['fillText', ...a]) }
  of(name: string) { return this.calls.filter((c) => c[0] === name) }
}

/** Decode an 8-bit RGBA, non-interlaced PNG whose rows all use filter 0 (what the fixture generator writes) and return its alpha mask. */
export function alphaMask(png: Uint8Array): { width: number; height: number; mask: boolean[] } {
  const view = new DataView(png.buffer, png.byteOffset, png.byteLength)
  let pos = 8
  let width = 0
  let height = 0
  const idat: Uint8Array[] = []
  while (pos < png.length) {
    const length = view.getUint32(pos)
    const kind = String.fromCharCode(...png.slice(pos + 4, pos + 8))
    const body = png.slice(pos + 8, pos + 8 + length)
    if (kind === 'IHDR') {
      width = new DataView(body.buffer, body.byteOffset).getUint32(0)
      height = new DataView(body.buffer, body.byteOffset).getUint32(4)
      if (body[8] !== 8 || body[9] !== 6 || body[12] !== 0) throw new Error('not an 8-bit RGBA non-interlaced PNG')
    }
    if (kind === 'IDAT') idat.push(body)
    pos += 12 + length
  }
  const raw = inflateSync(Buffer.concat(idat))
  const mask: boolean[] = []
  for (let y = 0; y < height; y++) {
    const row = y * (width * 4 + 1)
    if (raw[row] !== 0) throw new Error('only filter 0 rows are supported by this test reader')
    for (let x = 0; x < width; x++) mask.push(raw[row + 1 + x * 4 + 3] > 0)
  }
  return { width, height, mask }
}

export function differing(a: readonly boolean[], b: readonly boolean[]): number {
  return a.reduce((n, v, i) => n + (v !== b[i] ? 1 : 0), 0)
}
