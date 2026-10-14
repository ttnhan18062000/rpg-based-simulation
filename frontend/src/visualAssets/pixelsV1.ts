// The store's `pixels-v1` image hash, in TypeScript (`visual_assets/store/pixels.py::pixel_hash_of`). Used only by the local capture spec
// (`frontend/rehearsal-capture/bundle.capture.ts`) to hash what a page really DREW and compare it with the stored artifacts' pixel hashes.
//
// This is a SECOND implementation of the Python hash, so it is proven equal on known vectors (`__fixtures__/pixelhash/vectors.json`, written
// by Python and kept honest by `tests/visual_assets/test_pixelhash_vectors.py`; compared in `__tests__/pixelsV1.test.ts`). A drift would
// make every capture verdict meaningless, which is why the vectors include the committed artifacts, a non-square image and one with alpha.
//
// sha256 over: "pixels-v1\0", width and height as unsigned 32-bit big-endian, then the non-premultiplied RGBA bytes, row by row, with the
// RGB of every fully transparent pixel set to zero (a transparent pixel has no colour).

const MAGIC = new TextEncoder().encode('pixels-v1\u0000')
export const PIXEL_HASH_PREFIX = 'pixels-v1:'

export async function pixelsV1Hash(width: number, height: number, rgba: ArrayLike<number>): Promise<string> {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1) throw new Error('width and height must be positive integers')
  if (rgba.length !== width * height * 4) throw new Error(`expected ${width * height * 4} RGBA bytes, got ${rgba.length}`)
  const bytes = new Uint8Array(MAGIC.length + 8 + rgba.length)
  bytes.set(MAGIC, 0)
  const view = new DataView(bytes.buffer)
  view.setUint32(MAGIC.length, width, false)
  view.setUint32(MAGIC.length + 4, height, false)
  const body = MAGIC.length + 8
  for (let i = 0; i < rgba.length; i += 4) {
    const transparent = rgba[i + 3] === 0
    bytes[body + i] = transparent ? 0 : rgba[i]
    bytes[body + i + 1] = transparent ? 0 : rgba[i + 1]
    bytes[body + i + 2] = transparent ? 0 : rgba[i + 2]
    bytes[body + i + 3] = rgba[i + 3]
  }
  const digest = new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', bytes))
  return PIXEL_HASH_PREFIX + Array.from(digest, (b) => b.toString(16).padStart(2, '0')).join('')
}
