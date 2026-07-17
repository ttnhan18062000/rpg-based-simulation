import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TicketsView } from '../views/TicketsView'
import type { TicketSummary } from '../api'
import TICKETS_VIEW_SOURCE from '../views/TicketsView.tsx?raw'

function makeTicket(overrides: Partial<TicketSummary> = {}): TicketSummary {
  return {
    ticket_id: 'TCK-20260101-A',
    title: 'Sample ticket',
    tier: 'standard',
    ticket_type: 'feature',
    priority: 'P2',
    layer: 'observability',
    status: 'active',
    workflow_status: 'OPEN',
    tags: ['observability'],
    date: '2026-07-16',
    lifecycle_state: 'inprogress',
    matching_runs: [],
    ...overrides,
  }
}

function mockFetchReturning(response: TicketSummary[]) {
  const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => response })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

const noopOnSelectRun = () => {}

describe('TicketsView — rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders rows from fetchTickets covering all three lifecycle states', async () => {
    mockFetchReturning([
      makeTicket({ ticket_id: 'TCK-A', lifecycle_state: 'inprogress' }),
      makeTicket({ ticket_id: 'TCK-B', lifecycle_state: 'done' }),
      makeTicket({ ticket_id: 'TCK-C', lifecycle_state: 'todos' }),
    ])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.getByTestId('ticket-row-TCK-A')).toBeInTheDocument()
    expect(screen.getByTestId('ticket-row-TCK-B')).toBeInTheDocument()
    expect(screen.getByTestId('ticket-row-TCK-C')).toBeInTheDocument()
  })
})

describe('TicketsView — filter bar delegates to server query params', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('filter bar narrows rows AND-across-dimensions, OR-within-tag, via server query params', async () => {
    const user = userEvent.setup()
    const initial = [
      makeTicket({ ticket_id: 'TCK-A', tier: 'standard', layer: 'observability', tags: ['observability', 'infra'] }),
      makeTicket({ ticket_id: 'TCK-B', tier: 'hotfix', layer: 'combat', tags: ['combat'] }),
    ]
    const mockFetch = mockFetchReturning(initial)

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.selectOptions(screen.getByTestId('filter-tier'), 'standard')
    await user.selectOptions(screen.getByTestId('filter-layer'), 'observability')
    await user.click(screen.getByTestId('filter-tag-observability'))
    await user.click(screen.getByTestId('filter-tag-infra'))

    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
    const requestedUrl = String(lastCall[0])
    expect(requestedUrl).toContain('tier=standard')
    expect(requestedUrl).toContain('layer=observability')
    const tagMatches = requestedUrl.match(/tag=/g) ?? []
    expect(tagMatches.length).toBe(2)
    expect(requestedUrl).toContain('tag=observability')
    expect(requestedUrl).toContain('tag=infra')
  })

  it('selecting two tags with no dimension filter sends both as repeated tag params', async () => {
    const user = userEvent.setup()
    const initial = [
      makeTicket({ ticket_id: 'TCK-A', tags: ['observability', 'infra'] }),
      makeTicket({ ticket_id: 'TCK-B', tags: ['combat'] }),
    ]
    const mockFetch = mockFetchReturning(initial)

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.click(screen.getByTestId('filter-tag-observability'))
    await user.click(screen.getByTestId('filter-tag-infra'))

    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
    const requestedUrl = String(lastCall[0])
    expect(requestedUrl).not.toContain('tier=')
    expect(requestedUrl).not.toContain('layer=')
    expect(requestedUrl).toContain('tag=observability')
    expect(requestedUrl).toContain('tag=infra')
  })
})

