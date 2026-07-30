import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
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
})
