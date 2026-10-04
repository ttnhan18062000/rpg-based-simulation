// Pure, read-only resolver: a semantic visual key -> an image result or a typed fallback. It performs no I/O and
// registers nothing: the key set is the manifest's, finite, and an unknown key never causes a fetch.
import { slotKey, type RuntimeSnapshot } from './manifest'
import { DETAIL_SEED, pickDetail } from './pickDetail'

export type FallbackReason = 'unknown_key' | 'missing_image' | 'decode_failed' | 'manifest_invalid' | 'late_result_dropped'
// How loading ended for one file in one view: `late` = the completion arrived after the view was superseded and was dropped.
export type ImageStatus = 'ok' | 'missing' | 'decode_failed' | 'late'

export interface ImageResult {
  readonly kind: 'image'
  readonly visualKey: string
  readonly family: string
  readonly file: string
  readonly url: string
  readonly width: number
  readonly height: number
  readonly generation: string
  // Only for a key that declares a detail axis: `picked` is what `pickDetail` chose for the cell, `detail` the value whose image this is, and
  // `detailFallback` why they differ (the picked value's image was unavailable, so the default's is shown).
  readonly picked?: string
  readonly detail?: string
  readonly detailFallback?: FallbackReason
}

export interface FallbackResult {
  readonly kind: 'fallback'
  readonly visualKey: string
  // null when the family is not known (unknown key, or no valid manifest).
  readonly family: string | null
  readonly reason: FallbackReason
  // Only for a key that declares a detail axis: what was picked for the cell. `reason` is then why the DEFAULT value's image was unavailable too.
  readonly picked?: string
}

export type Resolution = ImageResult | FallbackResult

export interface ResolveContext {
  // The build's URL for a file, or undefined when the build does not contain it.
  readonly urlFor: (file: string) => string | undefined
  // How loading ended for a file in the view being resolved, or undefined while nothing is known (still loading).
  readonly statusOf?: (file: string) => ImageStatus | undefined
}

/** The Live Map cell a detail is picked for. A key without a detail axis ignores it. */
export interface Cell {
  readonly x: number
  readonly y: number
}

const STATUS_REASON = {
  missing: 'missing_image',
  decode_failed: 'decode_failed',
  late: 'late_result_dropped',
} as const

function resolveEntry(snapshot: RuntimeSnapshot, visualKey: string, slot: string, context: ResolveContext): Resolution {
  const entry = snapshot.entries.get(slot)
  if (entry === undefined) return { kind: 'fallback', visualKey, family: null, reason: 'unknown_key' }
  const status = context.statusOf?.(entry.file)
  if (status !== undefined && status !== 'ok') return { kind: 'fallback', visualKey, family: entry.family, reason: STATUS_REASON[status] }
  const url = context.urlFor(entry.file)
  if (url === undefined) return { kind: 'fallback', visualKey, family: entry.family, reason: 'missing_image' }
  return {
    kind: 'image', visualKey, family: entry.family, file: entry.file, url,
    width: entry.width, height: entry.height, generation: snapshot.generation,
  }
}

// A declared value with no art yet has no entry: that is a missing image (the family still comes from any of the key's slots), never an unknown key.
function declared(snapshot: RuntimeSnapshot, visualKey: string, result: Resolution, values: readonly string[]): Resolution {
  if (result.kind === 'image' || result.reason !== 'unknown_key') return result
  const family = values.map((v) => snapshot.entries.get(slotKey(visualKey, v))?.family).find((f) => f !== undefined) ?? null
  return { kind: 'fallback', visualKey, family, reason: 'missing_image' }
}

/**
 * A key without a detail axis resolves to its one image. A key WITH an axis resolves, for the cell, in this order: the picked value's image,
 * then the default value's image, then the role fallback (the caller's flat fill). Without a cell the default value is used. The result records
 * which step happened (`picked`, `detail`, `detailFallback`).
 */
export function resolveVisual(snapshot: RuntimeSnapshot | null, visualKey: string, context: ResolveContext, cell?: Cell): Resolution {
  if (snapshot === null) return { kind: 'fallback', visualKey, family: null, reason: 'manifest_invalid' }
  const axis = snapshot.details.get(visualKey)
  if (axis === undefined) return resolveEntry(snapshot, visualKey, visualKey, context)
  const picked = cell === undefined ? axis.default : pickDetail(visualKey, cell.x, cell.y, DETAIL_SEED, axis.values)
  const first = declared(snapshot, visualKey, resolveEntry(snapshot, visualKey, slotKey(visualKey, picked), context), axis.values)
  if (first.kind === 'image') return { ...first, picked, detail: picked }
  if (picked === axis.default) return { ...first, picked }
  const second = declared(snapshot, visualKey, resolveEntry(snapshot, visualKey, slotKey(visualKey, axis.default), context), axis.values)
  if (second.kind === 'image') return { ...second, picked, detail: axis.default, detailFallback: first.reason }
  return { ...second, picked }
}
