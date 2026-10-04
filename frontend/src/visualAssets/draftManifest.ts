// Strict parser for the draft preview manifest `python -m visual_assets.store draft export` writes (docs/assets/store_contract.md, "Draft sets").
// It mirrors visual_assets/store/contracts/draft.py (`DraftPreviewManifest`) and rejects everything that contract rejects. It is a record type of its own: `parseManifest`
// (the runtime manifest) refuses it and this parser refuses a runtime manifest, so nothing that loads one can load the other. Isolated preview code: nothing outside
// src/visualAssets/ imports it.
import {
  AXIS_VALUE, FAMILY, FILE, FILE_HASH, ID, ManifestError, PIXEL_HASH, VISUAL_KEY, MAX_DETAIL_KEYS, object, parseDetail, readJson, readOnly, slotKey, text,
  type RuntimeDetail, type RuntimeEntry, type RuntimeSnapshot,
} from './manifest'

export const MAX_DRAFT_SET_ENTRIES = 256
export const MAX_PREVIEW_DIM = 1024
export const MAX_PREVIEW_SCALE = 16

export interface DraftEntry {
  readonly visualKey: string
  readonly family: string
  readonly detail: string | null
  readonly sourceAssetId: string
  readonly draftId: string
  readonly pixelHash: string
  readonly file: string
  // The preview PNG's own size; the tile is width / scale by height / scale logical pixels.
  readonly width: number
  readonly height: number
  readonly scale: number
}

export interface DraftSnapshot {
  readonly setId: string
  // The file hash of the exact draft_set.json bytes: the value `adopt-set` prints in its confirmation.
  readonly draftSetHash: string
  readonly registryHash: string
  readonly entries: readonly DraftEntry[]
  readonly details: ReadonlyMap<string, RuntimeDetail>
}

const TOP_FIELDS = ['record_type', 'schema_version', 'set_id', 'draft_set_hash', 'registry_hash', 'entries'] as const
const OPTIONAL_TOP_FIELDS = ['details'] as const
const ENTRY_FIELDS = [
  'visual_key', 'family', 'source_asset_id', 'draft_id', 'pixel_hash', 'file', 'width', 'height', 'scale',
] as const
const OPTIONAL_ENTRY_FIELDS = ['detail'] as const
const DRAFT_ID = /^in-[0-9a-f]{16}$/

function previewDim(value: unknown, what: string): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 1 || value > MAX_PREVIEW_DIM) {
    throw new ManifestError('invalid_value', `${what} must be an integer 1..${MAX_PREVIEW_DIM}`)
  }
  return value
}

function parseEntry(raw: Parameters<typeof object>[0], index: number): DraftEntry {
  const o = object(raw, `entries[${index}]`, ENTRY_FIELDS, OPTIONAL_ENTRY_FIELDS)
  const pixelHash = text(o.pixel_hash, `entries[${index}].pixel_hash`, PIXEL_HASH)
  const file = text(o.file, `entries[${index}].file`, FILE)
  if (file !== `${pixelHash.slice('pixels-v1:'.length)}.png`) {
    throw new ManifestError('file_not_derived', `entries[${index}].file is not derived from its pixel hash`)
  }
  const width = previewDim(o.width, `entries[${index}].width`)
  const height = previewDim(o.height, `entries[${index}].height`)
  const scale = o.scale
  if (typeof scale !== 'number' || !Number.isInteger(scale) || scale < 1 || scale > MAX_PREVIEW_SCALE) {
    throw new ManifestError('invalid_value', `entries[${index}].scale must be an integer 1..${MAX_PREVIEW_SCALE}`)
  }
  if (width % scale !== 0 || height % scale !== 0) {
    throw new ManifestError('invalid_value', `entries[${index}] size is not a whole multiple of its scale`)
  }
  return Object.freeze({
    visualKey: text(o.visual_key, `entries[${index}].visual_key`, VISUAL_KEY),
    family: text(o.family, `entries[${index}].family`, FAMILY),
    detail: 'detail' in o && o.detail !== null ? text(o.detail, `entries[${index}].detail`, AXIS_VALUE) : null,
    sourceAssetId: text(o.source_asset_id, `entries[${index}].source_asset_id`, ID),
    draftId: text(o.draft_id, `entries[${index}].draft_id`, DRAFT_ID),
    pixelHash, file, width, height, scale,
  })
}

