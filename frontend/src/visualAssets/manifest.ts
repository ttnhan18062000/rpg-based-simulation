// Strict parser for the runtime manifest the store exports (docs/assets/store_contract.md, "The runtime manifest").
// Isolated rehearsal code (AM-M5): nothing outside src/visualAssets/ imports it. It mirrors the Python contract
// (visual_assets/store/contracts/runtime.py) and rejects everything that contract rejects.

export const MAX_DIM = 128
export const MAX_VISUAL_KEYS = 1024

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
}

export interface RuntimeSnapshot {
  readonly catalogId: string
  readonly releaseId: string
  // The generation of everything shown from this snapshot: the hash of the exact candidate manifest it was exported from.
  readonly generation: string
  readonly registryHash: string
  readonly entries: ReadonlyMap<string, RuntimeEntry>
}

// ---- JSON that refuses duplicate object keys (JSON.parse silently keeps the last one) --------------------------

type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

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

// ---- validation ----------------------------------------------------------------------------------------------------

const TOP_FIELDS = [
  'record_type', 'schema_version', 'catalog_id', 'release_id', 'candidate_manifest_hash', 'registry_hash',
  'fallback_contract_version', 'entries',
] as const
const ENTRY_FIELDS = ['visual_key', 'family', 'pixel_hash', 'file', 'width', 'height'] as const

const ID = /^[a-z0-9][a-z0-9_-]{0,63}$/
const RELEASE = /^rc-(?!0000$)[0-9]{4}$/
const FILE_HASH = /^sha256:[0-9a-f]{64}$/
const PIXEL_HASH = /^pixels-v1:[0-9a-f]{64}$/
const VISUAL_KEY = /^[a-z][a-z0-9_]{0,31}(\.[a-z][a-z0-9_]{0,31}){1,3}$/
const FAMILY = /^[a-z][a-z0-9_]{0,31}$/
const FILE = /^[0-9a-f]{64}\.png$/

function object(value: Json, what: string, fields: readonly string[]): { [key: string]: Json } {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new ManifestError('invalid_value', `${what} must be an object`)
  }
  for (const key of Object.keys(value)) {
    if (!fields.includes(key)) throw new ManifestError('unknown_field', `${what} has the unknown field ${JSON.stringify(key)}`)
  }
  for (const key of fields) {
    if (!(key in value)) throw new ManifestError('missing_field', `${what} lacks ${key}`)
  }
  return value
}

function text(value: Json, what: string, pattern: RegExp): string {
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
  const o = object(raw, `entries[${index}]`, ENTRY_FIELDS)
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
  })
}

/** Parse the exported `runtime_manifest.json` text into a deeply frozen snapshot, or throw a `ManifestError`. */
export function parseManifest(manifestText: string): RuntimeSnapshot {
  const o = object(new Reader(manifestText).parse(), 'the manifest', TOP_FIELDS)
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
  const keys = entries.map((e) => e.visualKey)
  if (new Set(keys).size !== keys.length) throw new ManifestError('duplicate_visual_key', 'entries must have unique visual keys')
  if (keys.some((key, i) => i > 0 && keys[i - 1] > key)) throw new ManifestError('unsorted_entries', 'entries must be sorted by visual key')
  const map = new Map(entries.map((e) => [e.visualKey, e] as const))
  // A ReadonlyMap is not frozen by Object.freeze (its entries stay mutable through `set`), so expose a map whose mutators throw.
  const frozen = Object.freeze({
    get: (key: string) => map.get(key),
    has: (key: string) => map.has(key),
    get size() { return map.size },
    keys: () => map.keys(),
    values: () => map.values(),
    entries: () => map.entries(),
    forEach: (fn: (value: RuntimeEntry, key: string) => void) => map.forEach((value, key) => fn(value, key)),
    [Symbol.iterator]: () => map[Symbol.iterator](),
  }) as ReadonlyMap<string, RuntimeEntry>
  return Object.freeze({ catalogId, releaseId, generation, registryHash, entries: frozen })
}
