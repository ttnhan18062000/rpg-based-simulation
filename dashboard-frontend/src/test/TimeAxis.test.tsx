import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TimeAxis } from '../components/TimeAxis'
import { toPercent } from '../components/GanttBar'
import TIME_AXIS_SOURCE from '../components/TimeAxis.tsx?raw'

describe('TimeAxis — reuses GanttBar toPercent, never re-derives it', () => {
  it('imports toPercent from GanttBar rather than redeclaring it', () => {
    expect(TIME_AXIS_SOURCE).toMatch(/import\s*\{\s*toPercent\s*\}\s*from\s*['"]@\/components\/GanttBar['"]/)
    expect(TIME_AXIS_SOURCE).not.toMatch(/function toPercent/)
  })

  it('positions a known tick at exactly the value toPercent returns for that timestamp', () => {
    const windowStartIso = '2026-07-16T00:00:00.000Z'
    const windowEndIso = '2026-07-17T00:00:00.000Z'

    render(<TimeAxis windowStartIso={windowStartIso} windowEndIso={windowEndIso} />)

    const startMs = Date.parse(windowStartIso)
    const endMs = Date.parse(windowEndIso)
    const midTickMs = startMs + ((endMs - startMs) * 3) / 6
    const expectedLeft = toPercent(new Date(midTickMs).toISOString(), windowStartIso, windowEndIso)

    const ticks = screen.getAllByTestId('gantt-time-axis-tick')
    expect(ticks).toHaveLength(7)
    const midTick = ticks[3] as HTMLElement
    expect(midTick.style.left).toBe(`${expectedLeft}%`)
  })

  it('renders the axis root immediately with no hover/interaction required', () => {
    render(<TimeAxis windowStartIso="2026-07-16T00:00:00.000Z" windowEndIso="2026-07-17T00:00:00.000Z" />)
    expect(screen.getByTestId('gantt-time-axis')).toBeInTheDocument()
  })
})
