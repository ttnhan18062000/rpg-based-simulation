import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ReplayTimelineView } from '../views/ReplayTimelineView'
import { _resetGlossaryCacheForTests, type GlossaryTerms, type RunTimeline } from '../api'
import REPLAY_VIEW_SOURCE from '../views/ReplayTimelineView.tsx?raw'

function makeTimeline(overrides: Partial<RunTimeline> = {}): RunTimeline {
  return {
    run_id: 'run-replay',
    is_live: false,
    entries: [
      {
        seq: 1,
        phase: 'Scope',
        agent: 'ticket-scoper',
        status: 'ok',
        summary: 'Scoped the ticket',
        ts: '2026-07-16T10:00:00Z',
        tool_call_count: 1,
        cost_proxy_score: 0.5,
        reason_code: null,
        tool_calls: [
          { tool: 'Read', input_summary: 'tickets/inprogress/T-1.md', status: 'ok', duration_ms: 50, ts: '2026-07-16T10:00:01Z' },
        ],
      },
      {
        seq: 2,
        phase: 'Implement',
        agent: 'implementer',
        status: 'ok',
        summary: 'Implemented the change',
        ts: '2026-07-16T10:05:00Z',
        tool_call_count: 1,
        cost_proxy_score: 1.5,
        reason_code: null,
        tool_calls: [
          { tool: 'Edit', input_summary: 'src/foo.py', status: 'ok', duration_ms: 120, ts: '2026-07-16T10:05:01Z' },
        ],
      },
    ],
    live_tail: [],
    files_touched: [
      { path: 'tickets/inprogress/T-1.md', tool: 'Read', ts: '2026-07-16T10:00:01Z' },
      { path: 'src/foo.py', tool: 'Edit', ts: '2026-07-16T10:05:01Z' },
    ],
    ...overrides,
  }
}

function mockFetchOnce(timeline: RunTimeline) {
  const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => timeline })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

function mockFetchWithGlossary(timeline: RunTimeline, glossary: GlossaryTerms) {
  const mockFetch = vi.fn((url: string) => {
    if (url.includes('glossary')) {
      return Promise.resolve({ ok: true, json: async () => ({ terms: glossary }) })
    }
    return Promise.resolve({ ok: true, json: async () => timeline })
  })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

describe('ReplayTimelineView — rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders entries in the given (backend-guaranteed seq-ascending) array order, each with its own tool_calls', async () => {
    mockFetchOnce(makeTimeline())

    render(<ReplayTimelineView runId="run-replay" />)

    await screen.findByTestId('replay-timeline-view')

    const segments = screen.getAllByTestId(/^replay-entry-\d+$/)
    expect(segments.map((el) => el.getAttribute('data-testid'))).toEqual([
      'replay-entry-1',
      'replay-entry-2',
    ])
    expect(segments[0]).toHaveTextContent('#1 Scope')
    expect(segments[1]).toHaveTextContent('#2 Implement')
  })

  it('trusts the backend-provided array order rather than re-sorting by seq value', async () => {
    const outOfOrder = makeTimeline({
      entries: [
        { ...makeTimeline().entries[1], seq: 5 },
        { ...makeTimeline().entries[0], seq: 3 },
      ],
    })
    mockFetchOnce(outOfOrder)

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    const segments = screen.getAllByTestId(/^replay-entry-\d+$/)
    expect(segments.map((el) => el.getAttribute('data-testid'))).toEqual([
      'replay-entry-5',
      'replay-entry-3',
    ])
  })

  it('files-touched panel renders RunTimeline.files_touched verbatim, without re-deriving it', async () => {
    const timeline = makeTimeline({
      files_touched: [
        { path: 'src/a.py', tool: 'Read', ts: '2026-07-16T10:00:01Z' },
        { path: 'src/a.py', tool: 'Read', ts: '2026-07-16T10:00:05Z' },
        { path: 'src/b.py', tool: 'Edit', ts: '2026-07-16T10:00:06Z' },
      ],
    })
    mockFetchOnce(timeline)

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    const readGroup = screen.getByTestId('replay-files-touched-group-Read')
    const readItems = within(readGroup).getAllByRole('listitem')
    expect(readItems).toHaveLength(2)
    expect(readItems[0]).toHaveTextContent('2026-07-16T10:00:01Z')
    expect(readItems[1]).toHaveTextContent('2026-07-16T10:00:05Z')

    const editGroup = screen.getByTestId('replay-files-touched-group-Edit')
    expect(within(editGroup).getAllByRole('listitem')).toHaveLength(1)
  })

  it('live_tail entries always render an honest phase-unknown caption when is_live is true', async () => {
    const timeline = makeTimeline({
      is_live: true,
      live_tail: [
        { tool: 'Edit', input_summary: 'src/live.py', status: 'ok', duration_ms: null, ts: '2026-07-16T10:10:00Z' },
        { tool: 'Read', input_summary: 'src/other.py', status: 'ok', duration_ms: null, ts: '2026-07-16T10:10:01Z' },
      ],
    })
    mockFetchOnce(timeline)

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    const captions = screen.getAllByTestId('replay-live-tail-caption')
    expect(captions).toHaveLength(2)
    for (const caption of captions) {
      expect(caption).toHaveTextContent('(phase unknown — run still in progress)')
    }
  })

  it('renders no live-tail section at all when is_live is false', async () => {
    mockFetchOnce(makeTimeline({ is_live: false, live_tail: [] }))

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    expect(screen.queryByTestId('replay-live-tail')).not.toBeInTheDocument()
  })
})

