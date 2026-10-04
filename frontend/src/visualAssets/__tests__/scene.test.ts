import { describe, expect, it } from 'vitest'
import { CELL_SIZE } from '../cell'
import { SnapshotLoader } from '../loader'
import { parseManifest } from '../manifest'
import { fixtureManifestText, fixtureUrlFor } from '../fixtureSource'
import { SCENE_COLUMNS, SCENE_ROWS, crowdedLayout, drawCell, drawScene } from '../scene'
import { RecordingContext, bitmap } from './helpers'

const snapshot = parseManifest(fixtureManifestText)

async function loadedView(urlFor: (f: string) => string | undefined = fixtureUrlFor) {
  const view = new SnapshotLoader(async () => bitmap(), urlFor).mount(snapshot)
  await view.ready
  return view
}

describe('the predeclared crowded scene', () => {
  it('is 12 x 8 cells with all three keys and exactly two cells the release does not contain', () => {
    const layout = crowdedLayout()
    expect(layout).toHaveLength(SCENE_COLUMNS * SCENE_ROWS)
    expect(new Set(layout)).toEqual(new Set(['fixture.rehearsal.gem', 'fixture.rehearsal.rock', 'fixture.rehearsal.frame', 'fixture.rehearsal.absent']))
    expect(layout.filter((k) => k.endsWith('.absent'))).toHaveLength(2)
    expect(crowdedLayout()).toEqual(layout) // predeclared: the same every time
  })

  it('draws every cell at native scale on the 16-pixel grid with smoothing off, images 1:1 and fallbacks for the rest', async () => {
    const ctx = new RecordingContext()
    drawScene(ctx, await loadedView())
    expect(ctx.imageSmoothingEnabled).toBe(false)
    const images = ctx.of('drawImage') as unknown as [string, unknown, number, number, ...unknown[]][]
    expect(images).toHaveLength(94)
    for (const [, , x, y, ...rest] of images) {
      expect(rest).toEqual([]) // no destination size: 1:1
      expect(x % CELL_SIZE).toBe(0)
      expect(y % CELL_SIZE).toBe(0)
    }
    expect(ctx.of('fillText')).toHaveLength(2) // the two absent keys show their generic fallback letter
    expect(new Set(ctx.of('fillText').map((c) => c[1]))).toEqual(new Set(['?']))
  })

  it('shows the invalid-manifest fallback in every cell when there is no view', () => {
    const ctx = new RecordingContext()
    drawScene(ctx, null)
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.of('fillText')).toHaveLength(SCENE_COLUMNS * SCENE_ROWS)
  })

  it('shows each family fallback (item, terrain, ui letters) when the images are missing', async () => {
    const ctx = new RecordingContext()
    drawScene(ctx, await loadedView(() => undefined))
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(new Set(ctx.of('fillText').map((c) => c[1]))).toEqual(new Set(['I', 'T', 'U', '?']))
  })

  it('draws a still-loading cell empty, never a stale image', () => {
    const view = new SnapshotLoader(() => new Promise(() => undefined), fixtureUrlFor).mount(snapshot)
    const ctx = new RecordingContext()
    drawCell(ctx, view, 'fixture.rehearsal.gem', 0, 0)
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.of('clearRect')).toHaveLength(1)
  })
})
