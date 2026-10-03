// The isolated surface harness (AM5-W02, W03): one native 16 x 16 cell per fixture key, and a predeclared crowded 12 x 8 scene,
// drawn 1:1 with image smoothing off. Mounted only from tests and from the dev-only page frontend/rehearsal.html. It touches no
// simulation state, no WebSocket and none of the normal Live Map code.
import { useEffect, useMemo, useRef, useState } from 'react'
import { describeResolution } from './fallback'
import { CELL_SIZE } from './cell'
import { SnapshotLoader, type Decode, type View } from './loader'
import { ManifestError, parseManifest, type RuntimeSnapshot } from './manifest'
import { SCENE_COLUMNS, SCENE_ROWS, SINGLE_KEYS, drawCell, drawScene } from './scene'

export interface HarnessProps {
  readonly manifestText: string
  readonly urlFor: (file: string) => string | undefined
  readonly decode: Decode
}

const PIXELATED = { imageRendering: 'pixelated' } as const

function tryParse(manifestText: string): { snapshot: RuntimeSnapshot | null; error: string | null } {
  try {
    return { snapshot: parseManifest(manifestText), error: null }
  } catch (failure) {
    // an invalid manifest never reaches the resolver: every cell shows the typed manifest_invalid fallback
    return { snapshot: null, error: failure instanceof ManifestError ? failure.message : 'manifest could not be read' }
  }
}

export function RehearsalHarness({ manifestText, urlFor, decode }: HarnessProps) {
  const { snapshot, error } = useMemo(() => tryParse(manifestText), [manifestText])
  const [loaded, setLoaded] = useState<View | null>(null)
  const cells = useRef<(HTMLCanvasElement | null)[]>([])
  const scene = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    if (snapshot === null) return
    let cancelled = false
    const mounted = new SnapshotLoader(decode, urlFor).mount(snapshot)
    void mounted.ready.then(() => {
      if (!cancelled) setLoaded(mounted)
    })
    return () => {
      cancelled = true
      mounted.superseded = true // unmount: late completions are dropped, nothing is cached beyond this component
    }
  }, [snapshot, urlFor, decode])

  // settled: an invalid manifest is final at once; a valid one when ITS view finished loading (never a view of an older snapshot)
  const view = snapshot !== null && loaded !== null && loaded.snapshot === snapshot ? loaded : null
  const settled = snapshot === null || view !== null

  useEffect(() => {
    if (!settled) return
    SINGLE_KEYS.forEach((key, index) => {
      const ctx = cells.current[index]?.getContext('2d')
      if (ctx) drawCell(ctx, view, key, 0, 0)
    })
    const sceneCtx = scene.current?.getContext('2d')
    if (sceneCtx) drawScene(sceneCtx, view)
  }, [settled, view])

  const names = SINGLE_KEYS.map((key) => (view ? view.resolve(key) : { kind: 'fallback' as const, visualKey: key, family: null, reason: 'manifest_invalid' as const }))

  return (
    <main data-testid="rehearsal" data-settled={settled} data-generation={view?.snapshot.generation ?? 'none'}>
      <h1>Visual asset surface rehearsal</h1>
      <p>Synthetic fixture, map role only, one {CELL_SIZE}-pixel cell. Not the game.</p>
      {error && <p role="alert">{error}</p>}
      <section aria-label="single cells">
        <ul>
          {SINGLE_KEYS.map((key, index) => {
            const text = describeResolution(names[index])
            return (
              <li key={key}>
                <canvas
                  ref={(node) => { cells.current[index] = node }}
                  width={CELL_SIZE}
                  height={CELL_SIZE}
                  role="img"
                  aria-label={`${text.name}: ${text.detail}`}
                  style={PIXELATED}
                />{' '}
                <span data-testid="cell-text">{text.name}: {text.detail}</span>
              </li>
            )
          })}
        </ul>
      </section>
      <section aria-label="crowded scene">
        <canvas
          ref={scene}
          width={SCENE_COLUMNS * CELL_SIZE}
          height={SCENE_ROWS * CELL_SIZE}
          role="img"
          aria-label={`crowded scene, ${SCENE_COLUMNS} by ${SCENE_ROWS} cells of the three fixture keys, two cells with a key the release does not contain`}
          style={PIXELATED}
        />
      </section>
    </main>
  )
}
