// Strict parser for the runtime manifest the store exports (docs/assets/store_contract.md, "The runtime manifest").
// Isolated rehearsal code (AM-M5): nothing outside src/visualAssets/ imports it. It mirrors the Python contract
// (visual_assets/store/contracts/runtime.py) and rejects everything that contract rejects.

export const MAX_DIM = 128
export const MAX_VISUAL_KEYS = 1024
export const MAX_DETAIL_VALUES = 16 // values on one key's detail axis
export const MAX_DETAIL_KEYS = 64 // keys declaring a detail axis in one manifest

export type ManifestErrorCode =
  | 'invalid_json'
  | 'duplicate_key'
  | 'unknown_field'
  | 'missing_field'
  | 'wrong_record_type'
  | 'unsupported_version'
  | 'invalid_value'
  | 'file_not_derived'
  | 'duplicate_visual_key'
  | 'unsorted_entries'
  | 'too_many_entries'
  | 'unsorted_details'
  | 'too_many_details'
  | 'detail_mismatch'

export class ManifestError extends Error {
  readonly code: ManifestErrorCode
  constructor(code: ManifestErrorCode, message: string) {
    super(`${code}: ${message}`)
    this.name = 'ManifestError'
    this.code = code
  }
}

export interface RuntimeEntry {
  readonly visualKey: string
  readonly family: string
  readonly pixelHash: string
  readonly file: string
  readonly width: number
  readonly height: number
  // The slot's detail value; present exactly for a key listed in the snapshot's `details`.
  readonly detail: string | null
}

// One key's DECLARED detail axis (copied from the registry): the client picks over these values, so adding art for a declared value never reshuffles the map.
export interface RuntimeDetail {
  readonly visualKey: string
  readonly values: readonly string[]
  readonly default: string
}

export interface RuntimeSnapshot {
  readonly catalogId: string
  readonly releaseId: string
  // The generation of everything shown from this snapshot: the hash of the exact candidate manifest it was exported from.
  readonly generation: string
  readonly registryHash: string
  // Keyed by visual key for a key without a detail axis, and by `${visualKey}\u0000${detail}` per slot otherwise; use `slotKey`.
  readonly entries: ReadonlyMap<string, RuntimeEntry>
  readonly details: ReadonlyMap<string, RuntimeDetail>
}

export function slotKey(visualKey: string, detail: string | null): string {
  return detail === null ? visualKey : `${visualKey}\u0000${detail}`
}

// ---- JSON that refuses duplicate object keys (JSON.parse silently keeps the last one) --------------------------

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

class Reader {
  private pos = 0
  private readonly text: string
  constructor(text: string) {
    this.text = text
  }

  parse(): Json {
    const value = this.value()
    this.space()
    if (this.pos !== this.text.length) this.fail('trailing characters')
    return value
  }

  private fail(why: string): never {
    throw new ManifestError('invalid_json', `${why} at ${this.pos}`)
  }

  private space() {
    while (this.pos < this.text.length && ' \t\n\r'.includes(this.text[this.pos])) this.pos++
  }

  private value(): Json {
    this.space()
    const ch = this.text[this.pos]
    if (ch === '{') return this.object()
    if (ch === '[') return this.array()
    if (ch === '"') return this.string()
    for (const [word, value] of [['true', true], ['false', false], ['null', null]] as const) {
      if (this.text.startsWith(word, this.pos)) {
        this.pos += word.length
        return value
      }
    }
    const match = /^-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?/.exec(this.text.slice(this.pos))
    if (!match) this.fail('unexpected character')
    this.pos += match[0].length
    return Number(match[0])
  }

  private string(): string {
    const start = this.pos
    this.pos++ // opening quote
    while (this.pos < this.text.length) {
      const ch = this.text[this.pos]
      if (ch === '\\') this.pos += 2
      else if (ch === '"') {
        this.pos++
        try {
          return JSON.parse(this.text.slice(start, this.pos)) as string
        } catch {
          this.fail('bad string')
        }
      } else this.pos++
    }
    return this.fail('unterminated string')
  }

  private array(): Json[] {
    const out: Json[] = []
    this.pos++
    this.space()
    if (this.text[this.pos] === ']') {
      this.pos++
      return out
    }
    for (;;) {
      out.push(this.value())
      this.space()
      const ch = this.text[this.pos++]
      if (ch === ']') return out
      if (ch !== ',') this.fail('expected , or ]')
    }
  }

