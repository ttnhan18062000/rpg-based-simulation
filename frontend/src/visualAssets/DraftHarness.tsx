// The isolated draft preview page (TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE): a whole map drawn from a draft set so a set can be judged as a whole before `adopt-set`.
// Mounted only from tests and from the dev-only page frontend/rehearsal-draft.html. It touches no simulation state, no WebSocket, no network and none of the Live Map code.
// A set is opened from the committed fixture or from a folder written by `python -m visual_assets.store draft export` (chosen with the folder picker, read in the browser).
import { useEffect, useMemo, useRef, useState } from 'react'
import { CELL_SIZE } from './cell'
import { asRuntimeSnapshot, parseDraftPreview, type DraftSnapshot } from './draftManifest'
import { SnapshotLoader, type Decode, type View } from './loader'
import { ManifestError } from './manifest'
import { MAP_COLUMNS, MAP_ROWS, TERRAIN_CODES, TILE_NAMES_COPY, drawDraftMap, statusOf } from './terrainDrafts'

export interface DraftSource {
  readonly manifestText: string
  readonly urlFor: (file: string) => string | undefined
}

export interface DraftHarnessProps extends DraftSource {
  readonly decode: Decode
}

const PIXELATED = { imageRendering: 'pixelated' } as const
const MANIFEST_NAME = 'draft_preview_manifest.json'

function tryParse(manifestText: string): { snapshot: DraftSnapshot | null; error: string | null } {
  try {
    return { snapshot: parseDraftPreview(manifestText), error: null }
  } catch (failure) {
    return { snapshot: null, error: failure instanceof ManifestError ? failure.message : 'the manifest could not be read' }
  }
}

export function DraftHarness({ manifestText, urlFor, decode }: DraftHarnessProps) {
  const [source, setSource] = useState<DraftSource>({ manifestText, urlFor })
  const [pickError, setPickError] = useState<string | null>(null)
  const [showFlat, setShowFlat] = useState(true)
  const { snapshot, error } = useMemo(() => tryParse(source.manifestText), [source.manifestText])
  const [loaded, setLoaded] = useState<View | null>(null)
  const draft = useRef<HTMLCanvasElement | null>(null)
  const flat = useRef<HTMLCanvasElement | null>(null)
  const objectUrls = useRef<string[]>([])

  useEffect(() => () => objectUrls.current.forEach((url) => URL.revokeObjectURL(url)), [])

  useEffect(() => {
    if (snapshot === null) return
    let cancelled = false
    const mounted = new SnapshotLoader(decode, source.urlFor).mount(asRuntimeSnapshot(snapshot))
    void mounted.ready.then(() => {
      if (!cancelled) setLoaded(mounted)
    })
    return () => {
      cancelled = true
      mounted.superseded = true
    }
  }, [snapshot, source.urlFor, decode])

  const view = snapshot !== null && loaded !== null && loaded.snapshot.generation === snapshot.draftSetHash && loaded.snapshot.catalogId === snapshot.setId ? loaded : null
  const settled = snapshot === null || view !== null
  const files = useMemo(() => new Map((snapshot?.entries ?? []).map((e) => [e.file, { scale: e.scale, adopted: e.adopted }] as const)), [snapshot])

  useEffect(() => {
    if (!settled) return
    const draftCtx = draft.current?.getContext('2d')
    if (draftCtx) drawDraftMap(draftCtx, view, 'draft', files)
    const flatCtx = flat.current?.getContext('2d')
    if (flatCtx) drawDraftMap(flatCtx, view, 'flat', files)
  }, [settled, view, files, showFlat])

  async function openFolder(files: FileList | null) {
    setPickError(null)
    const list = files ? Array.from(files) : []
    const manifestFile = list.find((f) => f.name === MANIFEST_NAME)
    if (!manifestFile) {
      setPickError(`the chosen folder has no ${MANIFEST_NAME}; choose the folder written by "draft export"`)
      return
    }
    objectUrls.current.forEach((url) => URL.revokeObjectURL(url))
    const urls = new Map<string, string>()
    for (const file of list) if (/^[0-9a-f]{64}\.png$/.test(file.name)) urls.set(file.name, URL.createObjectURL(file))
    objectUrls.current = [...urls.values()]
    setLoaded(null)
    setSource({ manifestText: await manifestFile.text(), urlFor: (name) => urls.get(name) })
  }

  const width = MAP_COLUMNS * CELL_SIZE
  const height = MAP_ROWS * CELL_SIZE
  return (
    <main data-testid="draft-page" data-settled={settled} data-set-hash={snapshot?.draftSetHash ?? 'none'}>
      <h1>Draft set preview</h1>
      <p>Review a whole draft set on a map before it is adopted. Nothing here is adopted, released or read by the game.</p>
      <p>
        Set <strong data-testid="draft-set-id">{snapshot?.setId ?? 'none'}</strong>, {snapshot?.entries.length ?? 0} drafts. Draft set hash (the one the <code>adopt-set</code> confirmation
        prints): <code data-testid="draft-set-hash">{snapshot?.draftSetHash ?? 'none'}</code>
      </p>
      <p>
        <label>
          Open an exported set (the folder written by <code>draft export</code>):{' '}
          <input type="file" data-testid="draft-folder" {...({ webkitdirectory: '', directory: '' } as Record<string, string>)} multiple onChange={(e) => void openFolder(e.target.files)} />
        </label>
      </p>
      {(error || pickError) && <p role="alert">{error ?? pickError}</p>}
      <label>
        <input type="checkbox" checked={showFlat} onChange={(e) => setShowFlat(e.target.checked)} /> Show the plain colour fills beside the drafts
      </label>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
        <section aria-label="draft map">
          <p>Draft map: every Live Map terrain code in patches; a diagonal marks a code with no draft; a small amber square marks a reference to ADOPTED art (not a draft under review).</p>
          <canvas ref={draft} width={width} height={height} role="img" aria-label="sample map drawn from the draft set" style={PIXELATED} />
        </section>
        {showFlat && (
          <section aria-label="flat fills">
            <p>Flat fills: the same map with the plain colours.</p>
            <canvas ref={flat} width={width} height={height} role="img" aria-label="the same map with flat colour fills" style={PIXELATED} />
          </section>
        )}
      </div>
      <table data-testid="draft-status" style={{ marginTop: 12, borderCollapse: 'collapse' }}>
        <thead>
          <tr><th align="left">Code</th><th align="left">Terrain</th><th align="left">Visual key</th><th align="left">Draft shown</th></tr>
        </thead>
        <tbody>
          {TERRAIN_CODES.map((code) => {
            const s = statusOf(snapshot, code)
            return (
              <tr key={code} data-testid={`status-${code}`} data-missing={s.missing}>
                <td>{code}</td><td>{TILE_NAMES_COPY[code]}</td><td>{s.key}</td><td>{s.text}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </main>
  )
}
