import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { RangeControl } from '../components/RangeControl'
import { RANGE_PRESETS, computePresetRange } from '../lib/timeRangePresets'

describe('RangeControl', () => {
  const fixedNowIso = '2026-07-20T12:00:00.000Z'

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(fixedNowIso))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  for (const preset of RANGE_PRESETS) {
    it(`clicking the ${preset.label} preset button calls onRangeChange with now-${preset.label} to now`, () => {
      const onRangeChange = vi.fn()
      render(
        <RangeControl
          sinceIso="2026-07-19T12:00:00.000Z"
          untilIso={fixedNowIso}
          onRangeChange={onRangeChange}
        />,
      )

      fireEvent.click(screen.getByTestId(`range-preset-${preset.id}`))

      const expected = computePresetRange(preset.id, Date.now())
      expect(expected).not.toBeNull()
      expect(onRangeChange).toHaveBeenCalledWith(expected?.sinceIso, expected?.untilIso)
    })
  }

  it('custom start/end inputs emit zero-padded UTC ISO strings on change', () => {
    const onRangeChange = vi.fn()
    render(
      <RangeControl
        sinceIso="2026-07-19T12:00:00.000Z"
        untilIso={fixedNowIso}
        onRangeChange={onRangeChange}
      />,
    )

    fireEvent.change(screen.getByTestId('range-custom-start'), {
      target: { value: '2026-07-19T23:30' },
    })

    expect(onRangeChange).toHaveBeenCalledTimes(1)
    const [calledSince] = onRangeChange.mock.calls[0]
    expect(calledSince).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/)
  })

  it('selecting a preset then editing a custom input clears the preset highlight', () => {
    const onRangeChange = vi.fn()
    render(
      <RangeControl
        sinceIso="2026-07-19T12:00:00.000Z"
        untilIso={fixedNowIso}
        onRangeChange={onRangeChange}
      />,
    )

    fireEvent.click(screen.getByTestId('range-preset-24h'))
    expect(screen.getByTestId('range-preset-24h')).toHaveAttribute('aria-pressed', 'true')

    fireEvent.change(screen.getByTestId('range-custom-start'), {
      target: { value: '2026-07-19T08:00' },
    })

    for (const preset of RANGE_PRESETS) {
      expect(screen.getByTestId(`range-preset-${preset.id}`)).toHaveAttribute('aria-pressed', 'false')
    }
  })

  it('rejects an inverted custom range (end before start)', () => {
    const onRangeChange = vi.fn()
    render(
      <RangeControl
        sinceIso="2026-07-19T12:00:00.000Z"
        untilIso={fixedNowIso}
        onRangeChange={onRangeChange}
      />,
    )

    fireEvent.change(screen.getByTestId('range-custom-end'), {
      target: { value: '2026-07-19T06:00' },
    })

    expect(onRangeChange).not.toHaveBeenCalled()
  })
})
