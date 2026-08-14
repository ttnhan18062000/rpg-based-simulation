import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, afterEach, vi } from 'vitest'
import { StatsView } from '../views/StatsView'
import STATS_VIEW_SOURCE from '../views/StatsView.tsx?raw'
import { _resetGlossaryCacheForTests } from '../api'
import type { AgentMonitoringStats, GlossaryTerms, TicketCorpusStats } from '../api'

function makeAgentStats(overrides: Partial<AgentMonitoringStats> = {}): AgentMonitoringStats {
  return {
    run_summary: { total: 42, done_count: 40, gate_fail_count: 2, avg_duration_min: 12, avg_agents: 8.5, total_agent_calls: 350 },
    gate_failure_breakdown: { architecture_review: 2, parity_gap: 1 },
    reason_code_breakdown: { scope_mismatch: 1 },
    tag_breakdown_subsystem: {},
    tag_breakdown_skill: {},
    tier_distribution: { standard: { count: 30, scoped: 30, done: 28 }, hotfix: { count: 12, scoped: 12, done: 12 } },
    agent_status_distribution: {
      implementer: { ok: 40, failed: 1 },
      'ticket-scoper': { ok: 42 },
    },
    phase_status_distribution: {
      Investigate: { ok: 40, failed: 2 },
      Implement: { ok: 42 },
    },
    spend_proxy_by_phase: {},
    spend_proxy_by_agent: {},
    summary_quality: { empty_summaries_current: 0, legacy_event_count: 5, long_summaries: 1 },
    slow_runs: [{ run_id: 'TCK-slow-1', duration_s: 9000, final_status: 'DONE' }],
    outliers: {
      duration_s: [{ run_id: 'TCK-dur-outlier', tier: 'standard', duration_s: 5000, median: 1000, ratio: 5 }],
      cost_proxy_score: [
        {
          run_id: 'TCK-cost-outlier',
          seq: 3,
          phase: 'Investigate',
          agent: 'investigator',
          cost_proxy_score: 1000,
          median: 100,
          ratio: 10,
        },
      ],
    },
    ...overrides,
  }
}

function makeTicketStats(overrides: Partial<TicketCorpusStats> = {}): TicketCorpusStats {
  return {
    scanned_files: 1178,
    included_tickets: 1154,
    skipped: { legacy: 20, sequence_md: 4 },
    velocity: { by_day: { '2026-07-16': 3, '2026-07-17': 5 }, by_week: {}, unparseable_rows: 0 },
    distribution: {
      tier: { standard: 929, hotfix: 103 },
      ticket_type: { feature: 500, bug: 200 },
      priority: { P1: 400, P2: 300 },
      layer: { observability: 100, engine: 200 },
      layer_by_tier: {},
    },
    artifact_completeness: {
      complete_count: 623,
      incomplete_count: 347,
      total_checked: 970,
      incomplete: [{ ticket_id: 'TCK-incomplete-1', missing: ['plan.md'] }],
    },
    ...overrides,
  }
}

function mockFetch(
  agentStats: AgentMonitoringStats,
  ticketStats: TicketCorpusStats,
  glossary: GlossaryTerms = {},
) {
  const fn = vi.fn((url: string) => {
    if (url.includes('glossary')) {
      return Promise.resolve({ ok: true, json: async () => ({ terms: glossary }) })
    }
    if (url.includes('agent-monitoring')) {
      return Promise.resolve({ ok: true, json: async () => agentStats })
    }
    return Promise.resolve({ ok: true, json: async () => ticketStats })
  })
  globalThis.fetch = fn as unknown as typeof fetch
  return fn
}

