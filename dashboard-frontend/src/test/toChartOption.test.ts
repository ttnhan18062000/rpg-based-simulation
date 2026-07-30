import { describe, it, expect } from 'vitest'
import { toChartOption, buildTooltipHtml, LIVE_SEGMENT_COLOR } from '../lib/toChartOption'
import type { RunSummary, TimelineEntry, GlossaryTerms } from '../api'
import TO_CHART_OPTION_SOURCE from '../lib/toChartOption.ts?raw'

function makeRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-a',
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: '2026-07-16T10:00:00Z',
    end_ts: '2026-07-16T10:10:00Z',
    duration_s: 600,
    agent_count: 1,
    is_inferred_active: false,
    inferred_start_ts: null,
    ...overrides,
  }
}

function makeEntry(overrides: Partial<TimelineEntry> = {}): TimelineEntry {
  return {
    seq: 0,
    phase: 'Implement',
    agent: 'implementer',
    status: 'DONE',
    summary: 'did a thing',
    ts: '2026-07-16T10:00:00Z',
    tool_call_count: 1,
    cost_proxy_score: 0.1,
    reason_code: null,
    tool_calls: [],
    ...overrides,
  }
}

describe('toChartOption — newest-first y-axis ordering', () => {
  it('lists run_ids in the same descending order the mergeAndSortRuns comparator produces', () => {
    const runs = [
      makeRun({ run_id: 'run-mid', start_ts: '2026-07-15T10:00:00Z' }),
      makeRun({ run_id: 'run-newest', start_ts: '2026-07-17T10:00:00Z' }),
      makeRun({ run_id: 'run-inferred-only', start_ts: null, inferred_start_ts: '2026-07-16T00:00:00Z' }),
      makeRun({ run_id: 'run-oldest', start_ts: '2026-07-10T10:00:00Z' }),
    ]

    const expectedOrder = [...runs]
      .sort((a, b) => {
        const aTs = a.start_ts ?? a.inferred_start_ts ?? ''
        const bTs = b.start_ts ?? b.inferred_start_ts ?? ''
        return bTs.localeCompare(aTs)
      })
      .map((r) => r.run_id)

    const option = toChartOption(runs, {}, '2026-07-18T00:00:00Z')

    expect(option.yAxis.data).toEqual(expectedOrder)
  })
})

describe('toChartOption — N entries produce N segments (Resolved Decision 10)', () => {
  it('settled run: 3 inter-entry segments + 1 trailing settled segment to end_ts', () => {
    const entries = [
      makeEntry({ seq: 0, phase: 'Scope', ts: '2026-07-16T10:00:00Z' }),
      makeEntry({ seq: 1, phase: 'Plan', ts: '2026-07-16T10:01:00Z' }),
      makeEntry({ seq: 2, phase: 'Implement', ts: '2026-07-16T10:02:00Z' }),
      makeEntry({ seq: 3, phase: 'Verify', ts: '2026-07-16T10:03:00Z' }),
    ]
    const run = makeRun({
      run_id: 'run-settled',
      is_inferred_active: false,
      end_ts: '2026-07-16T10:05:00Z',
    })

    const option = toChartOption([run], { 'run-settled': entries }, '2026-07-16T11:00:00Z')
    const segments = option.series[0].data

    expect(segments).toHaveLength(4)
    expect(segments.slice(0, 3).every((s: { isLive: boolean }) => s.isLive === false)).toBe(true)

    const trailing = segments[3]
    expect(trailing.isLive).toBe(false)
    expect(trailing.phase).toBe('Verify')
    expect(trailing.startMs).toBe(Date.parse('2026-07-16T10:03:00Z'))
    expect(trailing.endMs).toBe(Date.parse('2026-07-16T10:05:00Z'))
    expect(trailing.itemStyle.color).not.toBe(LIVE_SEGMENT_COLOR)
  })

  it('is_inferred_active run: 3 inter-entry segments + 1 live trailing segment to nowIso, replacing the settled trailing segment', () => {
    const entries = [
      makeEntry({ seq: 0, phase: 'Scope', ts: '2026-07-16T10:00:00Z' }),
      makeEntry({ seq: 1, phase: 'Plan', ts: '2026-07-16T10:01:00Z' }),
      makeEntry({ seq: 2, phase: 'Implement', ts: '2026-07-16T10:02:00Z' }),
      makeEntry({ seq: 3, phase: 'Verify', ts: '2026-07-16T10:03:00Z' }),
    ]
    const nowIso = '2026-07-16T10:10:00Z'
    const run = makeRun({
      run_id: 'run-active',
      is_inferred_active: true,
      end_ts: null,
      inferred_start_ts: '2026-07-16T10:00:00Z',
    })

    const option = toChartOption([run], { 'run-active': entries }, nowIso)
    const segments = option.series[0].data

    expect(segments).toHaveLength(4)
    expect(segments.slice(0, 3).every((s: { isLive: boolean }) => s.isLive === false)).toBe(true)

    const trailing = segments[3]
    expect(trailing.isLive).toBe(true)
    expect(trailing.itemStyle.color).toBe(LIVE_SEGMENT_COLOR)
    expect(trailing.startMs).toBe(Date.parse('2026-07-16T10:03:00Z'))
    expect(trailing.endMs).toBe(Date.parse(nowIso))
  })

  it('edge case A: zero entries + is_inferred_active -> exactly one live segment spanning inferred_start_ts to nowIso', () => {
    const nowIso = '2026-07-16T10:10:00Z'
    const run = makeRun({
      run_id: 'run-zero-entries-active',
      is_inferred_active: true,
      inferred_start_ts: '2026-07-16T10:05:00Z',
      end_ts: null,
    })

    const option = toChartOption([run], {}, nowIso)
    const segments = option.series[0].data

    expect(segments).toHaveLength(1)
    expect(segments[0].isLive).toBe(true)
    expect(segments[0].startMs).toBe(Date.parse('2026-07-16T10:05:00Z'))
    expect(segments[0].endMs).toBe(Date.parse(nowIso))
  })

  it('edge case A2: zero entries + is_inferred_active + null inferred_start_ts -> falls back to nowIso, no crash', () => {
    const nowIso = '2026-07-16T10:10:00Z'
    const run = makeRun({
      run_id: 'run-zero-entries-no-inferred-start',
      is_inferred_active: true,
      inferred_start_ts: null,
      end_ts: null,
    })

    expect(() => toChartOption([run], {}, nowIso)).not.toThrow()
    const option = toChartOption([run], {}, nowIso)
    const segments = option.series[0].data

    expect(segments).toHaveLength(1)
    expect(segments[0].startMs).toBe(Date.parse(nowIso))
    expect(segments[0].endMs).toBe(Date.parse(nowIso))
  })

  it('edge case B: run_id present in runs but absent (no key at all) from entriesByRun does not throw', () => {
    const run = makeRun({ run_id: 'run-missing-entries', is_inferred_active: false, end_ts: '2026-07-16T10:05:00Z' })

    expect(() => toChartOption([run], {}, '2026-07-16T11:00:00Z')).not.toThrow()
    const option = toChartOption([run], {}, '2026-07-16T11:00:00Z')
    expect(option.series[0].data).toHaveLength(0)
  })

  it('edge case C: settled run with end_ts null produces no trailing segment (only N-1 inter-entry segments)', () => {
    const entries = [
      makeEntry({ seq: 0, phase: 'Scope', ts: '2026-07-16T10:00:00Z' }),
      makeEntry({ seq: 1, phase: 'Plan', ts: '2026-07-16T10:01:00Z' }),
    ]
    const run = makeRun({ run_id: 'run-no-end-ts', is_inferred_active: false, end_ts: null })

    const option = toChartOption([run], { 'run-no-end-ts': entries }, '2026-07-16T11:00:00Z')
    const segments = option.series[0].data

    expect(segments).toHaveLength(1)
    expect(segments[0].isLive).toBe(false)
  })
})

