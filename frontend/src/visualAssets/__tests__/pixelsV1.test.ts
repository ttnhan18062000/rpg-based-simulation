// @vitest-environment node
// The TypeScript `pixels-v1` hash equals the store's Python hash on every known vector (written by `tests/visual_assets/test_pixelhash_vectors.py`).
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { pixelsV1Hash } from '../pixelsV1'

interface Vector { name: string; width: number; height: number; rgba_base64: string; pixel_hash: string }
const vectors: Vector[] = JSON.parse(readFileSync(path.join(process.cwd(), 'src/visualAssets/__fixtures__/pixelhash/vectors.json'), 'utf8')).vectors
const rgbaOf = (v: Vector) => Uint8Array.from(Buffer.from(v.rgba_base64, 'base64'))

describe('the TypeScript pixels-v1 hash equals the Python one', () => {
  it('covers the committed artifacts, a non-square image, alpha and transparent colour', () => {
    const names = vectors.map((v) => v.name)
    expect(names.filter((n) => n.startsWith('artifact:'))).toHaveLength(3)
    expect(names).toEqual(expect.arrayContaining(['non-square 5x3', 'alpha mix 4x2', 'transparent colour is not part of the hash 2x2']))
    expect(vectors.some((v) => v.width !== v.height)).toBe(true)
  })

  for (const v of vectors) {
    it(`matches on ${v.name}`, async () => {
      expect(await pixelsV1Hash(v.width, v.height, rgbaOf(v))).toBe(v.pixel_hash)
    })
  }

  it('does not depend on the colour of a fully transparent pixel, and does depend on every other byte', async () => {
    const base = Uint8Array.from([10, 20, 30, 255, 7, 7, 7, 0])
    const sameVisible = Uint8Array.from([10, 20, 30, 255, 200, 100, 50, 0])
    expect(await pixelsV1Hash(2, 1, base)).toBe(await pixelsV1Hash(2, 1, sameVisible))
    for (const index of [0, 1, 2, 3, 7]) {
      const changed = Uint8Array.from(base)
      changed[index] ^= 1
      expect(await pixelsV1Hash(2, 1, changed), `byte ${index}`).not.toBe(await pixelsV1Hash(2, 1, base))
    }
    expect(await pixelsV1Hash(2, 1, base)).not.toBe(await pixelsV1Hash(1, 2, base)) // the shape is part of the hash
  })

  it('refuses a buffer of the wrong length', async () => {
    await expect(pixelsV1Hash(2, 2, new Uint8Array(15))).rejects.toThrow()
  })
})