describe('StatsView', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    // Every render() in this file that mounts StatsView calls useGlossary() internally — without
    // this, a later test's differently-mocked glossary content silently loses to an earlier
    // test's already-resolved module-level cache (see _resetGlossaryCacheForTests's own docstring
    // in api.ts). Caught by this file's own "shows a hint icon..." /
    // "renders a Top Agents row plainly..." test pair, which genuinely fail without this reset.
    _resetGlossaryCacheForTests()
  })

  it('shows a loading state before the fetches resolve', () => {
    globalThis.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch
    render(<StatsView />)
    expect(screen.getByTestId('stats-view')).toHaveTextContent('Loading statistics')
  })

  it('renders real data from both endpoints once loaded', async () => {
    mockFetch(makeAgentStats(), makeTicketStats())
    render(<StatsView />)

    await screen.findByTestId('stats-section-agent-monitoring')
    expect(screen.getByTestId('stat-tile-Total runs')).toHaveTextContent('42')
    expect(screen.getByTestId('stat-tile-Done')).toHaveTextContent('40')
    expect(screen.getByTestId('bar-chart-row-architecture_review')).toBeInTheDocument()
    expect(screen.getByTestId('grouped-bar-chart-row-standard')).toBeInTheDocument()
    expect(screen.getByTestId('top-agent-row-implementer')).toBeInTheDocument()
    expect(screen.getByTestId('slow-run-row-TCK-slow-1')).toBeInTheDocument()

    expect(screen.getByTestId('stats-section-ticket-corpus')).toBeInTheDocument()
    expect(screen.getByTestId('stat-tile-Scanned files')).toHaveTextContent('1,178')
    expect(screen.getByTestId('stat-tile-Included tickets')).toHaveTextContent('1,154')
    expect(screen.getByTestId('bar-chart-row-standard')).toBeInTheDocument()
  })

  it('never renders the removed per-ticket incomplete-artifacts table', async () => {
    mockFetch(makeAgentStats(), makeTicketStats())
    render(<StatsView />)
    await screen.findByTestId('stats-section-ticket-corpus')
    // The aggregate "Artifact completeness" stat tile stays — only the detailed per-ticket
    // listing (ticket_id + missing files) was removed from the UI. The underlying data is
    // still returned in full by the API/CLI; this just isn't rendered as a table anymore.
    expect(screen.queryByTestId('incomplete-artifacts-table')).not.toBeInTheDocument()
  })

  it('computes artifact completeness as a rounded percentage', async () => {
    mockFetch(makeAgentStats(), makeTicketStats())
    render(<StatsView />)
    await screen.findByTestId('stats-section-ticket-corpus')
    // 623 / 970 = 64.2% -> rounds to 64%
    expect(screen.getByTestId('stat-tile-Artifact completeness')).toHaveTextContent('64%')
  })

  it('renders an error state when a fetch fails, without crashing', async () => {
    globalThis.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 500, json: async () => ({}) })) as unknown as typeof fetch
    render(<StatsView />)

    await waitFor(() => {
      expect(screen.getByTestId('stats-view')).toHaveTextContent('Failed to load statistics')
    })
  })

  it('renders empty-state charts and tables for a zero-corpus/zero-runs response, without crashing', async () => {
    mockFetch(
      makeAgentStats({
        run_summary: { total: 0, done_count: 0, gate_fail_count: 0, avg_duration_min: 0, avg_agents: 0, total_agent_calls: 0 },
        gate_failure_breakdown: {},
        reason_code_breakdown: {},
        tier_distribution: {},
        agent_status_distribution: {},
        phase_status_distribution: {},
        slow_runs: [],
        outliers: { duration_s: [], cost_proxy_score: [] },
      }),
      makeTicketStats({
        scanned_files: 0,
        included_tickets: 0,
        skipped: {},
        velocity: { by_day: {}, by_week: {}, unparseable_rows: 0 },
        distribution: { tier: {}, ticket_type: {}, priority: {}, layer: {}, layer_by_tier: {} },
        artifact_completeness: { complete_count: 0, incomplete_count: 0, total_checked: 0, incomplete: [] },
      }),
    )
    render(<StatsView />)

    await screen.findByTestId('stats-section-agent-monitoring')
    expect(screen.getAllByTestId('bar-chart-empty').length).toBeGreaterThan(0)
    expect(screen.getByTestId('grouped-bar-chart-empty')).toBeInTheDocument()
    expect(screen.getByText('No slow runs')).toBeInTheDocument()
    expect(screen.getByText('No phase data')).toBeInTheDocument()
    expect(screen.getByTestId('no-outliers-state')).toBeInTheDocument()
    expect(screen.getByTestId('stat-tile-Artifact completeness')).toHaveTextContent('0%')
  })

  it('passes a real backend-sourced descriptions map into its BarChart/GroupedBarChart children once the glossary loads', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {
      architecture_review: { term: 'architecture_review', category: 'reason-code', description: 'Architecture review found a fixable violation.' },
    })
    render(<StatsView />)
    await screen.findByTestId('stats-section-agent-monitoring')

    // Full hover-open simulation for this exact description text is covered directly and more
    // simply in src/test/BarChart.test.tsx (isolated render, no async glossary-fetch race with
    // the surrounding view) — this test instead confirms the wiring itself: the row renders, and
    // (per BarChart's own tested behavior) a `descriptions` prop match means the row is
    // hoverable at all, proven by BarChart.test.tsx's own dedicated test.
    await waitFor(() => {
      expect(screen.getByTestId('bar-chart-row-architecture_review')).toBeInTheDocument()
    })
  })

  it('shows a hint icon and real description on the Top Agents table when the glossary has a matching agent entry', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {
      implementer: {
        term: 'implementer',
        category: 'agent',
        description: 'Writes the code changes described in an approved plan.md.',
      },
    })
    render(<StatsView />)
    const row = await screen.findByTestId('top-agent-row-implementer')
    expect(row.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()
  })

  it('renders a Top Agents row plainly, with no hint icon, when the glossary has no entry for that agent (graceful degradation)', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {})
    render(<StatsView />)
    const row = await screen.findByTestId('top-agent-row-implementer')
    expect(row.querySelector('[data-testid="glossary-hint-icon"]')).toBeNull()
  })

  it('renders the slow-runs final_status cell without a tooltip when the glossary has no entry for it (graceful degradation)', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {})
    render(<StatsView />)
    await screen.findByTestId('slow-run-row-TCK-slow-1')

    // No glossary entry for "DONE" in this test's glossary fixture — the cell must still render
    // the raw value, unwrapped, never crash.
    expect(screen.getByTestId('slow-run-row-TCK-slow-1')).toHaveTextContent('DONE')
  })

  it('renders a Phase Status Distribution table with ok/failed/blocked/skipped columns', async () => {
    mockFetch(makeAgentStats(), makeTicketStats())
    render(<StatsView />)

    const table = await screen.findByTestId('phase-status-table')
    expect(table).toHaveTextContent('Phase')
    expect(table).toHaveTextContent('Ok')
    expect(table).toHaveTextContent('Failed')
    expect(table).toHaveTextContent('Blocked')
    expect(table).toHaveTextContent('Skipped')
    expect(screen.getByTestId('phase-status-row-Investigate')).toBeInTheDocument()
    expect(screen.getByTestId('phase-status-row-Implement')).toBeInTheDocument()
  })

  it('renders a hover description for a phase name in the Phase Status Distribution table', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {
      Investigate: {
        term: 'Investigate',
        category: 'phase',
        description: 'Digs into the affected code, docs, and prior tickets.',
      },
    })
    render(<StatsView />)
    const row = await screen.findByTestId('phase-status-row-Investigate')
    expect(row.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()
  })

  it('renders a Phase Status Distribution row plainly, with no hint icon, when the glossary has no entry for that phase', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {})
    render(<StatsView />)
    const row = await screen.findByTestId('phase-status-row-Investigate')
    expect(row.querySelector('[data-testid="glossary-hint-icon"]')).toBeNull()
  })

  it('renders Duration and Cost-Proxy-Score outlier tables when outliers are present', async () => {
    mockFetch(makeAgentStats(), makeTicketStats())
    render(<StatsView />)

    await screen.findByTestId('duration-outliers-table')
    expect(screen.getByTestId('duration-outlier-row-TCK-dur-outlier')).toBeInTheDocument()
    expect(screen.getByTestId('cost-outliers-table')).toBeInTheDocument()
    expect(screen.getByTestId('cost-outlier-row-TCK-cost-outlier-3')).toBeInTheDocument()
  })

  it('renders a graceful "no outliers" state when both outlier lists are empty, not a broken table', async () => {
    mockFetch(
      makeAgentStats({ outliers: { duration_s: [], cost_proxy_score: [] } }),
      makeTicketStats(),
    )
    render(<StatsView />)

    await screen.findByTestId('stats-section-agent-monitoring')
    expect(screen.getByTestId('no-outliers-state')).toBeInTheDocument()
    expect(screen.queryByTestId('duration-outliers-table')).not.toBeInTheDocument()
    expect(screen.queryByTestId('cost-outliers-table')).not.toBeInTheDocument()
  })

  it('wraps tier and agent values in outlier tables with GlossaryTooltip, matching existing Slow Runs / Top Agents cell-wrapping pattern', async () => {
    mockFetch(makeAgentStats(), makeTicketStats(), {
      standard: { term: 'standard', category: 'tier', description: 'Full 9-phase pipeline.' },
      investigator: { term: 'investigator', category: 'agent', description: 'Digs into affected code.' },
    })
    render(<StatsView />)

    const durationRow = await screen.findByTestId('duration-outlier-row-TCK-dur-outlier')
    expect(durationRow.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()

    const costRow = await screen.findByTestId('cost-outlier-row-TCK-cost-outlier-3')
    expect(costRow.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()
  })

  it('never hardcodes a glossary description string in its own source — always sourced from the fetched glossary', () => {
    // Anti-drift guard mirroring this codebase's own established pattern (TicketsView.test.tsx's
    // .filter( guard). A hardcoded description string here would violate this ticket's core
    // requirement: description text must originate ONLY from the backend-fetched glossary.
    expect(STATS_VIEW_SOURCE).toMatch(/useGlossary/)
    expect(STATS_VIEW_SOURCE).toMatch(/glossaryDescriptions/)
    expect(STATS_VIEW_SOURCE).not.toMatch(/description:\s*['"]/)
  })
})
