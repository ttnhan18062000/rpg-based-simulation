// The isolated icon preview page (TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET): the draft set `icons-key-v1` shown so the owner can judge the style on a few icons before `adopt-set`.
// Mounted only from tests and from the dev-only page frontend/rehearsal-icons.html. It touches no simulation state, no WebSocket, no network and none of the Live Map code; it imports
// nothing from outside src/visualAssets. It computes NO pass or fail: the verdict is the recorded result of the Python sheet rule (tests/visual_assets/icon_draft_set.py), printed below.
// The colour-vision columns are SVG colour matrices, a visual approximation for the eye only.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { parseDraftPreview, type DraftEntry, type DraftSnapshot } from './draftManifest'
import { ManifestError } from './manifest'
import {
  BUFF_KEY, DEBUFF_KEY, GLYPH_KEY, ICON_KEYS, ICON_SIZES, LUCIDE_PATHS, MARKER_LAYERS, PLATE_KEY, SCENE_COLUMNS, SCENE_MARKERS, SCENE_ROW_COUNT, TIERS, TILE_FILLS, VISION_FILTERS,
  fallbackFor, sceneKey, tierKey, type Fallback,
} from './iconScene'
import { cssSizeAtScale, normaliseDpr } from './pixelFit'

export interface IconSource {
  readonly manifestText: string
  readonly ruleResultText: string
  readonly urlFor: (file: string) => string | undefined
}

const PIXELATED = { imageRendering: 'pixelated' } as const
const DARK = '#111827'
const LIGHT = '#e5e7eb'

function useDpr(): number {
  const read = () => normaliseDpr(typeof window === 'undefined' ? 1 : window.devicePixelRatio)
  const [dpr, setDpr] = useState(read)
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined
    const query = window.matchMedia(`(resolution: ${dpr}dppx)`)
    const onChange = () => setDpr(read())
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [dpr])
  return dpr
}

interface RuleResult {
  readonly set_id: string
  readonly draft_set_hash: string
  readonly result: string
  readonly i1: boolean
  readonly i2: boolean
  readonly i3: boolean
  readonly rule: Readonly<Record<string, string>>
  readonly groups: Readonly<Record<string, { size: number; pairs: number; min_shape_px_across_classes: number | null; min_dL_by_vision: Readonly<Record<string, number>> }>>
  readonly plates: Readonly<Record<string, { rim_colours: readonly string[]; closest_by_vision: Readonly<Record<string, { dL: number; tile: string }>> }>>
  readonly off_palette_pixels?: Readonly<Record<string, number>>
  readonly lint: Readonly<Record<string, { warnings: readonly string[]; colors: number; color_budget: number }>>
  readonly glyph_live_area: { bbox: readonly number[]; margin: readonly number[] }
}

function parseResult(text: string): RuleResult | null {
  try {
    return JSON.parse(text) as RuleResult
  } catch {
    return null
  }
}

function tryParse(text: string): { snapshot: DraftSnapshot | null; error: string | null } {
  try {
    return { snapshot: parseDraftPreview(text), error: null }
  } catch (failure) {
    return { snapshot: null, error: failure instanceof ManifestError ? failure.message : 'the manifest could not be read' }
  }
}

function FallbackView({ fallback }: { fallback: Fallback }): ReactNode {
  switch (fallback.kind) {
    case 'emoji':
      return <span style={{ fontSize: 20, color: fallback.color }} title={fallback.note}>{fallback.glyph}</span>
    case 'lucide':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={fallback.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-label={`Lucide ${fallback.name}`}>
          {LUCIDE_PATHS[fallback.name].map((d) => <path key={d} d={d} />)}
        </svg>
      )
    case 'chip':
      return <span style={{ background: fallback.color, color: '#0e1018', fontWeight: 700, padding: '0 6px', borderRadius: 3 }}>{fallback.letter}</span>
    case 'text':
      return <em>{fallback.text}</em>
    default:
      return <em>no plate</em>
  }
}

