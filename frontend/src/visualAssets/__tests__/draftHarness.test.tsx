import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DraftHarness } from '../DraftHarness'
import { parseDraftPreview, asRuntimeSnapshot } from '../draftManifest'
import { draftManifestText, draftUrlFor } from '../draftSource'
import { SnapshotLoader, type Bitmap, type Decode } from '../loader'
import { pickDetail, DETAIL_SEED } from '../pickDetail'
import { CELL_SIZE } from '../cell'
import {
  MAP_COLUMNS, MAP_ROWS, TERRAIN_CODES, TERRAIN_DRAFT_KEYS, TILE_COLORS_COPY, drawDraftMap, mapCodes,
} from '../terrainDrafts'
import { Recorder } from './pilotHelpers'

const snapshot = parseDraftPreview(draftManifestText)
const scales = new Map(snapshot.entries.map((e) => [e.file, e.scale] as const))
type Tagged = Bitmap & { url: string }
const decode: Decode = async (url) => ({ width: 128, height: 128, url } as Tagged)

async function viewOf() {
  const view = new SnapshotLoader(decode, draftUrlFor).mount(asRuntimeSnapshot(snapshot))
  await view.ready
  return view
}

let contexts: Recorder[]
beforeEach(() => {
  contexts = []
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(() => {
    const ctx = new Recorder()
    contexts.push(ctx)
    return ctx as unknown as CanvasRenderingContext2D
  })
})
afterEach(() => vi.restoreAllMocks())

describe('drawing the sample map from the fixture draft set', () => {
  it('draws every present code at its logical size, 1/scale with smoothing off, and the detail pickDetail names for forest cells', async () => {
    const ctx = new Recorder()
    const outcomes = drawDraftMap(ctx.asCtx(), await viewOf(), 'draft', scales)
    expect(ctx.imageSmoothingEnabled).toBe(false)
    const codes = mapCodes().flat()
    const present = new Set([6, 7, 8, 9, 15]) // forest, desert, swamp, mountain, grassland have drafts in the fixture
    const images = ctx.of('drawImage')
    expect(images).toHaveLength(codes.filter((c) => present.has(c)).length)
    for (const call of images) expect(call.slice(4)).toEqual([CELL_SIZE, CELL_SIZE]) // a 128 px preview drawn at 16 x 16: scale 8
    // forest cells: the drawn file is the slot pickDetail names for that cell (the fixture holds all three)
    let index = 0
    const fileOf = (detail: string) => snapshot.entries.find((e) => e.visualKey === 'terrain.forest' && (e.detail ?? 'plain') === detail)!.file
    for (let y = 0; y < MAP_ROWS; y++) {
      for (let x = 0; x < MAP_COLUMNS; x++) {
        const code = codes[y * MAP_COLUMNS + x]
        if (!present.has(code)) continue
        const [, bitmap, px, py] = images[index++] as [string, Tagged, number, number]
        expect([px, py]).toEqual([x * CELL_SIZE, y * CELL_SIZE])
        if (code === 6) expect(bitmap.url).toBe(draftUrlFor(fileOf(pickDetail('terrain.forest', x, y, DETAIL_SEED, ['plain', 'bush', 'tree']))))
      }
    }
    expect(outcomes.filter((o) => o.kind === 'draft')).toHaveLength(images.length)
  })

  it('shows a code with no draft as the flat fill with a diagonal mark, labelled as a fallback, and nothing is drawn for it as an image', async () => {
    const ctx = new Recorder()
    const outcomes = drawDraftMap(ctx.asCtx(), await viewOf(), 'draft', scales)
    const missing = outcomes.filter((o) => o.kind === 'fallback')
    expect(new Set(missing.map((o) => o.code))).toEqual(new Set(TERRAIN_CODES.filter((c) => ![6, 7, 8, 9, 15].includes(c))))
    expect(ctx.of('stroke')).toHaveLength(missing.length) // one diagonal per missing cell
    expect(ctx.fills.filter((fill) => fill === TILE_COLORS_COPY[0]).length).toBeGreaterThan(0) // Floor has no draft: its own fill
  })

  it('draws plain colour fills for the flat control and no image', async () => {
    const ctx = new Recorder()
    drawDraftMap(ctx.asCtx(), await viewOf(), 'flat', scales)
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.of('fillRect')).toHaveLength(MAP_COLUMNS * MAP_ROWS)
    expect(new Set(ctx.fills)).toEqual(new Set(mapCodes().flat().map((c) => TILE_COLORS_COPY[c])))
  })

  it('shows every cell as the fallback, without a diagonal, when there is no view (nothing loaded)', () => {
    const ctx = new Recorder()
    const outcomes = drawDraftMap(ctx.asCtx(), null, 'draft', scales)
    expect(outcomes.every((o) => o.kind === 'fallback')).toBe(true)
    expect(ctx.of('stroke')).toHaveLength(0)
  })

  it('is deterministic: two draws record the same calls', async () => {
    const view = await viewOf()
    const a = new Recorder()
    const b = new Recorder()
    drawDraftMap(a.asCtx(), view, 'draft', scales)
    drawDraftMap(b.asCtx(), view, 'draft', scales)
    expect(b.calls).toEqual(a.calls)
  })
})