  private object(): { [key: string]: Json } {
    const out: { [key: string]: Json } = Object.create(null)
    this.pos++
    this.space()
    if (this.text[this.pos] === '}') {
      this.pos++
      return out
    }
    for (;;) {
      this.space()
      if (this.text[this.pos] !== '"') this.fail('expected a key')
      const key = this.string()
      if (key in out) throw new ManifestError('duplicate_key', `duplicate object key ${JSON.stringify(key)}`)
      this.space()
      if (this.text[this.pos++] !== ':') this.fail('expected :')
      out[key] = this.value()
      this.space()
      const ch = this.text[this.pos++]
      if (ch === '}') return out
      if (ch !== ',') this.fail('expected , or }')
    }
  }
}

/** Parse JSON text, refusing duplicate object keys. Throws a `ManifestError`. */
export function readJson(manifestText: string): Json {
  return new Reader(manifestText).parse()
}

// ---- validation ----------------------------------------------------------------------------------------------------

const TOP_FIELDS = [
  'record_type', 'schema_version', 'catalog_id', 'release_id', 'candidate_manifest_hash', 'registry_hash',
  'fallback_contract_version', 'entries',
] as const
const OPTIONAL_TOP_FIELDS = ['details'] as const
const ENTRY_FIELDS = ['visual_key', 'family', 'pixel_hash', 'file', 'width', 'height'] as const
const OPTIONAL_ENTRY_FIELDS = ['detail'] as const
const DETAIL_FIELDS = ['visual_key', 'values', 'default'] as const

export const ID = /^[a-z0-9][a-z0-9_-]{0,63}$/
const RELEASE = /^rc-(?!0000$)[0-9]{4}$/
export const FILE_HASH = /^sha256:[0-9a-f]{64}$/
export const PIXEL_HASH = /^pixels-v1:[0-9a-f]{64}$/
export const VISUAL_KEY = /^[a-z][a-z0-9_]{0,31}(\.[a-z][a-z0-9_]{0,31}){1,3}$/
export const FAMILY = /^[a-z][a-z0-9_]{0,31}$/
export const FILE = /^[0-9a-f]{64}\.png$/
export const AXIS_VALUE = /^[a-z0-9][a-z0-9_]{0,31}$/

export function object(value: Json, what: string, fields: readonly string[], optional: readonly string[] = []): { [key: string]: Json } {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new ManifestError('invalid_value', `${what} must be an object`)
  }
  for (const key of Object.keys(value)) {
    if (!fields.includes(key) && !optional.includes(key)) throw new ManifestError('unknown_field', `${what} has the unknown field ${JSON.stringify(key)}`)
  }
  for (const key of fields) {
    if (!(key in value)) throw new ManifestError('missing_field', `${what} lacks ${key}`)
  }
  return value
}

export function text(value: Json, what: string, pattern: RegExp): string {
  if (typeof value !== 'string' || !pattern.test(value)) throw new ManifestError('invalid_value', `${what} is not valid`)
  return value
}

function dimension(value: Json, what: string): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 1 || value > MAX_DIM) {
    throw new ManifestError('invalid_value', `${what} must be an integer 1..${MAX_DIM}`)
  }
  return value
}

function parseEntry(raw: Json, index: number): RuntimeEntry {
  const o = object(raw, `entries[${index}]`, ENTRY_FIELDS, OPTIONAL_ENTRY_FIELDS)
  const pixelHash = text(o.pixel_hash, `entries[${index}].pixel_hash`, PIXEL_HASH)
  const file = text(o.file, `entries[${index}].file`, FILE)
  if (file !== `${pixelHash.slice('pixels-v1:'.length)}.png`) {
    throw new ManifestError('file_not_derived', `entries[${index}].file is not derived from its pixel hash`)
  }
  return Object.freeze({
    visualKey: text(o.visual_key, `entries[${index}].visual_key`, VISUAL_KEY),
    family: text(o.family, `entries[${index}].family`, FAMILY),
    pixelHash,
    file,
    width: dimension(o.width, `entries[${index}].width`),
    height: dimension(o.height, `entries[${index}].height`),
    detail: 'detail' in o && o.detail !== null ? text(o.detail, `entries[${index}].detail`, AXIS_VALUE) : null, // an explicit null is the same as absent, as in the Python model
  })
}

export function parseDetail(raw: Json, index: number): RuntimeDetail {
  const o = object(raw, `details[${index}]`, DETAIL_FIELDS)
  if (!Array.isArray(o.values) || o.values.length < 1 || o.values.length > MAX_DETAIL_VALUES) {
    throw new ManifestError('invalid_value', `details[${index}].values must be a list of 1..${MAX_DETAIL_VALUES} values`)
  }
  const values = o.values.map((v, i) => text(v, `details[${index}].values[${i}]`, AXIS_VALUE))
  if (new Set(values).size !== values.length) throw new ManifestError('invalid_value', `details[${index}].values must be unique`)
  const def = text(o.default, `details[${index}].default`, AXIS_VALUE)
  if (!values.includes(def)) throw new ManifestError('invalid_value', `details[${index}].default must be one of its values`)
  return Object.freeze({ visualKey: text(o.visual_key, `details[${index}].visual_key`, VISUAL_KEY), values: Object.freeze(values), default: def })
}

