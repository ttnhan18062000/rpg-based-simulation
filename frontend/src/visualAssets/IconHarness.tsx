// The isolated icon preview page (TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET): the draft set `icons-key-v1` shown so the owner can judge the style on a few icons before `adopt-set`.
// Mounted only from tests and from the dev-only page frontend/rehearsal-icons.html. It touches no simulation state, no WebSocket, no network and none of the Live Map code; it imports
// nothing from outside src/visualAssets. It computes NO pass or fail: the verdict is the recorded result of the Python sheet rule (visual_assets/review/icon_draft_set.py), printed below.
// The colour-vision columns are SVG colour matrices, a visual approximation for the eye only.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { parseDraftPreview, type DraftEntry, type DraftSnapshot } from './draftManifest'
import { ManifestError } from './manifest'
import {
  BUFF_KEY, DEBUFF_KEY, GLYPH_KEY, ICON_KEYS, ICON_SIZES, LUCIDE_PATHS, MARKER_LAYERS, PLATE_KEY, SCENE_COLUMNS, SCENE_MARKERS, SCENE_ROW_COUNT, TIERS, TILE_FILLS, VISION_FILTERS,
  RARITIES, V2_FAMILIES, familyOf, fallbackFor, rarityKey, sceneKey, tierKey, type Fallback,
} from './iconScene'
import { cssSizeAtScale, normaliseDpr } from './pixelFit'

export interface IconSource {
  readonly manifestText: string
  readonly ruleResultText: string
  readonly urlFor: (file: string) => string | undefined
  // Icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`), optional: its own export and recorded rule result, shown beside the adopted key set.
  readonly v2?: { readonly manifestText: string; readonly ruleResultText: string }
  // The one-colour silhouette sheet of the proposals the owner approves before any full drawing (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`), optional.
  readonly silhouettes?: { readonly sheetText: string }
  // The owner-fix revisions (r0002 of six adopted icons), optional: their own export and recorded results, shown beside the adopted drawings (r0001), never merged into them.
  readonly fixes?: { readonly manifestText: string; readonly ruleResultText: string }
}

interface FixesResult {
  readonly set_id: string
  readonly draft_set_hash: string
  readonly result: string
  readonly compliance_all_ok: boolean
  readonly proposed: readonly string[]
  readonly not_proposed: Readonly<Record<string, string>>
  readonly compliance: Readonly<Record<string, readonly { item: string; spec: string; measured: string; ok: boolean }[]>>
  readonly key_set_rule: { readonly result: string; readonly groups: Readonly<Record<string, { min_shape_px_across_classes: number | null; min_dL_by_vision: Readonly<Record<string, number>> }>> }
  readonly v2_rule: { readonly result: string; readonly groups: Readonly<Record<string, { min_shape_px_across_classes: number | null; value_checked?: boolean; min_dL_by_vision: Readonly<Record<string, number>> }>> }
  readonly rarity_vs_tier_min_shape_px: Readonly<Record<string, number>>
}

function parseFixesResult(text: string): FixesResult | null {
  try {
    const parsed = JSON.parse(text) as FixesResult
    return parsed.compliance ? parsed : null
  } catch {
    return null
  }
}

interface SheetShape { readonly key?: string; readonly tag?: string; readonly label?: string; readonly size: number; readonly rows: readonly string[] }
interface SheetOption extends SheetShape {
  readonly tag: string
  readonly label: string
  readonly i1_smallest_xor_px: number | null
  readonly nearest_in_any_family_xor_px_of_576: readonly { key: string; xor_px: number }[]
}
interface SheetSlot { readonly key: string; readonly size: number; readonly current_rows: readonly string[]; readonly neighbours: readonly SheetShape[]; readonly options: readonly SheetOption[] }
interface SilhouetteSheet { readonly decided: string; readonly slots: readonly SheetSlot[] }

