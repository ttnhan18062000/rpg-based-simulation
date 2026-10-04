import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { ManifestError, MAX_DETAIL_KEYS, MAX_DETAIL_VALUES, MAX_VISUAL_KEYS, parseManifest, slotKey, type ManifestErrorCode } from '../manifest'
import { fixtureManifestText } from '../fixtureSource'
import { fixtureObject, manifestWith } from './helpers'

function codeOf(text: string): ManifestErrorCode {
  try {
    parseManifest(text)
  } catch (error) {
    if (error instanceof ManifestError) return error.code
    throw error
  }
  throw new Error('expected the manifest to be rejected')
}

const HEX_A = 'a'.repeat(64)
const HEX_B = 'b'.repeat(64)
const entry = (key: string, hex = HEX_A, over: Record<string, unknown> = {}) => ({
  visual_key: key, family: 'item', pixel_hash: `pixels-v1:${hex}`, file: `${hex}.png`, width: 16, height: 16, ...over,
})

describe('parseManifest', () => {
  it('parses the committed fixture into a frozen snapshot keyed by the manifest generation', () => {
    const snapshot = parseManifest(fixtureManifestText)
    expect(snapshot.releaseId).toBe('rc-0001')
    expect(snapshot.generation).toBe(fixtureObject().candidate_manifest_hash)
    expect([...snapshot.entries.keys()]).toEqual(['fixture.rehearsal.frame', 'fixture.rehearsal.gem', 'fixture.rehearsal.rock'])
    expect(Object.isFrozen(snapshot)).toBe(true)
    expect(Object.isFrozen(snapshot.entries)).toBe(true)
    const gem = snapshot.entries.get('fixture.rehearsal.gem')!
    expect(Object.isFrozen(gem)).toBe(true)
    expect(gem).toMatchObject({ family: 'item', width: 16, height: 16 })
    expect((snapshot.entries as unknown as { set?: unknown }).set).toBeUndefined() // no mutator is reachable
    expect(() => { (gem as { width: number }).width = 1 }).toThrow(TypeError)
  })

  it.each<[string, (raw: ReturnType<typeof fixtureObject>) => void, ManifestErrorCode]>([
    ['an unknown top-level field', (r) => { r.approver = 'x' }, 'unknown_field'],
    ['an unknown entry field', (r) => { r.entries[0].source_path = '/x' }, 'unknown_field'],
    ['a missing top-level field', (r) => { delete r.registry_hash }, 'missing_field'],
    ['a missing entry field', (r) => { delete r.entries[0].family }, 'missing_field'],
    ['a wrong record_type', (r) => { r.record_type = 'release_candidate_manifest' }, 'wrong_record_type'],
    ['schema_version 2', (r) => { r.schema_version = 2 }, 'unsupported_version'],
    ['schema_version as a string', (r) => { r.schema_version = '1' }, 'unsupported_version'],
    ['fallback_contract_version 2', (r) => { r.fallback_contract_version = 2 }, 'unsupported_version'],
    ['a file not derived from the pixel hash', (r) => { r.entries[0].file = `${HEX_B}.png` }, 'file_not_derived'],
    ['a file that is a path', (r) => { r.entries[0].file = `../${HEX_A}.png` }, 'invalid_value'],
    ['an upper-case extension', (r) => { r.entries[0].file = `${String(r.entries[0].file).slice(0, 64)}.PNG` }, 'invalid_value'],
    ['a bad pixel hash', (r) => { r.entries[0].pixel_hash = 'pixels-v1:xyz' }, 'invalid_value'],
    ['a bad generation hash', (r) => { r.candidate_manifest_hash = 'sha1:abc' }, 'invalid_value'],
    ['a bad visual key', (r) => { r.entries[0].visual_key = 'Not A Key' }, 'invalid_value'],
    ['a width over the maximum', (r) => { r.entries[0].width = 129 }, 'invalid_value'],
    ['a zero height', (r) => { r.entries[0].height = 0 }, 'invalid_value'],
    ['a fractional width', (r) => { r.entries[0].width = 16.5 }, 'invalid_value'],
    ['duplicate visual keys', (r) => { r.entries[1] = { ...r.entries[0] } }, 'duplicate_visual_key'],
    ['unsorted entries', (r) => { r.entries.reverse() }, 'unsorted_entries'],
    ['entries that are not a list', (r) => { (r as Record<string, unknown>).entries = {} }, 'invalid_value'],
  ])('rejects %s', (_name, change, code) => {
    expect(codeOf(manifestWith(change))).toBe(code)
  })

  it('rejects more entries than the registry bound', () => {
    const keys = Array.from({ length: MAX_VISUAL_KEYS + 1 }, (_, i) => `ui.k${String(i).padStart(5, '0')}`)
    const text = manifestWith((r) => { r.entries = keys.map((k) => entry(k)) })
    expect(codeOf(text)).toBe('too_many_entries')
  })

  it('rejects a duplicate JSON object key that JSON.parse would silently collapse', () => {
    const text = fixtureManifestText.replace('"release_id":"rc-0001"', '"release_id":"rc-0001","release_id":"rc-0002"')
    expect(text).not.toBe(fixtureManifestText)
    expect(codeOf(text)).toBe('duplicate_key')
    expect(codeOf(fixtureManifestText.replace('"width":16', '"width":16,"width":17'))).toBe('duplicate_key')
  })

  it.each([['', 'empty'], ['{', 'truncated'], ['[]', 'a list'], ['null', 'null'], [`${fixtureManifestText} x`, 'trailing text'], ['{"a":}', 'bad value']])(
    'rejects text that is not one JSON object: %s',
    (text) => {
      expect(['invalid_json', 'invalid_value']).toContain(codeOf(text))
    },
  )
})

