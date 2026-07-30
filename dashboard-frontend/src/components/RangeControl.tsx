import { useState } from 'react'
import {
  RANGE_PRESETS,
  DEFAULT_PRESET_ID,
  computePresetRange,
  datetimeLocalToUtcIso,
  utcIsoToDatetimeLocalValue,
} from '@/lib/timeRangePresets'

export interface RangeControlProps {
  sinceIso: string
  untilIso: string
  onRangeChange: (sinceIso: string, untilIso: string) => void
}

export function RangeControl({ sinceIso, untilIso, onRangeChange }: RangeControlProps) {
  // Ephemeral UI-only state (which preset button, if any, is highlighted) — not durable, does not
  // need to survive a remount, mirrors what button was last clicked rather than re-deriving it by
  // comparing sinceIso/untilIso against every preset on every render.
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(DEFAULT_PRESET_ID)

  function handlePresetClick(presetId: string) {
    const range = computePresetRange(presetId, Date.now())
    if (!range) return
    setSelectedPresetId(presetId)
    onRangeChange(range.sinceIso, range.untilIso)
  }

  function handleCustomStartChange(value: string) {
    const iso = datetimeLocalToUtcIso(value)
    if (iso === null) return
    // Lexical string comparison, matching the backend's own bounding convention (Anti-Drift
    // Hazard) — refuse an inverted range rather than silently sending since > until.
    if (iso >= untilIso) return
    setSelectedPresetId(null)
    onRangeChange(iso, untilIso)
  }

  function handleCustomEndChange(value: string) {
    const iso = datetimeLocalToUtcIso(value)
    if (iso === null) return
    if (sinceIso >= iso) return
    setSelectedPresetId(null)
    onRangeChange(sinceIso, iso)
  }

  return (
    <div className="flex flex-wrap items-end gap-3" data-testid="timeline-range-control">
      <div className="flex items-center gap-1" data-testid="timeline-range-presets">
        {RANGE_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            data-testid={`range-preset-${preset.id}`}
            aria-pressed={selectedPresetId === preset.id}
            onClick={() => handlePresetClick(preset.id)}
            className={`px-2 py-1 rounded-md text-[11px] border ${
              selectedPresetId === preset.id
                ? 'bg-accent-blue/15 text-accent-blue border-accent-blue'
                : 'bg-bg-tertiary text-text-secondary border-border'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
      <label className="flex flex-col text-[11px] text-text-secondary gap-0.5">
        Start
        <input
          type="datetime-local"
          data-testid="range-custom-start"
          key={`start-${sinceIso}`}
          defaultValue={utcIsoToDatetimeLocalValue(sinceIso)}
          onChange={(event) => handleCustomStartChange(event.target.value)}
          className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary"
        />
      </label>
      <label className="flex flex-col text-[11px] text-text-secondary gap-0.5">
        End
        <input
          type="datetime-local"
          data-testid="range-custom-end"
          key={`end-${untilIso}`}
          defaultValue={utcIsoToDatetimeLocalValue(untilIso)}
          onChange={(event) => handleCustomEndChange(event.target.value)}
          className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary"
        />
      </label>
    </div>
  )
}