function parseSheet(text: string): SilhouetteSheet | null {
  try {
    const parsed = JSON.parse(text) as SilhouetteSheet
    return Array.isArray(parsed.slots) ? parsed : null
  } catch {
    return null
  }
}

/** One shape as a one-colour SVG, whole device pixels per art pixel; `#` is a pixel. No colour beyond `ink` is ever used, so the owner judges the outline only. */
function Silhouette({ rows, size, px, ink, label }: { rows: readonly string[]; size: number; px: number; ink: string; label: string }): ReactNode {
  const runs: { x: number; y: number; w: number }[] = []
  rows.forEach((row, y) => {
    let x = 0
    while (x < row.length) {
      if (row[x] !== '#') { x += 1; continue }
      let end = x
      while (end < row.length && row[end] === '#') end += 1
      runs.push({ x, y, w: end - x })
      x = end
    }
  })
  return (
    <svg width={size * px} height={size * px} viewBox={`0 0 ${size} ${size}`} shapeRendering="crispEdges" role="img" aria-label={label} data-silhouette="true">
      {runs.map((r) => <rect key={`${r.x},${r.y}`} x={r.x} y={r.y} width={r.w} height={1} fill={ink} />)}
    </svg>
  )
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

interface V2Result {
  readonly set_id: string
  readonly draft_set_hash: string
  readonly result: string
  readonly i1: boolean
  readonly i2: boolean
  readonly i3: boolean
  readonly rule: Readonly<Record<string, string>>
  readonly groups: Readonly<Record<string, { size: number; pairs: number; min_shape_px_across_classes: number | null; value_checked: boolean; min_dL_by_vision: Readonly<Record<string, number>> }>>
  readonly off_palette_pixels?: Readonly<Record<string, number>>
  readonly lint: Readonly<Record<string, { warnings: readonly string[]; colors: number; color_budget: number }>>
  readonly glyph_live_area: Readonly<Record<string, { bbox: readonly number[]; margin: readonly number[] }>>
  readonly panel_live_area: Readonly<Record<string, readonly number[]>>
  readonly rarity_vs_tier_min_shape_px: Readonly<Record<string, number>>
}

function parseV2Result(text: string): V2Result | null {
  try {
    return JSON.parse(text) as V2Result
  } catch {
    return null
  }
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

export function IconHarness({ manifestText, ruleResultText, urlFor, v2, silhouettes, fixes }: IconSource) {
  const dpr = useDpr()
  const [scale, setScale] = useState(2)
  const { snapshot, error } = useMemo(() => tryParse(manifestText), [manifestText])
  const result = useMemo(() => parseResult(ruleResultText), [ruleResultText])
  const v2Parsed = useMemo(() => (v2 ? tryParse(v2.manifestText) : { snapshot: null, error: null }), [v2])
  const v2Result = useMemo(() => (v2 ? parseV2Result(v2.ruleResultText) : null), [v2])
  const sheet = useMemo(() => (silhouettes ? parseSheet(silhouettes.sheetText) : null), [silhouettes])
  const fixesParsed = useMemo(() => (fixes ? tryParse(fixes.manifestText) : { snapshot: null, error: null }), [fixes])
  const fixesResult = useMemo(() => (fixes ? parseFixesResult(fixes.ruleResultText) : null), [fixes])
  const fixEntries = useMemo(() => new Map((fixesParsed.snapshot?.entries ?? []).filter((e) => e.visualKey.startsWith('icon.')).map((e) => [e.visualKey, e] as const)), [fixesParsed])
  const entries = useMemo(() => {
    const byKey = new Map<string, DraftEntry>()
    for (const e of [...(snapshot?.entries ?? []), ...(v2Parsed.snapshot?.entries ?? [])]) if (e.detail === null || e.adopted || !byKey.has(e.visualKey)) byKey.set(e.visualKey, e)
    return byKey
  }, [snapshot, v2Parsed])

  if (error || !snapshot) return <p role="alert">The preview manifest was refused: {error}</p>
  if (v2Parsed.error) return <p role="alert">The icon set v2 preview manifest was refused: {v2Parsed.error}</p>
  if (fixesParsed.error) return <p role="alert">The owner-fixes preview manifest was refused: {fixesParsed.error}</p>

  const urlOf = (key: string): string | undefined => {
    const entry = entries.get(key)
    return entry ? urlFor(entry.file) : undefined
  }
  // The native size is read from the manifest (the preview's own size over its integer scale), so no key list is hard-coded here; ICON_SIZES stays as the fallback for the adopted key set.
  const nativeOf = (key: string): number => {
    const e = entries.get(key)
    return e ? e.width / e.scale : (ICON_SIZES[key] ?? 16)
  }
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
  const v2Keys = [...(v2Parsed.snapshot?.entries ?? [])].filter((e) => e.visualKey.startsWith('icon.')).map((e) => e.visualKey).sort()
  const v2Locations = [GLYPH_KEY, ...v2Keys.filter((k) => familyOf(k) === 'marker')]
  const v2Marker = ({ glyph, n }: { glyph: string; n: number }) => {
    const size = cssSizeAtScale(n, 16, dpr)
    return (
      <span style={{ position: 'relative', display: 'inline-block', width: size, height: size }} data-marker="v2-plate-then-glyph" data-glyph={glyph}>
        {[PLATE_KEY, glyph].map((k) => <img key={k} src={urlOf(k)} alt="" data-key={k} data-scale={n} width={size} height={size} style={{ ...PIXELATED, position: 'absolute', left: 0, top: 0 }} draggable={false} />)}
      </span>
    )
  }

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

      {silhouettes && sheet && (
        <section aria-labelledby="sil-sheet" data-testid="silhouette-sheet">
          <h2 id="sil-sheet">One-colour silhouette sheet: the proposed outlines, for the owner to approve before any drawing</h2>
          <p>{sheet.decided}. Every shape is one colour (the outline included): judge the outline only. Each row shows the icon as adopted today (r0001), the proposed new outline or outlines (A, B), and the neighbours it sits beside. The numbers are the sheet rule&apos;s shape measure against same-size neighbours (needed: 3 px at 8x8, 6 at 16x16, 8 at 24x24) and the look-alike report&apos;s distance to the nearest icon of any family out of 576 (smaller means more alike); they decide nothing.</p>
          {sheet.slots.map((slot) => (
            <div key={slot.key} data-slot={slot.key} style={{ marginBottom: 20 }}>
              <h3><code>{slot.key}</code> ({slot.size}x{slot.size})</h3>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                {[DARK, LIGHT].map((bg) => (
                  <div key={bg} style={{ background: bg, padding: 8, display: 'flex', gap: 14, alignItems: 'flex-end', flexWrap: 'wrap' }} data-panel={bg === DARK ? 'dark' : 'light'}>
                    <figure style={{ margin: 0 }} data-current="true">
                      <Silhouette rows={slot.current_rows} size={slot.size} px={cssSizeAtScale(scale * 3, 1, dpr)} ink={bg === DARK ? LIGHT : DARK} label={`${slot.key} as adopted`} />
                      <figcaption style={{ color: bg === DARK ? LIGHT : DARK }}>adopted today</figcaption>
                    </figure>
                    {slot.options.map((o) => (
                      <figure key={o.tag} style={{ margin: 0, outline: `2px solid ${bg === DARK ? '#34d399' : '#047857'}`, padding: 2 }} data-option={o.tag}>
                        <Silhouette rows={o.rows} size={o.size} px={cssSizeAtScale(scale * 3, 1, dpr)} ink={bg === DARK ? LIGHT : DARK} label={`${slot.key} proposal ${o.tag}: ${o.label}`} />
                        <figcaption style={{ color: bg === DARK ? LIGHT : DARK }}>{o.tag}: {o.label}</figcaption>
                      </figure>
                    ))}
                    {slot.neighbours.map((n) => (
                      <figure key={n.key} style={{ margin: 0, opacity: 0.8 }} data-neighbour={n.key}>
                        <Silhouette rows={n.rows} size={n.size} px={cssSizeAtScale(scale * 3, 1, dpr)} ink={bg === DARK ? LIGHT : DARK} label={`neighbour ${n.key}`} />
                        <figcaption style={{ color: bg === DARK ? LIGHT : DARK, fontSize: 11 }}>{(n.key ?? '').split('.').slice(-1)[0]}</figcaption>
                      </figure>
                    ))}
                  </div>
                ))}
              </div>
              <ul data-testid={`measures-${slot.key}`}>
                {slot.options.map((o) => (
                  <li key={o.tag}>{o.tag} ({o.label}): smallest shape difference to same-size neighbours {o.i1_smallest_xor_px ?? 'n/a'} px; nearest icon of any family {o.nearest_in_any_family_xor_px_of_576.map((n) => `${n.key.split('.').slice(1).join('.')} ${n.xor_px}`).join(', ')}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {fixes && fixesResult && (
        <section aria-labelledby="fixes" data-testid="owner-fixes">
          <h2 id="fixes">Owner fixes: the new revisions (r0002) beside the adopted drawings (r0001)</h2>
          <p>Draft set <strong>{fixesParsed.snapshot?.setId}</strong>, draft set hash <code>{fixesParsed.snapshot?.draftSetHash}</code>. {fixesResult.proposed.length} adopted icons are proposed a new revision each; nothing is adopted until the owner runs the commands in <code>docs/assets/icon_set_v2_review.md</code>. Left: what is adopted today. Right: the revision. The rows marked <strong>not proposed for adoption</strong> are drafts the owner decided not to revise: they stay in the draft set only because the store has no command to drop a draft, and they are never candidates.</p>
          <table>
            <thead><tr><th>key</th><th>adopted r0001: 1x dark, 2x dark, 1x light, 2x light</th><th>draft revision r0002 (a candidate only where it is proposed): 1x dark, 2x dark, 1x light, 2x light</th></tr></thead>
            <tbody>
              {[...fixEntries.keys()].sort().map((k) => {
                const fixEntry = fixEntries.get(k)!
                const native = fixEntry.width / fixEntry.scale
                const cellImg = (entry: DraftEntry | undefined, n: number, bg: string, label: string) => {
                  const size = cssSizeAtScale(n, native, dpr)
                  return entry ? <td key={`${label}${n}${bg}`} style={{ background: bg, padding: 4 }}><img src={urlFor(entry.file)} alt={`${k} ${label}`} data-key={k} data-revision={label} data-scale={n} width={size} height={size} style={{ ...PIXELATED, width: size, height: size }} draggable={false} /></td> : <td key={`${label}${n}${bg}`} />
                }
                const adopted = entries.get(k)
                const skipped = fixesResult.not_proposed[k]
                return (
                  <tr key={k} data-fix={k} data-not-proposed={skipped ? 'true' : undefined} style={skipped ? { opacity: 0.55 } : undefined}>
                    <td><code>{k}</code> ({native}x{native}){skipped && <div data-testid={`not-proposed-${k}`}><strong>not proposed for adoption</strong>: {skipped}</div>}</td>
                    {[[1, DARK], [2, DARK], [1, LIGHT], [2, LIGHT]].map(([n, bg]) => cellImg(adopted, n as number, bg as string, 'r0001'))}
                    {[[1, DARK], [2, DARK], [1, LIGHT], [2, LIGHT]].map(([n, bg]) => cellImg(fixEntry, n as number, bg as string, 'r0002'))}
                  </tr>
                )
              })}
            </tbody>
          </table>
          <h3>Recorded result, as measured</h3>
          <p>From <code>python -m visual_assets.review evaluate --set icons-owner-fixes-v1 --recorded</code> (committed as <code>icondraft_fixes/rule_result.json</code>): the adopted icons with the proposed revisions in place. The page only displays it.</p>
          <table data-testid="fixes-recorded-result">
            <tbody>
              <tr><th>sheet rule (thresholds unchanged)</th><td><strong>{fixesResult.result}</strong>: key-set groups {fixesResult.key_set_rule.result}, v2 groups {fixesResult.v2_rule.result}</td></tr>
              <tr><th>rarity vs the tier badges</th><td>{Object.entries(fixesResult.rarity_vs_tier_min_shape_px).map(([k, d]) => `${k.slice(k.lastIndexOf('.') + 1)} ${d} px`).join(', ')}</td></tr>
              <tr><th>spec compliance</th><td>{fixesResult.compliance_all_ok ? 'every measured row met' : 'SOME ROWS NOT MET'} ({Object.values(fixesResult.compliance).reduce((n, rows) => n + rows.length, 0)} rows)</td></tr>
            </tbody>
          </table>
          {Object.entries(fixesResult.compliance).map(([k, rows]) => (
            <table key={k} data-testid={`compliance-${k}`}>
              <caption><code>{k}</code>: {rows.every((r) => r.ok) ? 'all within the spec' : 'SPEC NOT MET'}</caption>
              <thead><tr><th>measurement</th><th>spec</th><th>measured from the pixels</th><th /></tr></thead>
              <tbody>{rows.map((r) => <tr key={r.item}><td>{r.item}</td><td>{r.spec}</td><td>{r.measured}</td><td>{r.ok ? 'ok' : 'FAIL'}</td></tr>)}</tbody>
            </table>
          ))}
        </section>
      )}

      {v2 && v2Result && (
        <>
          <section aria-labelledby="v2-sheet">
            <h2 id="v2-sheet">Icon set v2 contact sheet: {v2Keys.length} keys at 1x and 2x on a dark and a light panel, beside their fallbacks</h2>
            <p>Draft set <strong>{v2Parsed.snapshot?.setId}</strong>, draft set hash <code>{v2Parsed.snapshot?.draftSetHash}</code>. Draft only: nothing here is adopted, released or read by the game. The adopted key set is above.</p>
            {V2_FAMILIES.map((family) => {
              const keys = v2Keys.filter((k) => familyOf(k) === family)
              if (keys.length === 0) return null
              return (
                <div key={family} data-testid={`v2-family-${family}`}>
                  <h3>{family} ({keys.length})</h3>
                  <table>
                    <thead><tr><th>key</th><th>size</th><th>1x dark</th><th>2x dark</th><th>1x light</th><th>2x light</th><th>fallback today</th></tr></thead>
                    <tbody>
                      {keys.map((k) => {
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
                </div>
              )
            })}
          </section>

          <section aria-labelledby="v2-rim">
            <h2 id="v2-rim">Location glyphs on the plate over the darkest and the brightest terrain-v1 tile</h2>
            <p>Each row is one glyph (the adopted enemy camp first, then the five new ones) on the same plate, at the scale chosen above.</p>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {tileKeys.map((k) => (
                <figure key={k} style={{ margin: 0 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${v2Locations.length}, ${cell}px)`, background: TILE_FILLS[k] }} data-testid={`v2-rim-${k}`}>
                    {v2Locations.map((glyph) => (
                      <div key={glyph} style={{ position: 'relative', width: cell, height: cell }}>
                        <div style={{ position: 'absolute', inset: 0 }}><Tile k={k} n={scale} /></div>
                        <div style={{ position: 'absolute', left: 0, top: 0 }}>{v2Marker({ glyph, n: scale })}</div>
                      </div>
                    ))}
                  </div>
                  <figcaption>{k}</figcaption>
                </figure>
              ))}
            </div>
          </section>

          <section aria-labelledby="v2-rarity">
            <h2 id="v2-rarity">Rarity badges beside the tier badges, in colour, greyscale and three simulated visions</h2>
            <p data-testid="v2-approximation-note"><strong>Visual approximation only</strong> (SVG colour matrices in linear RGB): it computes no pass or fail. The badges are the same 8x8 size as the tiers; the name stays as text beside each.</p>
            <table>
              <thead><tr><th />{VISION_FILTERS.map((f) => <th key={f.id}>{f.label}</th>)}</tr></thead>
              <tbody>
                <tr>
                  <th>common, uncommon, rare, then tiers E D C B A S SS SSS</th>
                  {VISION_FILTERS.map((f) => (
                    <td key={f.id} style={{ background: DARK, padding: 6, filter: f.values ? `url(#icon-vision-${f.id})` : undefined }} data-v2-vision={f.id}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        {RARITIES.map((r) => <Img key={r} k={rarityKey(r)} n={4} label={`rarity ${r}`} />)}
                        <span style={{ width: 8 }} />
                        {TIERS.map((t) => <Img key={t} k={tierKey(t)} n={4} label={`tier ${t.toUpperCase()}`} />)}
                      </div>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </section>

          <section aria-labelledby="v2-recorded">
            <h2 id="v2-recorded">Icon set v2: recorded result of the sheet rule (I1 to I3), as measured</h2>
            <p>From <code>python -m visual_assets.review evaluate --set icons-v2 --recorded</code> on the set above (committed as <code>icondraft_v2/rule_result.json</code>); the page only displays it. Groups are the owner&apos;s answers of 2026-10-07: I1 only for the subject groups, I1 and I2 for rarity.</p>
            <table data-testid="v2-recorded-result">
              <tbody>
                <tr><th>result</th><td><strong>{v2Result.result}</strong> (I1 {String(v2Result.i1)}, I2 {String(v2Result.i2)}, I3 {String(v2Result.i3)})</td></tr>
                {Object.entries(v2Result.rule).map(([id, text]) => <tr key={id}><th>{id.toUpperCase()}</th><td>{text}</td></tr>)}
                {Object.entries(v2Result.groups).map(([name, g]) => (
                  <tr key={name}><th>group {name}</th><td>{g.pairs} pair(s) at {g.size}x{g.size}; smallest silhouette difference across classes {g.min_shape_px_across_classes ?? 'n/a'} px; {g.value_checked ? `smallest L* gap by vision ${Object.entries(g.min_dL_by_vision).map(([v, d]) => `${v} ${d}`).join(', ')}` : 'value separation not checked for this group (shape only)'}</td></tr>
                ))}
                <tr><th>rarity vs tier silhouettes</th><td>{Object.entries(v2Result.rarity_vs_tier_min_shape_px).map(([k, d]) => `${k.slice(k.lastIndexOf('.') + 1)} ${d} px`).join(', ')} from the nearest tier badge (at least 3 px asked)</td></tr>
                <tr><th>off-palette pixels</th><td>{Object.keys(v2Result.off_palette_pixels ?? {}).length === 0 ? 'none' : JSON.stringify(v2Result.off_palette_pixels)}</td></tr>
                <tr><th>lint warnings</th><td>{Object.values(v2Result.lint).every((l) => l.warnings.length === 0) ? 'none (info notes only)' : JSON.stringify(Object.fromEntries(Object.entries(v2Result.lint).filter(([, l]) => l.warnings.length)))}</td></tr>
                <tr><th>glyph live areas</th><td>{Object.entries(v2Result.glyph_live_area).map(([k, a]) => `${k.slice(k.lastIndexOf('.') + 1)} margins ${a.margin.join(', ')}`).join('; ')} px on the 16x16 canvas</td></tr>
              </tbody>
            </table>
          </section>
        </>
      )}

      {result && (
        <section aria-labelledby="recorded">
          <h2 id="recorded">Recorded result of the sheet rule (I1 to I3), as measured</h2>
          <p>From <code>python -m visual_assets.review evaluate --set icons-key-v1 --recorded</code> on the set above (committed as <code>rule_result.json</code>); the page only displays it.</p>
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
