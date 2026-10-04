// Detail pick, contract version 1. A key that declares a detail axis (runtime manifest `details`) shows ONE of its declared values per cell;
// which one is a pure function of the key, the cell and a fixed seed, so the same map always looks the same: no `Math.random`, no clock, no
// state, nothing from the simulation. Look only.
//
// The hash is 32-bit FNV-1a (offset basis 0x811c9dc5, prime 0x01000193) over the UTF-8 bytes of `${key}|${x}|${y}|${seed}` with x, y and seed as
// base-10 integers (a negative one keeps its `-`), and the index is `hash mod values.length`, over the DECLARED values in their declared
// order (so adding art for a declared value never reshuffles the map; only changing the declaration does). Changing any part of this
// (the hash, the string, the order, the seed) changes every map and is a contract change: bump PICK_CONTRACT_VERSION and record it in
// docs/assets/store_contract.md. Golden vectors in __tests__/pickDetail.test.ts were computed independently in Python.

export const PICK_CONTRACT_VERSION = 1
/** One seed for every key of a release; per-world seeds would be a later, separate decision. */
export const DETAIL_SEED = 1

const OFFSET_BASIS = 0x811c9dc5
const PRIME = 0x01000193
const encoder = new TextEncoder()

export function fnv1a32(text: string): number {
  let hash = OFFSET_BASIS
  for (const byte of encoder.encode(text)) {
    hash = Math.imul(hash ^ byte, PRIME) >>> 0
  }
  return hash
}

function integer(value: number, what: string): number {
  if (!Number.isSafeInteger(value)) throw new RangeError(`${what} must be a safe integer`)
  return value
}

/** The declared value this cell shows. `values` is the key's declared list (at least one). */
export function pickDetail(visualKey: string, x: number, y: number, seed: number, values: readonly string[]): string {
  if (values.length === 0) throw new RangeError('a detail axis has at least one value')
  const hash = fnv1a32(`${visualKey}|${integer(x, 'x')}|${integer(y, 'y')}|${integer(seed, 'seed')}`)
  return values[hash % values.length]
}
