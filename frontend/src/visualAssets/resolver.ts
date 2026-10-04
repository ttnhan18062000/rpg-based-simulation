// Pure, read-only resolver: a semantic visual key -> an image result or a typed fallback. It performs no I/O and
// registers nothing: the key set is the manifest's, finite, and an unknown key never causes a fetch.
import type { RuntimeSnapshot } from './manifest'

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
}

export interface FallbackResult {
  readonly kind: 'fallback'
  readonly visualKey: string
  // null when the family is not known (unknown key, or no valid manifest).
  readonly family: string | null
  readonly reason: FallbackReason
}

export type Resolution = ImageResult | FallbackResult

export interface ResolveContext {
  // The build's URL for a file, or undefined when the build does not contain it.
  readonly urlFor: (file: string) => string | undefined
  // How loading ended for a file in the view being resolved, or undefined while nothing is known (still loading).
  readonly statusOf?: (file: string) => ImageStatus | undefined
}

const STATUS_REASON = {
  missing: 'missing_image',
  decode_failed: 'decode_failed',
  late: 'late_result_dropped',
} as const

export function resolveVisual(snapshot: RuntimeSnapshot | null, visualKey: string, context: ResolveContext): Resolution {
  if (snapshot === null) return { kind: 'fallback', visualKey, family: null, reason: 'manifest_invalid' }
  const entry = snapshot.entries.get(visualKey)
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
