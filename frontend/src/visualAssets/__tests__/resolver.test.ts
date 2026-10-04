import { describe, expect, it, vi } from 'vitest'
import { parseManifest } from '../manifest'
import { fixtureManifestText, fixtureUrlFor } from '../fixtureSource'
import { resolveVisual } from '../resolver'

const snapshot = parseManifest(fixtureManifestText)
const ctx = { urlFor: fixtureUrlFor }

describe('resolveVisual', () => {
  it('returns the build URL, the logical size and the snapshot generation for every key the manifest has', () => {
    for (const key of snapshot.entries.keys()) {
      const result = resolveVisual(snapshot, key, ctx)
      expect(result).toMatchObject({ kind: 'image', visualKey: key, width: 16, height: 16, generation: snapshot.generation })
      expect(result.kind === 'image' && result.url).toBe(fixtureUrlFor(snapshot.entries.get(key)!.file))
    }
  })

  it('answers an unknown key with the unknown_key fallback and no lookup, fetch or registration', () => {
    const urlFor = vi.fn(fixtureUrlFor)
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const before = snapshot.entries.size
    const result = resolveVisual(snapshot, 'fixture.rehearsal.nothing', { urlFor })
    expect(result).toEqual({ kind: 'fallback', visualKey: 'fixture.rehearsal.nothing', family: null, reason: 'unknown_key' })
    expect(urlFor).not.toHaveBeenCalled()
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(snapshot.entries.size).toBe(before)
    expect(snapshot.entries.has('fixture.rehearsal.nothing')).toBe(false)
    fetchSpy.mockRestore()
  })

  it('never resolves prototype-chain names or path-like keys', () => {
    for (const key of ['__proto__', 'constructor', 'toString', '../etc/passwd', 'https://example.org/x.png', '']) {
      expect(resolveVisual(snapshot, key, ctx)).toMatchObject({ kind: 'fallback', reason: 'unknown_key' })
    }
  })

  it('reports an image the build does not contain as missing_image', () => {
    expect(resolveVisual(snapshot, 'fixture.rehearsal.gem', { urlFor: () => undefined })).toEqual({
      kind: 'fallback', visualKey: 'fixture.rehearsal.gem', family: 'item', reason: 'missing_image',
    })
  })

  it.each([['missing', 'missing_image'], ['decode_failed', 'decode_failed'], ['late', 'late_result_dropped']] as const)(
    'maps the load status %s to the %s fallback and keeps the family',
    (status, reason) => {
      expect(resolveVisual(snapshot, 'fixture.rehearsal.rock', { ...ctx, statusOf: () => status })).toEqual({
        kind: 'fallback', visualKey: 'fixture.rehearsal.rock', family: 'terrain', reason,
      })
    },
  )

  it('treats an ok status like no status', () => {
    expect(resolveVisual(snapshot, 'fixture.rehearsal.rock', { ...ctx, statusOf: () => 'ok' }).kind).toBe('image')
  })

  it('answers every key with manifest_invalid when there is no valid snapshot', () => {
    expect(resolveVisual(null, 'fixture.rehearsal.gem', ctx)).toEqual({ kind: 'fallback', visualKey: 'fixture.rehearsal.gem', family: null, reason: 'manifest_invalid' })
  })
})
