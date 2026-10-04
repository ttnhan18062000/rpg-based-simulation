// AM5-W09 / AM-C06 rollback drill (TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK), under Profile A (ADR D8): a release is a whole frontend build.
// "Previous release" = the previous build's runtime fixture set (the synthetic rehearsal export, catalog "rehearsal"); "new" = the pilot export (pilot/rc-0001).
// Old client + new release is defence in depth against a mis-deploy: under Profile A an old client never receives a new manifest, because the manifest is bound to its build.
// Whatever the combination, a cell shows its role or its fallback, never a mixed snapshot.
import { describe, expect, it } from 'vitest'
import { CELL_SIZE } from '../cell'
import { fixtureManifestText, fixtureUrlFor } from '../fixtureSource'
import { SnapshotLoader, type Bitmap, type Decode } from '../loader'
import { parseManifest } from '../manifest'
import { pilotManifestText, pilotUrlFor } from '../pilotSource'
import { PILOT_KEY, drawPilotScene, terrainAt, FOREST_CODE, PILOT_COLUMNS, PILOT_ROWS } from '../pilotScene'
import { SCENE_COLUMNS, SCENE_ROWS, drawScene } from '../scene'
import { bitmap } from './helpers'
import { Recorder } from './pilotHelpers'

const FILL = '#1b3a1b'
const FOREST_CELLS = Array.from({ length: PILOT_ROWS * PILOT_COLUMNS }, (_, i) => terrainAt(i % PILOT_COLUMNS, Math.floor(i / PILOT_COLUMNS))).filter((c) => c === FOREST_CODE).length

const previousBuild = { name: 'previous build (rehearsal export)', manifestText: fixtureManifestText, urlFor: fixtureUrlFor }
const newBuild = { name: 'new build (pilot/rc-0001)', manifestText: pilotManifestText, urlFor: pilotUrlFor }

async function view(build: { manifestText: string; urlFor: (f: string) => string | undefined }, decode: Decode = async () => bitmap()) {
  const v = new SnapshotLoader(decode, build.urlFor).mount(parseManifest(build.manifestText))
  await v.ready
  return v
}

describe('rollback drill: every combination renders the role or its fallback', () => {
  it('baseline: new client + new release draws the tile on every forest cell', async () => {
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await view(newBuild), 'image')
    expect(ctx.of('drawImage')).toHaveLength(FOREST_CELLS)
  })

  it('new client + old release: the key is not in the previous release, so every forest cell shows the flat fill', async () => {
    expect(parseManifest(previousBuild.manifestText).entries.has(PILOT_KEY)).toBe(false)
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await view(previousBuild), 'image')
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.fills.filter((c) => c === FILL).length).toBeGreaterThanOrEqual(FOREST_CELLS)
  })

  it('old client + new release (a mis-deploy): the old rehearsal scene knows none of the pilot keys, so it shows only its typed fallbacks and no image', async () => {
    const ctx = new Recorder()
    drawScene(ctx as never, await view(newBuild))
    expect(ctx.of('drawImage')).toHaveLength(0)
    const letters = ctx.of('fillText').map((c) => c[1])
    expect(letters).toHaveLength(SCENE_COLUMNS * SCENE_ROWS)
    expect(new Set(letters)).toEqual(new Set(['?'])) // every cell is the generic "unknown visual" fallback, never a half-drawn image
  })

  it('recall: a release with the key removed shows the flat fill on every forest cell', async () => {
    const raw = JSON.parse(pilotManifestText) as { entries: unknown[] }
    raw.entries = []
    const recalled = { manifestText: JSON.stringify(raw), urlFor: pilotUrlFor }
    const ctx = new Recorder()
    drawPilotScene(ctx.asCtx(), await view(recalled), 'image')
    expect(ctx.of('drawImage')).toHaveLength(0)
    expect(ctx.fills.filter((c) => c === FILL).length).toBeGreaterThanOrEqual(FOREST_CELLS)
  })

  it('the three combinations never draw a pixel of the other release: a cell is the role or its fallback', async () => {
    for (const [client, release] of [['new', previousBuild], ['old', newBuild]] as const) {
      const ctx = new Recorder()
      if (client === 'new') drawPilotScene(ctx.asCtx(), await view(release), 'image')
      else drawScene(ctx as never, await view(release))
      expect(ctx.of('drawImage'), `${client} client + ${release.name}`).toHaveLength(0)
    }
    expect(CELL_SIZE).toBe(16)
  })
})

describe('rollback drill: a mixed snapshot is never accepted', () => {
  type Tagged = Bitmap & { from: string }
  const tagged = (url: string): Tagged => ({ ...bitmap(), from: url })

  it('switching release mid-load: the superseded release\'s late images are dropped and never drawn', async () => {
    const releases: { url: string; release: () => void }[] = []
    const decode: Decode = (url) => new Promise<Bitmap>((resolve) => releases.push({ url, release: () => resolve(tagged(url)) }))
    const loader = new SnapshotLoader(decode, (file) => fixtureUrlFor(file) ?? pilotUrlFor(file))
    const previous = loader.mount(parseManifest(previousBuild.manifestText))
    const current = loader.mount(parseManifest(newBuild.manifestText)) // the redeploy: supersedes the previous release while its images are still loading
    releases.reverse().forEach((r) => r.release()) // late, in the opposite order
    await Promise.all([previous.ready, current.ready])

    expect(loader.dropped.length).toBeGreaterThan(0)
    expect(new Set(loader.dropped.map((d) => d.generation))).toEqual(new Set([previous.snapshot.generation]))
    const pilotUrl = pilotUrlFor(parseManifest(newBuild.manifestText).entries.get(PILOT_KEY)!.file)

    const fresh = new Recorder()
    drawPilotScene(fresh.asCtx(), current, 'image')
    const drawn = fresh.of('drawImage').map((c) => (c[1] as Tagged).from)
    expect(drawn).toHaveLength(FOREST_CELLS)
    expect(new Set(drawn)).toEqual(new Set([pilotUrl])) // only the current release's own image

    const stale = new Recorder()
    drawPilotScene(stale.asCtx(), previous, 'image') // drawing with the superseded view shows no image at all, not the late ones
    expect(stale.of('drawImage')).toHaveLength(0)
    for (const file of parseManifest(previousBuild.manifestText).entries.values()) expect(previous.bitmapFor(file.file)).toBeUndefined()
  })
})