describe('buildTooltipHtml', () => {
  const fixtureData = {
    runId: 'run-tooltip',
    tier: 'standard',
    workflow: 'implement-ticket',
    phase: 'Implement',
    agent: 'implementer',
    status: 'DONE',
    startMs: Date.parse('2026-07-16T10:00:00Z'),
    endMs: Date.parse('2026-07-16T10:05:30Z'),
    isLive: false,
  }

  it('with a populated glossary, includes all seven base fields plus both description lines', () => {
    const glossary: GlossaryTerms = {
      Implement: { term: 'Implement', category: 'phase', description: 'Writes the code.' },
      implementer: { term: 'implementer', category: 'agent', description: 'Writes code changes.' },
    }

    const html = buildTooltipHtml({ data: fixtureData }, glossary)

    expect(html).toContain('run-tooltip')
    expect(html).toContain('standard')
    expect(html).toContain('implement-ticket')
    expect(html).toContain('Implement')
    expect(html).toContain('implementer')
    expect(html).toContain('DONE')
    expect(html).toContain('5m 30s')
    expect(html).toContain('Writes the code.')
    expect(html).toContain('Writes code changes.')
  })

  it('with an empty glossary, includes the seven base fields with no description line and does not throw', () => {
    expect(() => buildTooltipHtml({ data: fixtureData }, {})).not.toThrow()
    const html = buildTooltipHtml({ data: fixtureData }, {})

    expect(html).toContain('run-tooltip')
    expect(html).toContain('standard')
    expect(html).toContain('implement-ticket')
    expect(html).toContain('Implement')
    expect(html).toContain('implementer')
    expect(html).toContain('DONE')
    expect(html).toContain('5m 30s')
    expect(html).not.toContain('color:#8b8fa8')
  })

  it('returns an empty string when params.data is absent, without throwing', () => {
    expect(() => buildTooltipHtml({}, {})).not.toThrow()
    expect(buildTooltipHtml({}, {})).toBe('')
  })
})

describe('toChartOption — anti-drift: no client-side activity re-derivation', () => {
  it('never calls Date.now() or constructs a new Date() to judge activity', () => {
    expect(TO_CHART_OPTION_SOURCE).not.toMatch(/Date\.now\(\)/)
    expect(TO_CHART_OPTION_SOURCE).not.toMatch(/new Date\(/)
  })

  it('gates the live-segment branch on run.is_inferred_active directly', () => {
    expect(TO_CHART_OPTION_SOURCE).toMatch(/if\s*\(\s*run\.is_inferred_active\s*\)/)
  })
})
