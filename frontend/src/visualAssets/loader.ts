// Single-generation loading. `mount(snapshot)` creates a View for that snapshot's images and supersedes the previous one. A completion
// that belongs to a superseded View is dropped (its image is never stored and never reaches the newer View): a mounted view uses one
// manifest generation, whatever order the loads finish in.
import type { RuntimeSnapshot } from './manifest'
import { resolveVisual, type ImageStatus, type Resolution } from './resolver'

export interface Bitmap {
  readonly width: number
  readonly height: number
  close?: () => void
}
export type Decode = (url: string) => Promise<Bitmap>

export interface DroppedCompletion {
  readonly generation: string
  readonly file: string
}

export class View {
  readonly snapshot: RuntimeSnapshot
  readonly ready: Promise<void>
  superseded = false
  private readonly statuses = new Map<string, ImageStatus>()
  private readonly bitmaps = new Map<string, Bitmap>()
  private readonly urlFor: (file: string) => string | undefined

  constructor(
    snapshot: RuntimeSnapshot,
    urlFor: (file: string) => string | undefined,
    decode: Decode,
    onDropped: (dropped: DroppedCompletion) => void,
  ) {
    this.snapshot = snapshot
    this.urlFor = urlFor
    const files = [...new Set([...snapshot.entries.values()].map((entry) => entry.file))]
    const sizes = new Map([...snapshot.entries.values()].map((entry) => [entry.file, entry] as const))
    this.ready = Promise.all(
      files.map(async (file) => {
        const url = this.urlFor(file)
        if (url === undefined) {
          this.statuses.set(file, 'missing') // not in the build: nothing is fetched
          return
        }
        let bitmap: Bitmap | null = null
        let failed = false
        try {
          bitmap = await decode(url)
        } catch {
          failed = true
        }
        if (this.superseded) {
          bitmap?.close?.()
          this.statuses.set(file, 'late')
          onDropped({ generation: snapshot.generation, file })
          return
        }
        const entry = sizes.get(file)
        if (failed || bitmap === null || entry === undefined || bitmap.width !== entry.width || bitmap.height !== entry.height) {
          bitmap?.close?.()
          this.statuses.set(file, 'decode_failed')
          return
        }
        this.bitmaps.set(file, bitmap)
        this.statuses.set(file, 'ok')
      }),
    ).then(() => undefined)
  }

  resolve(visualKey: string): Resolution {
    return resolveVisual(this.snapshot, visualKey, { urlFor: this.urlFor, statusOf: (file) => this.statuses.get(file) })
  }

  /** The decoded image of a file, only if it loaded in THIS view. */
  bitmapFor(file: string): Bitmap | undefined {
    return this.bitmaps.get(file)
  }

  statusOf(file: string): ImageStatus | undefined {
    return this.statuses.get(file)
  }
}

export class SnapshotLoader {
  current: View | null = null
  readonly dropped: DroppedCompletion[] = []
  private readonly decode: Decode
  private readonly urlFor: (file: string) => string | undefined

  constructor(decode: Decode, urlFor: (file: string) => string | undefined) {
    this.decode = decode
    this.urlFor = urlFor
  }

  mount(snapshot: RuntimeSnapshot): View {
    if (this.current) this.current.superseded = true
    const view = new View(snapshot, this.urlFor, this.decode, (d) => this.dropped.push(d))
    this.current = view
    return view
  }
}