describe('ReplayTimelineView — scrub/playback never fetches', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches the timeline exactly once and scrubbing/playback interaction never issues another fetch', async () => {
    const user = userEvent.setup()
    const mockFetch = mockFetchOnce(makeTimeline())

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    expect(mockFetch).toHaveBeenCalledTimes(1)

    await user.click(screen.getByTestId('replay-entry-2'))
    await user.click(screen.getByTestId('replay-entry-1'))
    await user.click(screen.getByRole('button', { name: 'Play' }))
    await user.click(screen.getByRole('button', { name: '5x' }))
    await user.click(screen.getByRole('button', { name: 'Pause' }))

    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('scrub position gates the detail area, revealing more entries as the position advances, never fewer', async () => {
    const user = userEvent.setup()
    mockFetchOnce(makeTimeline())

    render(<ReplayTimelineView runId="run-replay" />)
    await screen.findByTestId('replay-timeline-view')

    expect(screen.queryByTestId('replay-detail-1')).toBeInTheDocument()
    expect(screen.queryByTestId('replay-detail-2')).not.toBeInTheDocument()

    await user.click(screen.getByTestId('replay-entry-2'))

    expect(screen.queryByTestId('replay-detail-1')).toBeInTheDocument()
    expect(screen.queryByTestId('replay-detail-2')).toBeInTheDocument()
  })
})

describe('ReplayTimelineView — glossary tooltip wiring', () => {
  // Scoped to this describe block only — other describe blocks in this file deliberately rely on
  // the module-level glossary cache persisting across tests (see the "fetches the timeline
  // exactly once" test above, which asserts on total fetch() call count and would break if the
  // cache reset forced a second glossary fetch mid-suite). Only this block varies glossary content
  // across its own it()s, so only this block needs the reset (same reasoning as api.ts's own
  // _resetGlossaryCacheForTests docstring and StatsView.test.tsx's file-wide afterEach) — before
  // each test too, since an earlier describe block may already have resolved the shared cache.
  beforeEach(() => {
    vi.restoreAllMocks()
    _resetGlossaryCacheForTests()
  })

  afterEach(() => {
    _resetGlossaryCacheForTests()
  })

  it('shows a hint icon for the phase name in the phase-timeline button strip when the glossary has a matching entry', async () => {
    mockFetchWithGlossary(makeTimeline(), {
      Scope: { term: 'Scope', category: 'phase', description: 'Creates the ticket file.' },
    })

    render(<ReplayTimelineView runId="run-replay" />)
    const entry = await screen.findByTestId('replay-entry-1')

    expect(entry.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()
  })

  it('renders the phase-timeline button strip plainly, with no hint icon, when the glossary has no entry for that phase', async () => {
    mockFetchWithGlossary(makeTimeline(), {})

    render(<ReplayTimelineView runId="run-replay" />)
    const entry = await screen.findByTestId('replay-entry-1')

    expect(entry.querySelector('[data-testid="glossary-hint-icon"]')).toBeNull()
    expect(entry).toHaveTextContent('#1 Scope')
  })

  it('shows hint icons for phase and agent in the detail-area header when the glossary has matching entries', async () => {
    mockFetchWithGlossary(makeTimeline(), {
      Scope: { term: 'Scope', category: 'phase', description: 'Creates the ticket file.' },
      'ticket-scoper': { term: 'ticket-scoper', category: 'agent', description: 'Creates the ticket.' },
    })

    render(<ReplayTimelineView runId="run-replay" />)
    const detail = await screen.findByTestId('replay-detail-1')

    const hintIcons = detail.querySelectorAll('[data-testid="glossary-hint-icon"]')
    // phase + agent, both matched — status ('ok') has no matching entry in this test's fixture.
    expect(hintIcons.length).toBe(2)
  })

  it('renders the detail-area header plainly, with no hint icons, when the glossary has no matching entries', async () => {
    mockFetchWithGlossary(makeTimeline(), {})

    render(<ReplayTimelineView runId="run-replay" />)
    const detail = await screen.findByTestId('replay-detail-1')

    expect(detail.querySelectorAll('[data-testid="glossary-hint-icon"]').length).toBe(0)
    expect(detail).toHaveTextContent('#1 Scope · ticket-scoper · ok')
  })
})

describe('ReplayTimelineView — anti-drift source guards', () => {
  it('never re-implements a second files_touched dedup/filter pass over tool_calls data', () => {
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/\.filter\(/)
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/\.set\(\s*(touch|call|tailCall)\.(path|input_summary)/)
  })

  it('never infers a phase/agent label for live_tail entries', () => {
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/tailCall\.phase/)
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/tailCall\.agent/)
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/tool\s*===\s*'/)
  })

  it('never re-sorts entries client-side', () => {
    expect(REPLAY_VIEW_SOURCE).not.toMatch(/\.sort\(/)
  })
})