// The same cases `tests/visual_assets/store/unit/test_detail_axis.py` runs through the Python contract: both parsers must decide each one alike.
describe('the detail axis (shared cases with the Python contract)', () => {
  const cases = JSON.parse(readFileSync(path.resolve(__dirname, '../__fixtures__/detail_cases.json'), 'utf8')) as {
    name: string
    accept: boolean
    manifest: unknown
  }[]

  it.each(cases.map((c) => [c.name, c] as const))('%s', (_name, c) => {
    const text = JSON.stringify(c.manifest)
    if (c.accept) expect(() => parseManifest(text)).not.toThrow()
    else expect(() => parseManifest(text)).toThrow(ManifestError)
  })

  it('exposes the declared axis and a slot per detail value, and leaves a key without an axis keyed by its own name', () => {
    const accepted = cases.find((c) => c.name === 'a manifest with a detail axis and per-slot entries')!
    const snapshot = parseManifest(JSON.stringify(accepted.manifest))
    expect([...snapshot.entries.keys()]).toEqual([slotKey('ui.a', 'bush'), slotKey('ui.a', 'plain'), 'ui.b'])
    expect(snapshot.details.get('ui.a')).toMatchObject({ values: ['bush', 'plain'], default: 'plain' })
    expect(snapshot.entries.get(slotKey('ui.a', 'bush'))!.detail).toBe('bush')
    expect(snapshot.entries.get('ui.b')!.detail).toBeNull()
    expect(Object.isFrozen(snapshot.details)).toBe(true)
    expect((snapshot.details as unknown as { set?: unknown }).set).toBeUndefined()
  })

  it('parses the committed pilot manifest with no details and one slot keyed by its visual key', () => {
    const snapshot = parseManifest(readFileSync(path.resolve(__dirname, '../__fixtures__/pilot/runtime_manifest.json'), 'utf8'))
    expect(snapshot.details.size).toBe(0)
    expect(snapshot.entries.get('terrain.forest')!.detail).toBeNull()
  })

  it('mirrors the Python bounds', () => {
    expect([MAX_DETAIL_VALUES, MAX_DETAIL_KEYS]).toEqual([16, 64])
  })
})
