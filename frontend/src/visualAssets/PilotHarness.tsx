// The isolated pilot terrain page (AM5-W03/W05/W07, docs/assets/pilot_terrain_m5_criteria.md): the predeclared 12 x 8 crowded scene drawn twice at
// native scale with smoothing off, from the real pilot export ('image') and as the flat-fill control ('flat'). Mounted only from tests and from
// the dev-only page frontend/rehearsal-pilot.html. It touches no simulation state, no WebSocket and none of the normal Live Map code.
import { useEffect, useMemo, useRef, useState } from 'react'
import { CELL_SIZE } from './cell'
import { SnapshotLoader, type Decode, type View } from './loader'
import { ManifestError, parseManifest, type RuntimeSnapshot } from './manifest'
import { PILOT_COLUMNS, PILOT_ROWS, drawPilotScene, hoverText } from './pilotScene'

export interface PilotHarnessProps {
  readonly manifestText: string
  readonly urlFor: (file: string) => string | undefined
  readonly decode: Decode
}

const PIXELATED = { imageRendering: 'pixelated' } as const

function tryParse(manifestText: string): { snapshot: RuntimeSnapshot | null; error: string | null } {
  try {
    return { snapshot: parseManifest(manifestText), error: null }
  } catch (failure) {
    return { snapshot: null, error: failure instanceof ManifestError ? failure.message : 'manifest could not be read' }
  }
}

export function PilotHarness({ manifestText, urlFor, decode }: PilotHarnessProps) {
  const { snapshot, error } = useMemo(() => tryParse(manifestText), [manifestText])
  const [loaded, setLoaded] = useState<View | null>(null)
  const image = useRef<HTMLCanvasElement | null>(null)
  const flat = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    if (snapshot === null) return
    let cancelled = false
    const mounted = new SnapshotLoader(decode, urlFor).mount(snapshot)
    void mounted.ready.then(() => {
      if (!cancelled) setLoaded(mounted)
    })
    return () => {
      cancelled = true
      mounted.superseded = true
    }
  }, [snapshot, urlFor, decode])

  const view = snapshot !== null && loaded !== null && loaded.snapshot === snapshot ? loaded : null
  const settled = snapshot === null || view !== null

  useEffect(() => {
    if (!settled) return
    const imageCtx = image.current?.getContext('2d')
    if (imageCtx) drawPilotScene(imageCtx, view, 'image')
    const flatCtx = flat.current?.getContext('2d')
    if (flatCtx) drawPilotScene(flatCtx, view, 'flat')
  }, [settled, view])

  const width = PILOT_COLUMNS * CELL_SIZE
  const height = PILOT_ROWS * CELL_SIZE
  const hoverSample = [6, 8, 9, 7].map((code) => hoverText(code))
  return (
    <main data-testid="pilot" data-settled={settled} data-generation={view?.snapshot.generation ?? 'none'}>
      <h1>Pilot terrain rehearsal</h1>
      <p>Real pilot export, terrain.forest only, one {CELL_SIZE}-pixel cell. Not the game.</p>
      {error && <p role="alert">{error}</p>}
      <section aria-label="image scene">
        <p>Image scene: forest cells use the tile.</p>
        <canvas ref={image} width={width} height={height} role="img" aria-label={`pilot scene with the tile; hover text of a terrain cell is its name, for example ${hoverSample.join(', ')}`} style={PIXELATED} />
      </section>
      <section aria-label="flat control">
        <p>Flat control: forest cells use the flat fill.</p>
        <canvas ref={flat} width={width} height={height} role="img" aria-label="pilot scene with flat fills only" style={PIXELATED} />
      </section>
    </main>
  )
}
