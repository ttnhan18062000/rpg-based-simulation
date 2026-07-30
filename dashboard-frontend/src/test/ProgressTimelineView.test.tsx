import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ProgressTimelineView } from '@/views/ProgressTimelineView'
import { useRunsPolling, useRunTimelinesPolling, useGlossary } from '@/api'

let capturedProps: Record<string, unknown> = {}

vi.mock('echarts-for-react/lib/core', () => ({
  default: vi.fn((props: Record<string, unknown>) => {
    capturedProps = props
    return <div data-testid="mocked-echarts" />
  }),
}))

vi.mock('@/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api')>()
  return {
    ...actual,
    useRunsPolling: vi.fn(),
    useRunTimelinesPolling: vi.fn(),
    useGlossary: vi.fn(),
  }
})

const mockedUseRunsPolling = vi.mocked(useRunsPolling)
const mockedUseRunTimelinesPolling = vi.mocked(useRunTimelinesPolling)
const mockedUseGlossary = vi.mocked(useGlossary)

describe('ProgressTimelineView', () => {
  beforeEach(() => {
    capturedProps = {}
    mockedUseRunsPolling.mockReset()
    mockedUseRunsPolling.mockReturnValue({ runs: [], isLoading: false, error: null })
    mockedUseRunTimelinesPolling.mockReset()
    mockedUseRunTimelinesPolling.mockReturnValue({ entriesByRun: {}, isLoading: false, error: null })
    mockedUseGlossary.mockReset()
    mockedUseGlossary.mockReturnValue({})
  })

  it('renders exactly one ReactEChartsCore instance with two dataZoom entries (inside + slider)', () => {
    render(<ProgressTimelineView onSelectRun={vi.fn()} />)

    expect(screen.getAllByTestId('mocked-echarts')).toHaveLength(1)
    const option = capturedProps.option as { dataZoom: Array<{ type: string }> }
    expect(option.dataZoom).toHaveLength(2)
    expect(option.dataZoom.map((z) => z.type).sort()).toEqual(['inside', 'slider'])
  })

  it('does not wire any datazoom/dataZoom onEvents handler that could trigger a network call', () => {
    render(<ProgressTimelineView onSelectRun={vi.fn()} />)

    const onEvents = capturedProps.onEvents as Record<string, unknown>
    expect(Object.keys(onEvents)).not.toContain('datazoom')
    expect(Object.keys(onEvents)).not.toContain('dataZoom')
  })

  it('row click navigates via onSelectRun with the clicked segment run_id', () => {
    const onSelectRun = vi.fn()
    render(<ProgressTimelineView onSelectRun={onSelectRun} />)

    const onEvents = capturedProps.onEvents as { click: (params: { data?: { runId?: string } }) => void }
    onEvents.click({ data: { runId: 'run-nav-target' } })

    expect(onSelectRun).toHaveBeenCalledWith('run-nav-target')
  })

  it('renders data-testid="progress-timeline-view" on the root', () => {
    render(<ProgressTimelineView onSelectRun={vi.fn()} />)

    expect(screen.getByTestId('progress-timeline-view')).toBeInTheDocument()
  })

  describe('range-control integration', () => {
    const fixedNowIso = '2026-07-20T12:00:00.000Z'

    beforeEach(() => {
      vi.useFakeTimers()
      vi.setSystemTime(new Date(fixedNowIso))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('default mount reproduces now-24h to now bit-for-bit (AC #3)', () => {
      render(<ProgressTimelineView onSelectRun={vi.fn()} />)

      const expectedSince = new Date(Date.parse(fixedNowIso) - 24 * 60 * 60 * 1000).toISOString()
      expect(mockedUseRunsPolling).toHaveBeenLastCalledWith(expectedSince)
      expect(mockedUseRunTimelinesPolling).toHaveBeenLastCalledWith(expectedSince, 5000, fixedNowIso)
    })

    it('quick-range preset click updates the bounded fetch, not just the chart (AC #1)', () => {
      render(<ProgressTimelineView onSelectRun={vi.fn()} />)

      fireEvent.click(screen.getByTestId('range-preset-1h'))

      const expectedSince = new Date(Date.parse(fixedNowIso) - 60 * 60 * 1000).toISOString()
      expect(mockedUseRunTimelinesPolling).toHaveBeenLastCalledWith(expectedSince, 5000, fixedNowIso)
    })

    it('custom picker change triggers a refetch bounded by the exact custom values (AC #2)', () => {
      render(<ProgressTimelineView onSelectRun={vi.fn()} />)

      fireEvent.change(screen.getByTestId('range-custom-start'), {
        target: { value: '2026-07-19T08:00' },
      })

      const lastCall = mockedUseRunTimelinesPolling.mock.calls.at(-1)
      expect(lastCall?.[0]).toBe(new Date('2026-07-19T08:00').toISOString())
      expect(lastCall?.[2]).toBe(fixedNowIso)
    })

    it('dataZoom stays independent of range-control changes (AC #4)', () => {
      render(<ProgressTimelineView onSelectRun={vi.fn()} />)

      fireEvent.click(screen.getByTestId('range-preset-1h'))

      const option = capturedProps.option as { dataZoom: Array<{ type: string }> }
      expect(option.dataZoom).toHaveLength(2)
      expect(option.dataZoom.map((z) => z.type).sort()).toEqual(['inside', 'slider'])
      expect(option.dataZoom.every((z) => !('start' in z) && !('end' in z))).toBe(true)

      const onEvents = capturedProps.onEvents as Record<string, unknown>
      expect(Object.keys(onEvents)).not.toContain('datazoom')
      expect(Object.keys(onEvents)).not.toContain('dataZoom')
    })

    it('range control renders above the chart', () => {
      render(<ProgressTimelineView onSelectRun={vi.fn()} />)

      expect(screen.getByTestId('timeline-range-control')).toBeInTheDocument()
      expect(screen.getAllByTestId('mocked-echarts')).toHaveLength(1)
    })
  })
})
