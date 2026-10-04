import { describe, expect, it } from 'vitest'
import { SnapshotLoader } from '../loader'
import { parseManifest } from '../manifest'
import { fixtureManifestText, fixtureUrlFor, fixtureUrls } from '../fixtureSource'
import { bitmap, controlledDecode, manifestWith } from './helpers'

const A = parseManifest(fixtureManifestText)
const B = parseManifest(manifestWith((r) => { r.candidate_manifest_hash = `sha256:${'f'.repeat(64)}`; r.release_id = 'rc-0002' }))
const urlOf = (file: string) => fixtureUrls[file]
const filesOf = (s: typeof A) => [...s.entries.values()].map((e) => e.file)

describe('SnapshotLoader (single generation)', () => {
  it('shows only images that loaded in the view that asked for them', async () => {
    const { decode, pending } = controlledDecode()
    const loader = new SnapshotLoader(decode, urlOf)
    const view = loader.mount(A)
    for (const [, p] of pending) p.resolve(bitmap())
    await view.ready
    expect(filesOf(A).map((f) => view.statusOf(f))).toEqual(['ok', 'ok', 'ok'])
    expect(view.resolve('fixture.rehearsal.gem').kind).toBe('image')
    expect(view.bitmapFor(A.entries.get('fixture.rehearsal.gem')!.file)).toBeDefined()
  })

  it('a late completion is closed, recorded, and never reaches the newer view', async () => {
    const decodes: { url: string; resolve: (b: ReturnType<typeof bitmap>) => void }[] = []
    const loader = new SnapshotLoader(
      (url) => new Promise((resolve) => { decodes.push({ url, resolve }) }),
      urlOf,
    )
    const viewA = loader.mount(A) // three pending decodes: A's
    const viewB = loader.mount(B) // three more: B's
    expect(decodes).toHaveLength(6)
    const aBitmaps = decodes.slice(0, 3).map(() => bitmap())
    const bBitmaps = decodes.slice(3).map(() => bitmap())
    // B finishes first, then A's late completions arrive
    decodes.slice(3).forEach((d, i) => d.resolve(bBitmaps[i]))
    await viewB.ready
    decodes.slice(0, 3).forEach((d, i) => d.resolve(aBitmaps[i]))
    await viewA.ready

    expect(aBitmaps.every((b) => b.closed)).toBe(true) // dropped images are released
    expect(bBitmaps.some((b) => b.closed)).toBe(false)
    expect(loader.dropped).toEqual(filesOf(A).map((file) => ({ generation: A.generation, file })))
    // the older view resolves its files as late; the newer view holds only its own bitmaps
    expect(viewA.resolve('fixture.rehearsal.gem')).toMatchObject({ kind: 'fallback', reason: 'late_result_dropped', family: 'item' })
    for (const file of filesOf(B)) {
      const held = viewB.bitmapFor(file)
      expect(bBitmaps).toContain(held)
      expect(aBitmaps).not.toContain(held)
    }
    expect(loader.current).toBe(viewB)
  })

  it('does not fetch a file the build does not contain and reports it missing', async () => {
    const { decode, calls } = controlledDecode()
    const loader = new SnapshotLoader(decode, (file) => (file === A.entries.get('fixture.rehearsal.gem')!.file ? undefined : fixtureUrlFor(file)))
    const view = loader.mount(A)
    expect(calls).toHaveLength(2)
    expect(view.statusOf(A.entries.get('fixture.rehearsal.gem')!.file)).toBe('missing')
    expect(view.resolve('fixture.rehearsal.gem')).toMatchObject({ kind: 'fallback', reason: 'missing_image' })
  })

  it('reports an undecodable image, and an image of the wrong size, as decode_failed', async () => {
    const { decode, pending } = controlledDecode()
    const loader = new SnapshotLoader(decode, urlOf)
    const view = loader.mount(A)
    const [first, second, third] = [...pending.values()]
    first.reject(new Error('corrupt'))
    second.resolve(bitmap(15, 16)) // not the manifest's 16 x 16
    third.resolve(bitmap())
    await view.ready
    const statuses = filesOf(A).map((f) => view.statusOf(f))
    expect(statuses.filter((s) => s === 'decode_failed')).toHaveLength(2)
    expect(statuses.filter((s) => s === 'ok')).toHaveLength(1)
  })
})
