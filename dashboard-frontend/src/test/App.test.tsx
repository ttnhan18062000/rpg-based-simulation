import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../App'
import {
  useRunsPolling,
  fetchRunTimeline,
  type RunSummary,
  type RunTimeline,
  type TicketSummary,
} from '../api'

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

// TicketsView calls the real fetchTickets (only useRunsPolling/fetchRunTimeline
// are mocked above), which issues an actual fetch() — must be stubbed whenever
// the Tickets tab is activated in a test.
function ticketWithRun(runId: string): TicketSummary {
  return {
    ticket_id: 'TCK-20260716-NAV',
    title: 'Nav-target ticket',
    tier: 'standard',
    ticket_type: 'feature',
    priority: 'P2',
    layer: 'observability',
    status: 'active',
    workflow_status: 'OPEN',
    tags: [],
    date: '2026-07-16',
    lifecycle_state: 'inprogress',
    matching_runs: [{ run_id: runId, start_ts: '2026-07-16T10:00:00Z', end_ts: null, final_status: 'DONE' }],
  }
}

function mockTicketsFetch(items: TicketSummary[]) {
  const body = { items, total_count: items.length, facets: { tiers: [], layers: [], statuses: [], priorities: [], tags: [] } }
  const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => body })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

function mockStatsFetch() {
  const agentBody = {
    run_summary: { total: 1, done_count: 1, gate_fail_count: 0, avg_duration_min: 1, avg_agents: 1, total_agent_calls: 1 },
    gate_failure_breakdown: {},
    reason_code_breakdown: {},
    tag_breakdown_subsystem: {},
    tag_breakdown_skill: {},
    tier_distribution: {},
    agent_status_distribution: {},
    phase_status_distribution: {},
    spend_proxy_by_phase: {},
    spend_proxy_by_agent: {},
    summary_quality: { empty_summaries_current: 0, legacy_event_count: 0, long_summaries: 0 },
    slow_runs: [],
    outliers: { duration_s: [], cost_proxy_score: [] },
  }
  const ticketBody = {
    scanned_files: 1,
    included_tickets: 1,
    skipped: {},
    velocity: { by_day: {}, by_week: {}, unparseable_rows: 0 },
    distribution: { tier: {}, ticket_type: {}, priority: {}, layer: {}, layer_by_tier: {} },
    artifact_completeness: { complete_count: 1, incomplete_count: 0, total_checked: 1, incomplete: [] },
  }
  const mockFetch = vi.fn((url: string) => {
    const body = url.includes('agent-monitoring') ? agentBody : ticketBody
    return Promise.resolve({ ok: true, json: async () => body })
  })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

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

  it('header wraps and relaxes fixed height at narrow widths', () => {
    const { container } = render(<App />)

    const header = container.querySelector('header')!
    expect(header.className).toContain('flex-wrap')
    expect(header.className).toContain('sm:h-14')
    expect(header.className).not.toMatch(/(?<!sm:)\bh-14\b/)
  })

  it('lands on the RecentActivityGantt view by default', () => {
    render(<App />)

    expect(screen.getByTestId('recent-activity-gantt')).toBeInTheDocument()
    expect(screen.queryByTestId('tickets-view')).not.toBeInTheDocument()
    expect(screen.queryByTestId('replay-timeline-view')).not.toBeInTheDocument()
  })

  it('App-shell scaffold smoke test: Tickets tab renders the real TicketsView, other tabs unaffected', async () => {
    mockTicketsFetch([])
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Tickets' }))
    expect(await screen.findByTestId('tickets-view')).toBeInTheDocument()
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Recent Activity' }))
    expect(screen.getByTestId('recent-activity-gantt')).toBeInTheDocument()
    expect(screen.queryByTestId('tickets-view')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Replay' }))
    expect(screen.queryByTestId('tickets-view')).not.toBeInTheDocument()
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()
    expect(screen.queryByTestId('replay-timeline-view')).not.toBeInTheDocument()
    expect(
      screen.getByText('Select a run from Recent Activity to view its replay.'),
    ).toBeInTheDocument()
    expect(mockedFetchRunTimeline).not.toHaveBeenCalled()
  })

  it("row-link navigates to that row's Replay timeline via the existing App navigation state", async () => {
    mockTicketsFetch([ticketWithRun('run-nav-target')])
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Tickets' }))
    await screen.findByTestId('tickets-view')

    const link = await screen.findByTestId('linked-run-link-TCK-20260716-NAV-run-nav-target')
    await user.click(link)

    expect(await screen.findByTestId('replay-timeline-view')).toBeInTheDocument()
    expect(mockedFetchRunTimeline).toHaveBeenCalledWith('run-nav-target')
    expect(screen.queryByTestId('tickets-view')).not.toBeInTheDocument()
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

  it('Stats tab renders the real StatsView, other tabs unaffected', async () => {
    mockStatsFetch()
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Stats' }))
    expect(await screen.findByTestId('stats-view')).toBeInTheDocument()
    expect(screen.queryByTestId('recent-activity-gantt')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Recent Activity' }))
    expect(screen.getByTestId('recent-activity-gantt')).toBeInTheDocument()
    expect(screen.queryByTestId('stats-view')).not.toBeInTheDocument()
  })
})