// A ReadonlyMap is not frozen by Object.freeze (its entries stay mutable through `set`), so expose a map whose mutators throw.
export function readOnly<V>(map: Map<string, V>): ReadonlyMap<string, V> {
  return Object.freeze({
    get: (key: string) => map.get(key),
    has: (key: string) => map.has(key),
    get size() { return map.size },
    keys: () => map.keys(),
    values: () => map.values(),
    entries: () => map.entries(),
    forEach: (fn: (value: V, key: string) => void) => map.forEach((value, key) => fn(value, key)),
    [Symbol.iterator]: () => map[Symbol.iterator](),
  }) as ReadonlyMap<string, V>
}

/** Parse the exported `runtime_manifest.json` text into a deeply frozen snapshot, or throw a `ManifestError`. */
export function parseManifest(manifestText: string): RuntimeSnapshot {
  const o = object(new Reader(manifestText).parse(), 'the manifest', TOP_FIELDS, OPTIONAL_TOP_FIELDS)
  if (o.record_type !== 'runtime_manifest') throw new ManifestError('wrong_record_type', 'expected record_type "runtime_manifest"')
  if (o.schema_version !== 1) throw new ManifestError('unsupported_version', `schema_version ${JSON.stringify(o.schema_version)} is not supported`)
  if (o.fallback_contract_version !== 1) {
    throw new ManifestError('unsupported_version', `fallback_contract_version ${JSON.stringify(o.fallback_contract_version)} is not supported`)
  }
  const catalogId = text(o.catalog_id, 'catalog_id', ID)
  const releaseId = text(o.release_id, 'release_id', RELEASE)
  const generation = text(o.candidate_manifest_hash, 'candidate_manifest_hash', FILE_HASH)
  const registryHash = text(o.registry_hash, 'registry_hash', FILE_HASH)
  if (!Array.isArray(o.entries)) throw new ManifestError('invalid_value', 'entries must be a list')
  if (o.entries.length > MAX_VISUAL_KEYS) throw new ManifestError('too_many_entries', `more than ${MAX_VISUAL_KEYS} entries`)
  const entries = o.entries.map(parseEntry)
  const rawDetails = 'details' in o ? o.details : []
  if (!Array.isArray(rawDetails)) throw new ManifestError('invalid_value', 'details must be a list')
  if (rawDetails.length > MAX_DETAIL_KEYS) throw new ManifestError('too_many_details', `more than ${MAX_DETAIL_KEYS} details`)
  const detailList = rawDetails.map(parseDetail)
  const detailKeys = detailList.map((d) => d.visualKey)
  if (new Set(detailKeys).size !== detailKeys.length || detailKeys.some((key, i) => i > 0 && detailKeys[i - 1] > key)) {
    throw new ManifestError('unsorted_details', 'details must be unique and sorted by visual key')
  }
  const declared = new Map(detailList.map((d) => [d.visualKey, d] as const))
  const slots = entries.map((e) => [e.visualKey, e.detail ?? ''] as const)
  if (new Set(slots.map(([k, d]) => `${k}\u0000${d}`)).size !== slots.length) {
    throw new ManifestError('duplicate_visual_key', 'entries must have unique (visual key, detail) slots')
  }
  if (slots.some(([k, d], i) => i > 0 && (slots[i - 1][0] > k || (slots[i - 1][0] === k && slots[i - 1][1] > d)))) {
    throw new ManifestError('unsorted_entries', 'entries must be sorted by visual key, then detail')
  }
  for (const e of entries) {
    const axis = declared.get(e.visualKey)
    if ((axis !== undefined) !== (e.detail !== null)) {
      throw new ManifestError('detail_mismatch', `entry ${e.visualKey} has a detail value exactly when its key is listed in details`)
    }
    if (axis !== undefined && !axis.values.includes(e.detail as string)) {
      throw new ManifestError('detail_mismatch', `entry ${e.visualKey} detail ${JSON.stringify(e.detail)} is not a declared value`)
    }
  }
  return Object.freeze({
    catalogId, releaseId, generation, registryHash,
    entries: readOnly(new Map(entries.map((e) => [slotKey(e.visualKey, e.detail), e] as const))),
    details: readOnly(declared),
  })
}
