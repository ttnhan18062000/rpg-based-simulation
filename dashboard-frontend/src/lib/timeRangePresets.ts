export interface RangePreset {
  id: string
  label: string
  durationMs: number
}

export const RANGE_PRESETS: RangePreset[] = [
  { id: '1h', label: '1h', durationMs: 60 * 60 * 1000 },
  { id: '6h', label: '6h', durationMs: 6 * 60 * 60 * 1000 },
  { id: '24h', label: '24h', durationMs: 24 * 60 * 60 * 1000 },
  { id: '7d', label: '7d', durationMs: 7 * 24 * 60 * 60 * 1000 },
]

// Single source of truth for "today's default window" (previously ProgressTimelineView.tsx's own
// local SINCE_WINDOW_MS = 24 * 60 * 60 * 1000 literal). Both the initial-mount default AND the
// "24h" preset button MUST read this same constant/preset entry — never a second, independently
// typed 24h literal (Anti-Drift Hazard from investigation.md).
export const DEFAULT_PRESET_ID = '24h'
const DEFAULT_PRESET = RANGE_PRESETS.find((p) => p.id === DEFAULT_PRESET_ID)
if (!DEFAULT_PRESET) {
  throw new Error(`RANGE_PRESETS is missing the default preset id ${DEFAULT_PRESET_ID}`)
}
export const DEFAULT_WINDOW_MS = DEFAULT_PRESET.durationMs

export function computePresetRange(
  presetId: string,
  nowMs: number,
): { sinceIso: string; untilIso: string } | null {
  const preset = RANGE_PRESETS.find((p) => p.id === presetId)
  if (!preset) return null
  return {
    sinceIso: new Date(nowMs - preset.durationMs).toISOString(),
    untilIso: new Date(nowMs).toISOString(),
  }
}

// Converts an <input type="datetime-local"> value (naive local time, "YYYY-MM-DDTHH:mm", no
// seconds, no timezone) to a UTC ISO 8601 string matching the backend's zero-padded
// lexical-comparison convention. `new Date(value)` interprets the naive string in the browser's
// local timezone; `.toISOString()` re-renders it as zero-padded UTC. Returns null for an empty or
// unparseable value (e.g. the input was cleared) rather than throwing or emitting "Invalid Date".
export function datetimeLocalToUtcIso(value: string): string | null {
  if (!value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

// Inverse of datetimeLocalToUtcIso, for populating an <input type="datetime-local">'s displayed
// value from a UTC ISO string. Renders in the browser's local time, truncated to minutes (matching
// the input's own minute-granularity default).
export function utcIsoToDatetimeLocalValue(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
