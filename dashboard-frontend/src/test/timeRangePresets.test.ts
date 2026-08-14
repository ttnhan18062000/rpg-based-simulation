import { describe, it, expect } from 'vitest'
import {
  RANGE_PRESETS,
  DEFAULT_WINDOW_MS,
  computePresetRange,
  datetimeLocalToUtcIso,
  utcIsoToDatetimeLocalValue,
} from '../lib/timeRangePresets'

describe('computePresetRange', () => {
  const nowMs = Date.parse('2026-07-20T12:00:00.000Z')

  for (const preset of RANGE_PRESETS) {
    it(`computes sinceIso/untilIso for preset '${preset.id}'`, () => {
      const range = computePresetRange(preset.id, nowMs)
      expect(range).not.toBeNull()
      expect(range?.sinceIso).toBe(new Date(nowMs - preset.durationMs).toISOString())
      expect(range?.untilIso).toBe(new Date(nowMs).toISOString())
    })
  }

  it('returns null for an unknown preset id', () => {
    expect(computePresetRange('bogus', nowMs)).toBeNull()
  })
})

describe('datetimeLocalToUtcIso', () => {
  it('converts a straightforward same-day datetime-local value to UTC ISO', () => {
    const value = '2026-07-20T12:30'
    expect(datetimeLocalToUtcIso(value)).toBe(new Date(value).toISOString())
  })

  it('converts a late-evening local value that may cross a date boundary in UTC, timezone-independently', () => {
    const value = '2026-07-20T23:45'
    expect(datetimeLocalToUtcIso(value)).toBe(new Date(value).toISOString())
  })

  it('returns null for an empty string', () => {
    expect(datetimeLocalToUtcIso('')).toBeNull()
  })

  it('returns null for a clearly-invalid string, without throwing', () => {
    expect(() => datetimeLocalToUtcIso('not-a-date')).not.toThrow()
    expect(datetimeLocalToUtcIso('not-a-date')).toBeNull()
  })
})

describe('utcIsoToDatetimeLocalValue', () => {
  const iso = '2026-07-20T12:34:56.789Z'

  it('produces a zero-padded YYYY-MM-DDTHH:mm shape', () => {
    const value = utcIsoToDatetimeLocalValue(iso)
    expect(value).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/)
  })

  it('round-trips back to the same instant modulo seconds truncation', () => {
    const localValue = utcIsoToDatetimeLocalValue(iso)
    const roundTripped = datetimeLocalToUtcIso(localValue)
    expect(roundTripped).not.toBeNull()
    const diffMs = Math.abs(Date.parse(roundTripped as string) - Date.parse(iso))
    expect(diffMs).toBeLessThan(60_000)
  })
})

describe('DEFAULT_WINDOW_MS', () => {
  it('equals the 24h preset duration, never a second independent literal', () => {
    expect(DEFAULT_WINDOW_MS).toBe(RANGE_PRESETS.find((p) => p.id === '24h')!.durationMs)
  })
})
