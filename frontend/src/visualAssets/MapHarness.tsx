// The isolated whole-map page (AM5-W03-SET / W07, docs/assets/pilot_terrain_m5_criteria.md): the predeclared 40 x 24 scene drawn from the real rc-0005 export with borders on or off and as the
// flat-fill control, at native scale with smoothing off. Mounted only from tests and from the dev-only page frontend/rehearsal-map.html. It touches no simulation state, no WebSocket and
// none of the normal Live Map code.
import { useEffect, useMemo, useRef, useState } from 'react'
import { browserRasterize } from './borderRender'
import { CELL_SIZE } from './cell'
import { SnapshotLoader, type Decode, type View } from './loader'
import { ManifestError, parseManifest, type RuntimeSnapshot } from './manifest'
import { drawMapScene } from './mapScene'
import { MAP_COLUMNS, MAP_ROWS } from './terrainDrafts'

export interface MapHarnessProps {
  readonly manifestText: string
  readonly urlFor: (file: string) => string | undefined
  readonly decode: Decode
  /** Test hook: the rasteriser the borders use (the browser's by default). */
  readonly rasterize?: typeof browserRasterize
}

const PIXELATED = { imageRendering: 'pixelated' } as const

function tryParse(manifestText: string): { snapshot: RuntimeSnapshot | null; error: string | null } {
  try {
    return { snapshot: parseManifest(manifestText), error: null }
  } catch (failure) {
    return { snapshot: null, error: failure instanceof ManifestError ? failure.message : 'manifest could not be read' }
  }
}

export function MapHarness({ manifestText, urlFor, decode, rasterize = browserRasterize }: MapHarnessProps) {
  const { snapshot, error } = useMemo(() => tryParse(manifestText), [manifestText])
  const [loaded, setLoaded] = useState<View | null>(null)
  const [borders, setBorders] = useState(true)
  const [fringed, setFringed] = useState(0)
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
    // The fringe count is read back from the drawing (not recomputed), so the page reports what it really drew.
    const count = imageCtx ? drawMapScene(imageCtx, view, 'image', { borders, rasterize }).fringed.length : 0
    const flatCtx = flat.current?.getContext('2d')
    if (flatCtx) drawMapScene(flatCtx, view, 'flat')
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the status line reports the drawing just made
    setFringed(count)
  }, [settled, view, borders, rasterize])

  const width = MAP_COLUMNS * CELL_SIZE
  const height = MAP_ROWS * CELL_SIZE
  return (
    <main data-testid="map" data-settled={settled} data-generation={view?.snapshot.generation ?? 'none'} data-borders={borders} data-fringed={fringed}>
      <h1>Whole-map rehearsal (terrain set)</h1>
      <p>Real rc-0005 export: 22 terrain tiles, the forest slots and the nine border masks, the predeclared {MAP_COLUMNS} x {MAP_ROWS} scene. Not the game.</p>
      {error && <p role="alert">{error}</p>}
      <label>
        <input type="checkbox" data-testid="map-borders" checked={borders} onChange={(e) => setBorders(e.target.checked)} /> Show terrain borders
      </label>
      <p data-testid="map-status">{borders ? `Borders on: ${fringed} map cells carry a fringe.` : 'Borders off: every cell is one terrain with a hard edge.'}</p>
      <section aria-label="image scene">
        <p>Image scene: each terrain uses its tile{borders ? ' and fringes' : ''}; markers on top.</p>
        <canvas ref={image} width={width} height={height} role="img" aria-label="whole-map scene drawn from the release" style={PIXELATED} />
      </section>
      <section aria-label="flat control">
        <p>Flat control: every cell uses its flat fill; same markers.</p>
        <canvas ref={flat} width={width} height={height} role="img" aria-label="the same scene with flat fills only" style={PIXELATED} />
      </section>
    </main>
  )
}