export function IconHarness({ manifestText, ruleResultText, urlFor }: IconSource) {
  const dpr = useDpr()
  const [scale, setScale] = useState(2)
  const { snapshot, error } = useMemo(() => tryParse(manifestText), [manifestText])
  const result = useMemo(() => parseResult(ruleResultText), [ruleResultText])
  const entries = useMemo(() => {
    const byKey = new Map<string, DraftEntry>()
    for (const e of snapshot?.entries ?? []) if (e.detail === null || e.adopted || !byKey.has(e.visualKey)) byKey.set(e.visualKey, e)
    return byKey
  }, [snapshot])

  if (error || !snapshot) return <p role="alert">The preview manifest was refused: {error}</p>

  const urlOf = (key: string): string | undefined => {
    const entry = entries.get(key)
    return entry ? urlFor(entry.file) : undefined
  }
  const nativeOf = (key: string): number => ICON_SIZES[key] ?? 16
  const Img = ({ k, n, label }: { k: string; n: number; label?: string }) => {
    const size = cssSizeAtScale(n, nativeOf(k), dpr)
    return <img src={urlOf(k)} alt={label ?? k} data-key={k} data-scale={n} width={size} height={size} style={{ ...PIXELATED, width: size, height: size }} draggable={false} />
  }
  const Marker = ({ n }: { n: number }) => {
    const size = cssSizeAtScale(n, 16, dpr)
    return (
      <span style={{ position: 'relative', display: 'inline-block', width: size, height: size }} data-marker="plate-then-glyph">
        {MARKER_LAYERS.map((k) => <img key={k} src={urlOf(k)} alt="" data-key={k} data-scale={n} width={size} height={size} style={{ ...PIXELATED, position: 'absolute', left: 0, top: 0 }} draggable={false} />)}
      </span>
    )
  }
  const Tile = ({ k, n }: { k: string; n: number }) => {
    const size = cssSizeAtScale(n, 16, dpr)
    return urlOf(k)
      ? <img src={urlOf(k)} alt={k} data-key={k} data-scale={n} width={size} height={size} style={{ ...PIXELATED, display: 'block' }} draggable={false} />
      : <span style={{ display: 'block', width: size, height: size, background: TILE_FILLS[k] ?? '#444' }} data-fallback="flat-fill" />
  }

  const tileKeys = ['terrain.floor', 'terrain.snow']
  const cell = cssSizeAtScale(scale, 16, dpr)
  const iconKeys = ICON_KEYS.filter((k) => entries.has(k))

  return (
    <main style={{ padding: 12 }}>
      <h1>Icon key set preview (dev only)</h1>
      <p>Draft set <strong>{snapshot.setId}</strong>, draft set hash <code>{snapshot.draftSetHash}</code>. Draft only: nothing here is adopted, released or read by the game.</p>
      <label>whole-number scale for tiles and the scene{' '}
        <select value={scale} onChange={(e) => setScale(Number(e.target.value))} aria-label="device pixels per art pixel">
          {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}x</option>)}
        </select>
      </label>{' '}
      <span data-testid="dpr-note">devicePixelRatio {dpr}: one art pixel is {scale} device pixel{scale === 1 ? '' : 's'} ({(scale / dpr).toFixed(3)} CSS px)</span>

      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
        {VISION_FILTERS.filter((f) => f.values).map((f) => (
          <filter key={f.id} id={`icon-vision-${f.id}`} colorInterpolationFilters="linearRGB"><feColorMatrix type="matrix" values={f.values} /></filter>
        ))}
      </svg>

      <section aria-labelledby="sheet">
        <h2 id="sheet">Contact sheet: every key at 1x and 2x on a dark and a light panel, beside its fallback</h2>
        <table>
          <thead><tr><th>key</th><th>size</th><th>1x dark</th><th>2x dark</th><th>1x light</th><th>2x light</th><th>fallback today</th></tr></thead>
          <tbody>
            {iconKeys.map((k) => {
              const fb = fallbackFor(k)
              return (
                <tr key={k}>
                  <td><code>{k}</code></td>
                  <td>{nativeOf(k)}x{nativeOf(k)}</td>
                  {[[1, DARK], [2, DARK], [1, LIGHT], [2, LIGHT]].map(([n, bg]) => <td key={`${n}${bg}`} style={{ background: bg as string, padding: 4 }}><Img k={k} n={n as number} /></td>)}
                  <td><FallbackView fallback={fb} /> <small>{fb.note}</small></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      <section aria-labelledby="rim">
        <h2 id="rim">Plate and glyph over the darkest and the brightest terrain-v1 tile</h2>
        <p>The plate rim is the mid-light colour <code>#9ea4b6</code>, not a dark outline: the terrain is dark, and a dark rim cannot clear the floor tile (docs/assets/icon_criteria.md).</p>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {tileKeys.map((k) => (
            <figure key={k} style={{ margin: 0 }}>
              <div style={{ position: 'relative', width: cell * 3, height: cell * 3, display: 'grid', gridTemplateColumns: `repeat(3, ${cell}px)` }} data-testid={`rim-${k}`}>
                {Array.from({ length: 9 }, (_, i) => <Tile key={i} k={k} n={scale} />)}
                <div style={{ position: 'absolute', left: cell, top: cell }}><Marker n={scale} /></div>
              </div>
              <figcaption>{k}{result ? ` (recorded closest L* gap to the plate rim: ${result.plates[PLATE_KEY]?.closest_by_vision.normal.dL.toFixed(1)}, ${result.plates[PLATE_KEY]?.closest_by_vision.normal.tile})` : ''}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section aria-labelledby="scene">
        <h2 id="scene">A small map scene at a whole-number scale</h2>
        <div style={{ position: 'relative', width: cell * SCENE_COLUMNS, height: cell * SCENE_ROW_COUNT, display: 'grid', gridTemplateColumns: `repeat(${SCENE_COLUMNS}, ${cell}px)` }} data-testid="scene">
          {Array.from({ length: SCENE_ROW_COUNT }, (_, y) => Array.from({ length: SCENE_COLUMNS }, (_, x) => <Tile key={`${x},${y}`} k={sceneKey(x, y)} n={scale} />))}
          {SCENE_MARKERS.map(([x, y]) => <div key={`${x},${y}`} style={{ position: 'absolute', left: x * cell, top: y * cell }}><Marker n={scale} /></div>)}
        </div>
      </section>

      <section aria-labelledby="vision">
        <h2 id="vision">Tier ladder and status frames in colour, greyscale and three simulated visions</h2>
        <p data-testid="approximation-note"><strong>Visual approximation only</strong> (SVG colour matrices in linear RGB, Machado 2009 severity 1.0). It is not a verdict: the verdict is the recorded result of the Python sheet rule printed below, and this page computes no pass or fail.</p>
        <table>
          <thead><tr><th />{VISION_FILTERS.map((f) => <th key={f.id}>{f.label}</th>)}</tr></thead>
          <tbody>
            <tr>
              <th>tiers E D C B A S SS SSS</th>
              {VISION_FILTERS.map((f) => (
                <td key={f.id} style={{ background: DARK, padding: 6, filter: f.values ? `url(#icon-vision-${f.id})` : undefined }} data-vision={f.id}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>{TIERS.map((t) => <Img key={t} k={tierKey(t)} n={4} label={`tier ${t.toUpperCase()}`} />)}</div>
                </td>
              ))}
            </tr>
            <tr>
              <th>letters, as text beside the badges</th>
              <td colSpan={VISION_FILTERS.length} style={{ fontFamily: 'monospace' }}>{TIERS.map((t) => t.toUpperCase()).join('   ')} (the letter stays as text; the badge never replaces it)</td>
            </tr>
            <tr>
              <th>buff, debuff</th>
              {VISION_FILTERS.map((f) => (
                <td key={f.id} style={{ background: DARK, padding: 6, filter: f.values ? `url(#icon-vision-${f.id})` : undefined }} data-vision={f.id}>
                  <div style={{ display: 'flex', gap: 10 }}><Img k={BUFF_KEY} n={4} label="buff frame" /><Img k={DEBUFF_KEY} n={4} label="debuff frame" /></div>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </section>

      {result && (
        <section aria-labelledby="recorded">
          <h2 id="recorded">Recorded result of the sheet rule (I1 to I3), as measured</h2>
          <p>From <code>python -m tests.visual_assets.icon_draft_set</code> on the set above (committed as <code>rule_result.json</code>); the page only displays it.</p>
          <table data-testid="recorded-result">
            <tbody>
              <tr><th>result</th><td><strong>{result.result}</strong> (I1 {String(result.i1)}, I2 {String(result.i2)}, I3 {String(result.i3)})</td></tr>
              {Object.entries(result.rule).map(([id, text]) => <tr key={id}><th>{id.toUpperCase()}</th><td>{text}</td></tr>)}
              {Object.entries(result.groups).map(([name, g]) => (
                <tr key={name}><th>group {name}</th><td>{g.pairs} pair(s) at {g.size}x{g.size}; smallest silhouette difference across classes {g.min_shape_px_across_classes ?? 'n/a'} px; smallest L* gap by vision {Object.entries(g.min_dL_by_vision).map(([v, d]) => `${v} ${d}`).join(', ')}</td></tr>
              ))}
              {Object.entries(result.plates).map(([name, p]) => (
                <tr key={name}><th>plate {name}</th><td>rim colours {p.rim_colours.join(', ')}; closest terrain tile by vision {Object.entries(p.closest_by_vision).map(([v, c]) => `${v} ${c.dL} (${c.tile})`).join(', ')}</td></tr>
              ))}
              <tr><th>off-palette pixels</th><td>{Object.keys(result.off_palette_pixels ?? {}).length === 0 ? 'none' : JSON.stringify(result.off_palette_pixels)}</td></tr>
              <tr><th>lint warnings</th><td>{Object.values(result.lint).every((l) => l.warnings.length === 0) ? 'none (info notes only)' : JSON.stringify(Object.fromEntries(Object.entries(result.lint).filter(([, l]) => l.warnings.length)))}</td></tr>
              <tr><th>glyph live area</th><td>bbox {result.glyph_live_area.bbox.join(', ')}; margins {result.glyph_live_area.margin.join(', ')} px on the 16x16 canvas</td></tr>
              <tr><th>glyph and plate</th><td>separate keys, composited plate first then glyph: <code>{MARKER_LAYERS.join(' then ')}</code> ({GLYPH_KEY})</td></tr>
            </tbody>
          </table>
        </section>
      )}
    </main>
  )
}
