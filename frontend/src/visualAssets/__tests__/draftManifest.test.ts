import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { asRuntimeSnapshot, parseDraftPreview } from '../draftManifest'
import { draftManifestText } from '../draftSource'
import { ManifestError, parseManifest, slotKey } from '../manifest'
import { pilotManifestText } from '../pilotSource'
import { fixtureManifestText } from '../fixtureSource'

type Raw = Record<string, unknown> & { entries: Record<string, unknown>[] }
const raw = (): Raw => JSON.parse(draftManifestText) as Raw
const codeOf = (parse: (text: string) => unknown, text: string): string => {
  try {
    parse(text)
  } catch (error) {
    if (error instanceof ManifestError) return error.code
    throw error
  }
  throw new Error('expected the manifest to be rejected')
}
const draftCode = (change: (r: Raw) => void) => {
  const r = raw()
  change(r)
  return codeOf(parseDraftPreview, JSON.stringify(r))
}

describe('parseDraftPreview', () => {
  it('parses the committed fixture: the set id, the exact set hash, seven drafts and the forest axis in its declared order', () => {
    const snapshot = parseDraftPreview(draftManifestText)
    expect(snapshot.setId).toBe('fixture-terrain')
    expect(snapshot.draftSetHash).toBe((raw().draft_set_hash as string))
    expect(snapshot.entries.map((e) => [e.visualKey, e.detail])).toEqual([
      ['terrain.desert', null], ['terrain.forest', null], ['terrain.forest', 'bush'], ['terrain.forest', 'tree'], ['terrain.grassland', null], ['terrain.mountain', null], ['terrain.swamp', null],
    ])
    expect(snapshot.details.get('terrain.forest')).toMatchObject({ values: ['plain', 'bush', 'tree'], default: 'plain' })
    expect(snapshot.entries.every((e) => e.scale === 8 && e.width === 128 && e.height === 128)).toBe(true)
    expect(Object.isFrozen(snapshot) && Object.isFrozen(snapshot.entries[0])).toBe(true)
  })

  it('shows the same set hash the Python export wrote, byte for byte, into the manifest it displays', () => {
    const fixtureDir = path.resolve(__dirname, '../__fixtures__/draft')
    expect(parseDraftPreview(readFileSync(path.join(fixtureDir, 'draft_preview_manifest.json'), 'utf8')).draftSetHash).toBe(raw().draft_set_hash)
  })

  it('fills the forest default slot with no detail value and hands the loader a runtime-shaped snapshot keyed by slot', () => {
    const runtime = asRuntimeSnapshot(parseDraftPreview(draftManifestText))
    expect(runtime.generation).toBe(raw().draft_set_hash)
    expect([...runtime.entries.keys()]).toContain(slotKey('terrain.forest', 'plain')) // the default slot, though the entry names no value
    expect(runtime.entries.get(slotKey('terrain.forest', 'plain'))!.detail).toBe('plain')
    expect(runtime.entries.has('terrain.forest')).toBe(false)
    expect(runtime.entries.has('terrain.desert')).toBe(true)
  })

  it.each<[string, (r: Raw) => void, string]>([
    ['an unknown top-level field', (r) => { r.approver = 'x' }, 'unknown_field'],
    ['an unknown entry field', (r) => { r.entries[0].source_path = '/x' }, 'unknown_field'],
    ['a missing set id', (r) => { delete r.set_id }, 'missing_field'],
    ['a missing draft set hash', (r) => { delete r.draft_set_hash }, 'missing_field'],
    ['the wrong record type', (r) => { r.record_type = 'runtime_manifest' }, 'wrong_record_type'],
    ['schema_version 2', (r) => { r.schema_version = 2 }, 'unsupported_version'],
    ['a bad set hash', (r) => { r.draft_set_hash = 'sha1:abc' }, 'invalid_value'],
    ['a file not derived from the pixel hash', (r) => { r.entries[0].file = `${'b'.repeat(64)}.png` }, 'file_not_derived'],
    ['a scale of zero', (r) => { r.entries[0].scale = 0 }, 'invalid_value'],
    ['a scale above 16', (r) => { r.entries[0].scale = 17 }, 'invalid_value'],
    ['a fractional scale', (r) => { r.entries[0].scale = 2.5 }, 'invalid_value'],
    ['a scale that does not divide the preview size', (r) => { r.entries[0].scale = 3 }, 'invalid_value'],
    ['a width that is not a multiple of the scale', (r) => { r.entries[0].width = 130 }, 'invalid_value'],
    ['a preview over the maximum size', (r) => { r.entries[0].width = 1040; r.entries[0].height = 1040 }, 'invalid_value'],
    ['a draft id that is not an intake id', (r) => { r.entries[0].draft_id = 'in-xyz' }, 'invalid_value'],
    ['an undeclared detail value', (r) => { r.entries[2].detail = 'shrub' }, 'detail_mismatch'],
    ['a detail value on a key with no axis', (r) => { r.entries[0].detail = 'bush' }, 'detail_mismatch'],
    ['two entries filling one slot (the default and an explicit default)', (r) => { r.entries[2].detail = 'plain' }, 'duplicate_visual_key'],
    ['unsorted entries', (r) => { r.entries.reverse() }, 'unsorted_entries'],
    ['entries that are not a list', (r) => { (r as Record<string, unknown>).entries = {} }, 'invalid_value'],
  ])('rejects %s', (_name, change, code) => {
    expect(draftCode(change)).toBe(code)
  })

  it('accepts `adopted` only as the literal true (a reference to adopted art), and an explicit null as absent', () => {
    const parsed = (value: unknown) => {
      const r = raw()
      r.entries[0].adopted = value
      return parseDraftPreview(JSON.stringify(r)).entries[0].adopted
    }
    expect(parsed(true)).toBe(true)
    expect(parsed(null)).toBe(false)
    expect(parseDraftPreview(draftManifestText).entries.every((e) => e.adopted === false)).toBe(true)
    for (const bad of [false, 1, 'true', 0, {}]) expect(draftCode((r) => { r.entries[0].adopted = bad }), String(bad)).toBe('invalid_value')
  })

  it('rejects more drafts than a set may hold', () => {
    const entry = raw().entries[0]
    expect(draftCode((r) => { r.entries = Array.from({ length: 257 }, () => ({ ...entry })) })).toBe('too_many_entries')
  })
})

describe('a draft preview manifest and a runtime manifest are mutually unparseable', () => {
  it('the runtime parser refuses the draft manifest and the draft parser refuses runtime manifests', () => {
    expect(() => parseManifest(draftManifestText)).toThrow(ManifestError)
    expect(() => parseDraftPreview(pilotManifestText)).toThrow(ManifestError)
    expect(() => parseDraftPreview(fixtureManifestText)).toThrow(ManifestError)
    expect(codeOf(parseDraftPreview, pilotManifestText)).toMatch(/^(unknown_field|missing_field|wrong_record_type)$/)
  })

  it('still refuses each other after the record type is swapped, because the fields differ', () => {
    const swappedDraft = { ...raw(), record_type: 'runtime_manifest' }
    expect(() => parseManifest(JSON.stringify(swappedDraft))).toThrow(ManifestError)
    const swappedRuntime = { ...JSON.parse(pilotManifestText), record_type: 'draft_preview_manifest' }
    expect(() => parseDraftPreview(JSON.stringify(swappedRuntime))).toThrow(ManifestError)
  })
})