/** Parse the exported `draft_preview_manifest.json` text into a frozen snapshot, or throw a `ManifestError`. A runtime manifest is refused (`wrong_record_type`). */
export function parseDraftPreview(manifestText: string): DraftSnapshot {
  const o = object(readJson(manifestText), 'the draft preview manifest', TOP_FIELDS, OPTIONAL_TOP_FIELDS)
  if (o.record_type !== 'draft_preview_manifest') throw new ManifestError('wrong_record_type', 'expected record_type "draft_preview_manifest"')
  if (o.schema_version !== 1) throw new ManifestError('unsupported_version', `schema_version ${JSON.stringify(o.schema_version)} is not supported`)
  const setId = text(o.set_id, 'set_id', ID)
  const draftSetHash = text(o.draft_set_hash, 'draft_set_hash', FILE_HASH)
  const registryHash = text(o.registry_hash, 'registry_hash', FILE_HASH)
  if (!Array.isArray(o.entries)) throw new ManifestError('invalid_value', 'entries must be a list')
  if (o.entries.length > MAX_DRAFT_SET_ENTRIES) throw new ManifestError('too_many_entries', `more than ${MAX_DRAFT_SET_ENTRIES} entries`)
  const entries = o.entries.map(parseEntry)
  const rawDetails = 'details' in o ? o.details : []
  if (!Array.isArray(rawDetails)) throw new ManifestError('invalid_value', 'details must be a list')
  if (rawDetails.length > MAX_DETAIL_KEYS) throw new ManifestError('too_many_details', `more than ${MAX_DETAIL_KEYS} details`)
  const detailList = rawDetails.map(parseDetail)
  const keys = detailList.map((d) => d.visualKey)
  if (new Set(keys).size !== keys.length || keys.some((key, i) => i > 0 && keys[i - 1] > key)) {
    throw new ManifestError('unsorted_details', 'details must be unique and sorted by visual key')
  }
  const declared = new Map(detailList.map((d) => [d.visualKey, d] as const))
  const slots = entries.map((e) => [e.visualKey, e.detail ?? ''] as const)
  if (new Set(slots.map(([k, d]) => slotKey(k, d))).size !== slots.length) throw new ManifestError('duplicate_visual_key', 'entries must have unique slots')
  if (slots.some(([k, d], i) => i > 0 && (slots[i - 1][0] > k || (slots[i - 1][0] === k && slots[i - 1][1] > d)))) {
    throw new ManifestError('unsorted_entries', 'entries must be sorted by visual key, then detail')
  }
  const effective = new Set<string>()
  for (const e of entries) {
    const axis = declared.get(e.visualKey)
    if (e.detail !== null && (axis === undefined || !axis.values.includes(e.detail))) {
      throw new ManifestError('detail_mismatch', `entry ${e.visualKey} names a detail value its key does not declare`)
    }
    // No detail value on a key with a declared axis means its declared default: two entries may not fill one slot.
    const slot = slotKey(e.visualKey, e.detail ?? axis?.default ?? null)
    if (effective.has(slot)) throw new ManifestError('duplicate_visual_key', `two entries fill the slot of ${e.visualKey}`)
    effective.add(slot)
  }
  return Object.freeze({ setId, draftSetHash, registryHash, entries: Object.freeze(entries), details: readOnly(declared) })
}

/**
 * The draft snapshot as the loader and resolver understand a runtime snapshot (they stay unchanged): the set id stands in for the catalog, the draft set hash for the
 * generation. Entry sizes are the preview PNG's, which is what the loader checks a decoded image against.
 */
export function asRuntimeSnapshot(draft: DraftSnapshot): RuntimeSnapshot {
  const entries = new Map<string, RuntimeEntry>()
  for (const e of draft.entries) {
    const detail = e.detail ?? draft.details.get(e.visualKey)?.default ?? null // an entry without a value fills its key's declared default slot
    entries.set(slotKey(e.visualKey, detail), Object.freeze({
      visualKey: e.visualKey, family: e.family, pixelHash: e.pixelHash, file: e.file, width: e.width, height: e.height, detail,
    }))
  }
  return Object.freeze({
    catalogId: draft.setId, releaseId: 'draft', generation: draft.draftSetHash, registryHash: draft.registryHash, entries: readOnly(entries), details: draft.details,
  })
}