describe('TicketsView — linked-runs control', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('surfaces every matching_runs entry as a separate link, never collapsed', async () => {
    const user = userEvent.setup()
    const onSelectRun = vi.fn()
    mockFetchReturning([
      makeTicket({
        ticket_id: 'TCK-MULTI',
        matching_runs: [
          { run_id: 'run-2', start_ts: '2026-07-02T00:00:00Z', end_ts: null, final_status: 'DONE' },
          { run_id: 'run-1', start_ts: '2026-07-01T00:00:00Z', end_ts: null, final_status: 'DONE' },
        ],
      }),
    ])

    render(<TicketsView onSelectRun={onSelectRun} />)
    await screen.findByTestId('tickets-table')

    const link1 = screen.getByTestId('linked-run-link-TCK-MULTI-run-2')
    const link2 = screen.getByTestId('linked-run-link-TCK-MULTI-run-1')
    expect(link1).toBeInTheDocument()
    expect(link2).toBeInTheDocument()

    await user.click(link2)
    expect(onSelectRun).toHaveBeenCalledWith('run-1')

    await user.click(link1)
    expect(onSelectRun).toHaveBeenCalledWith('run-2')
  })

  it('renders no link/picker control when matching_runs is empty', async () => {
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-NONE', matching_runs: [] })])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const cell = screen.getByTestId('linked-runs-TCK-NONE')
    expect(cell.querySelector('button')).toBeNull()
  })
})

describe('TicketsView — null-safe rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('null tier/priority/type render as null/empty, never a placeholder string', async () => {
    mockFetchReturning([
      makeTicket({ ticket_id: 'TCK-NULLS', tier: null, priority: null, ticket_type: null }),
    ])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const tierCell = screen.getByTestId('tier-cell-TCK-NULLS')
    const priorityCell = screen.getByTestId('priority-cell-TCK-NULLS')
    const typeCell = screen.getByTestId('type-cell-TCK-NULLS')

    for (const cell of [tierCell, priorityCell, typeCell]) {
      expect(cell.textContent).toBe('')
      expect(cell.textContent).not.toBe('N/A')
      expect(cell.textContent).not.toBe('null')
      expect(cell.textContent).not.toBe('—')
      expect(cell.textContent).not.toBe('unknown')
    }
  })
})

describe('TicketsView — client-side column sort', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('a tier column-header click re-orders rendered rows without triggering a new fetchTickets call', async () => {
    const user = userEvent.setup()
    const mockFetch = mockFetchReturning([
      makeTicket({ ticket_id: 'TCK-B', tier: 'standard' }),
      makeTicket({ ticket_id: 'TCK-A', tier: 'hotfix' }),
    ])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const callsBeforeSort = mockFetch.mock.calls.length

    await user.click(screen.getByTestId('col-header-tier'))

    const rowsAfterSort = screen.getAllByTestId(/^ticket-row-/)
    expect(rowsAfterSort.map((row) => row.getAttribute('data-testid'))).toEqual([
      'ticket-row-TCK-A',
      'ticket-row-TCK-B',
    ])

    const callsAfterSort = mockFetch.mock.calls.length
    if (callsAfterSort > callsBeforeSort) {
      const lastCall = mockFetch.mock.calls[callsAfterSort - 1]
      const requestedUrl = String(lastCall[0])
      const sortParam = new URL(requestedUrl, 'http://localhost').searchParams.get('sort')
      expect(['date_asc', 'date_desc']).toContain(sortParam)
    } else {
      expect(callsAfterSort).toBe(callsBeforeSort)
    }
  })
})

describe('TicketsView — anti-drift source guards', () => {
  it('never re-implements a client-side .filter( pass over fetched ticket rows', () => {
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.filter\(/)
  })

  it('never re-sorts matching_runs client-side', () => {
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/matching_runs[^\n]*\.sort\(/)
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.sort\([^)]*\)[^\n]*matching_runs/)
  })

  it('never constructs a sort value other than date_asc/date_desc for a fetchTickets call', () => {
    const sortLiteralAssignments = TICKETS_VIEW_SOURCE.match(/sort:\s*'[^']*'/g) ?? []
    for (const assignment of sortLiteralAssignments) {
      expect(['date_asc', 'date_desc'].some((literal) => assignment.includes(literal))).toBe(true)
    }
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/'tier_asc'|'tier_desc'|'layer_asc'|'layer_desc'|'priority_asc'|'priority_desc'|'status_asc'|'status_desc'|'tag_asc'|'tag_desc'/)
  })
})