describe('DraftHarness', () => {
  async function settled() {
    await waitFor(() => expect(screen.getByTestId('draft-page').getAttribute('data-settled')).toBe('true'))
  }

  it('shows the set id and the exact DraftSet file hash the adopt-set confirmation prints', async () => {
    render(<DraftHarness manifestText={draftManifestText} urlFor={draftUrlFor} decode={decode} />)
    await settled()
    expect(screen.getByTestId('draft-set-id').textContent).toBe('fixture-terrain')
    expect(screen.getByTestId('draft-set-hash').textContent).toBe(snapshot.draftSetHash)
    expect(screen.getByTestId('draft-page').getAttribute('data-set-hash')).toBe(snapshot.draftSetHash)
    expect(snapshot.draftSetHash).toMatch(/^sha256:[0-9a-f]{64}$/)
  })

  it('lists, per terrain code, which draft is shown (each forest slot with its source) or that it is missing', async () => {
    render(<DraftHarness manifestText={draftManifestText} urlFor={draftUrlFor} decode={decode} />)
    await settled()
    expect(screen.getAllByTestId(/^status-\d+$/)).toHaveLength(23)
    const forest = screen.getByTestId('status-6')
    expect(forest.getAttribute('data-missing')).toBe('false')
    expect(forest.textContent).toContain('terrain.forest')
    for (const slot of ['plain', 'bush', 'tree']) expect(forest.textContent).toContain(`${slot}: draft_terrain_forest`)
    expect(screen.getByTestId('status-7').textContent).toContain('draft: desert (in-') // a key with no axis: the draft, its source asset and intake
    const floor = screen.getByTestId('status-0')
    expect(floor.getAttribute('data-missing')).toBe('true')
    expect(floor.textContent).toContain('missing')
    expect(TERRAIN_DRAFT_KEYS[0]).toBe('terrain.floor')
    expect(screen.getAllByTestId(/^status-\d+$/).filter((r) => r.getAttribute('data-missing') === 'true')).toHaveLength(18)
  })

  it('draws two canvases of the whole map and the toggle hides the flat one', async () => {
    render(<DraftHarness manifestText={draftManifestText} urlFor={draftUrlFor} decode={decode} />)
    await settled()
    const canvases = [...document.querySelectorAll('canvas')]
    expect(canvases.map((c) => [c.width, c.height])).toEqual([[MAP_COLUMNS * CELL_SIZE, MAP_ROWS * CELL_SIZE], [MAP_COLUMNS * CELL_SIZE, MAP_ROWS * CELL_SIZE]])
    expect(canvases.every((c) => c.style.imageRendering === 'pixelated')).toBe(true)
    fireEvent.click(screen.getByRole('checkbox'))
    expect(document.querySelectorAll('canvas')).toHaveLength(1)
  })

  it('shows an alert and no set for a manifest that is not a draft preview manifest (a runtime manifest is refused)', async () => {
    const { pilotManifestText } = await import('../pilotSource')
    render(<DraftHarness manifestText={pilotManifestText} urlFor={draftUrlFor} decode={decode} />)
    await settled()
    expect(screen.getByRole('alert').textContent).toMatch(/unknown_field|missing_field|wrong_record_type/)
    expect(screen.getByTestId('draft-set-hash').textContent).toBe('none')
  })

  it('opens an exported folder chosen with the picker, or says what is missing from the chosen folder', async () => {
    render(<DraftHarness manifestText={draftManifestText} urlFor={draftUrlFor} decode={decode} />)
    await settled()
    URL.createObjectURL = vi.fn(() => 'blob:x')
    URL.revokeObjectURL = vi.fn()
    const input = screen.getByTestId('draft-folder') as HTMLInputElement
    fireEvent.change(input, { target: { files: [new File(['x'], 'notes.txt')] } })
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('draft_preview_manifest.json'))
    const other = JSON.stringify({ ...JSON.parse(draftManifestText), set_id: 'other-set' })
    fireEvent.change(input, { target: { files: [new File([other], 'draft_preview_manifest.json'), new File(['png'], `${'a'.repeat(64)}.png`)] } })
    await waitFor(() => expect(screen.getByTestId('draft-set-id').textContent).toBe('other-set'))
  })
})
