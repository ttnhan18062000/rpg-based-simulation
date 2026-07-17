import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../App'
import { useRunsPolling, fetchRunTimeline, type RunSummary, type RunTimeline } from '../api'

vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api')>()
  return {
    ...actual,
    useRunsPolling: vi.fn(),
    fetchRunTimeline: vi.fn(),
  }
})

const mockedUseRunsPolling = vi.mocked(useRunsPolling)
const mockedFetchRunTimeline = vi.mocked(fetchRunTimeline)

function navTargetRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-nav-target',
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: '2026-07-16T10:00:00Z',
    end_ts: '2026-07-16T10:05:00Z',
    duration_s: 300,
    agent_count: 2,
    is_inferred_active: false,
    inferred_start_ts: null,
    ...overrides,
  }
}

function navTargetTimeline(): RunTimeline {
  return {
    run_id: 'run-nav-target',
    is_live: false,
    entries: [],
    live_tail: [],
    files_touched: [],
  }
}

describe('App', () => {
  beforeEach(() => {
    mockedUseRunsPolling.mockReset()
    mockedUseRunsPolling.mockReturnValue({ runs: [], isLoading: false, error: null })
    mockedFetchRunTimeline.mockReset()
    mockedFetchRunTimeline.mockResolvedValue(navTargetTimeline())
  })

  it('lands on the RecentActivityGantt view by default', () => {
    render(<App />)

    expect(screen.getByTestId('recent-activity-gantt')).toBeInTheDocument()
    expect(screen.queryByText('Tickets view coming soon.')).not.toBeInTheDocument()
    expect(screen.queryByTestId('replay-timeline-view')).not.toBeInTheDocument()
  })

  it('App-shell scaffold smoke test: Replay tab renders a "select a run" placeholder with no run selected, Tickets remains its unchanged stub', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Tickets' }))
    expect(screen.getByText('Tickets view coming soon.')).toBeInTheDocument()
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Replay' }))
    expect(screen.queryByText('Tickets view coming soon.')).not.toBeInTheDocument()
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()
    expect(screen.queryByTestId('replay-timeline-view')).not.toBeInTheDocument()
    expect(
      screen.getByText('Select a run from Recent Activity to view its replay.'),
    ).toBeInTheDocument()
    expect(mockedFetchRunTimeline).not.toHaveBeenCalled()
  })

  it('Gantt row click navigates to that run\'s Replay timeline, scoped to that run_id', async () => {
    const user = userEvent.setup()
    mockedUseRunsPolling.mockReturnValue({ runs: [navTargetRun()], isLoading: false, error: null })

    render(<App />)

    const bar = document.querySelector('[data-run-id="run-nav-target"]')!
    const row = bar.closest('.relative.h-6')!
    await user.click(row)

    expect(await screen.findByTestId('replay-timeline-view')).toBeInTheDocument()
    expect(screen.getByText('run-nav-target')).toBeInTheDocument()
    expect(mockedFetchRunTimeline).toHaveBeenCalledWith('run-nav-target')
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()
  })
})
