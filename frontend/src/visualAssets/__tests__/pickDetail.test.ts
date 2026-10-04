import { afterEach, describe, expect, it, vi } from 'vitest'
import { DETAIL_SEED, PICK_CONTRACT_VERSION, fnv1a32, pickDetail } from '../pickDetail'

const KEY = 'terrain.forest'
const THREE = ['plain', 'bush', 'tree'] as const

afterEach(() => vi.restoreAllMocks())

// Computed ONCE, in Python, from the documented hash (see the ticket's test plan), not by running this module:
//   h = 0x811C9DC5; for b in data: h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF   then   index = h % n   over f"{key}|{x}|{y}|{seed}".encode()
const GOLDEN: readonly [string, number, number, number, number, number, number][] = [
  // key, x, y, seed, n, hash, index
  [KEY, 0, 0, 1, 3, 2553659498, 2],
  [KEY, 1, 0, 1, 3, 1607584925, 2],
  [KEY, 0, 1, 1, 3, 733085261, 2],
  [KEY, 5, 7, 1, 3, 1330371028, 1],
  [KEY, -3, -9, 1, 3, 1245209784, 0],
  [KEY, 100000, 2000000, 1, 3, 1806053651, 2],
  [KEY, 7, 7, 1, 1, 2295137410, 0],
  [KEY, 7, 7, 1, 2, 2295137410, 0],
  [KEY, 7, 7, 2, 3, 2278359791, 2],
  ['ui.other', 7, 7, 1, 3, 4127443676, 2],
]

describe('pickDetail, pick contract version 1', () => {
  it('documents its version and uses a fixed seed', () => {
    expect([PICK_CONTRACT_VERSION, DETAIL_SEED]).toEqual([1, 1])
  })

  it('is 32-bit FNV-1a: the published test vectors', () => {
    expect([fnv1a32(''), fnv1a32('a'), fnv1a32('foobar')]).toEqual([0x811c9dc5, 0xe40c292c, 0xbf9cf968])
    expect(fnv1a32('\u00e9')).toBe(0x1e9de8c1) // hashed as UTF-8 bytes (c3 a9), not UTF-16 units (Python: 'é'.encode())
  })

  it.each(GOLDEN)('golden vector (%s, %i, %i, seed %i, n %i) hashes to %i and picks index %i', (key, x, y, seed, n, hash, index) => {
    expect(fnv1a32(`${key}|${x}|${y}|${seed}`)).toBe(hash)
    const values = Array.from({ length: n }, (_, i) => `v${i}`)
    expect(pickDetail(key, x, y, seed, values)).toBe(`v${index}`)
  })

  it('picks over the declared list in its declared order', () => {
    expect(pickDetail(KEY, 0, 0, DETAIL_SEED, THREE)).toBe('tree')
    expect(pickDetail(KEY, 5, 7, DETAIL_SEED, THREE)).toBe('bush')
    expect(pickDetail(KEY, -3, -9, DETAIL_SEED, THREE)).toBe('plain')
    expect(pickDetail(KEY, 5, 7, DETAIL_SEED, ['tree', 'bush', 'plain'])).toBe('bush') // index 1 of a reordered declaration
    expect(pickDetail(KEY, 0, 0, DETAIL_SEED, ['tree', 'bush', 'plain'])).toBe('plain') // a changed declaration reshuffles
  })

  it('is stable across repeated calls and across a fresh module load', async () => {
    const first = Array.from({ length: 50 }, (_, i) => pickDetail(KEY, i, 49 - i, DETAIL_SEED, THREE))
    expect(Array.from({ length: 50 }, (_, i) => pickDetail(KEY, i, 49 - i, DETAIL_SEED, THREE))).toEqual(first)
    vi.resetModules()
    const fresh = await import('../pickDetail')
    expect(Array.from({ length: 50 }, (_, i) => fresh.pickDetail(KEY, i, 49 - i, fresh.DETAIL_SEED, THREE))).toEqual(first)
  })

  it('does not read the clock or a random source', () => {
    const random = vi.spyOn(Math, 'random').mockImplementation(() => { throw new Error('Math.random was called') })
    const now = vi.spyOn(Date, 'now').mockImplementation(() => { throw new Error('Date.now was called') })
    expect(() => pickDetail(KEY, 3, 4, DETAIL_SEED, THREE)).not.toThrow()
    expect([random, now].map((s) => s.mock.calls.length)).toEqual([0, 0])
  })

  it('depends on every part of the cell: x, y, key and seed each change some picks', () => {
    const grid = (f: (x: number, y: number) => string) => Array.from({ length: 256 }, (_, i) => f(i % 16, Math.floor(i / 16))).join()
    const base = grid((x, y) => pickDetail(KEY, x, y, DETAIL_SEED, THREE))
    expect(grid((_x, y) => pickDetail(KEY, 0, y, DETAIL_SEED, THREE))).not.toBe(base) // x matters
    expect(grid((x) => pickDetail(KEY, x, 0, DETAIL_SEED, THREE))).not.toBe(base) // y matters
    expect(grid((x, y) => pickDetail('terrain.other', x, y, DETAIL_SEED, THREE))).not.toBe(base)
    expect(grid((x, y) => pickDetail(KEY, x, y, DETAIL_SEED + 1, THREE))).not.toBe(base)
  })

  it('handles a single value, negative and large coordinates', () => {
    expect(pickDetail(KEY, -1, -1, DETAIL_SEED, ['only'])).toBe('only')
    expect(pickDetail(KEY, Number.MAX_SAFE_INTEGER, -Number.MAX_SAFE_INTEGER, DETAIL_SEED, THREE)).toMatch(/^(plain|bush|tree)$/)
    expect(fnv1a32(`${KEY}|-3|-9|1`)).not.toBe(fnv1a32(`${KEY}|3|9|1`)) // the sign is part of the hashed string
    expect(pickDetail(KEY, -3, -9, DETAIL_SEED, THREE)).toBe('plain') // index 0, from the golden vector
  })

  it('refuses what is not a pick: no values, a fractional or non-finite coordinate', () => {
    expect(() => pickDetail(KEY, 0, 0, DETAIL_SEED, [])).toThrow(RangeError)
    for (const bad of [0.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      expect(() => pickDetail(KEY, bad, 0, DETAIL_SEED, THREE)).toThrow(RangeError)
      expect(() => pickDetail(KEY, 0, bad, DETAIL_SEED, THREE)).toThrow(RangeError)
      expect(() => pickDetail(KEY, 0, 0, bad, THREE)).toThrow(RangeError)
    }
  })

  it('spreads a 64 x 64 grid of [plain, bush, tree] near-uniformly (the same counts the Python mirror gives)', () => {
    const counts: Record<string, number> = { plain: 0, bush: 0, tree: 0 }
    for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) counts[pickDetail(KEY, x, y, DETAIL_SEED, THREE)]++
    expect(counts).toEqual({ plain: 1354, bush: 1397, tree: 1345 }) // 33.1 %, 34.1 %, 32.8 % of 4096
  })
})
