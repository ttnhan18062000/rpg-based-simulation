import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { GanttBar } from '../components/GanttBar'
import type { RunSummary } from '../api'
import GANTT_BAR_SOURCE from '../components/GanttBar.tsx?raw'

// Anti-drift guard: the frontend must never independently re-derive "is this
// run active" from raw timestamps — it must always trust the backend's
// computed `is_inferred_active`/`inferred_start_ts` fields verbatim. Prevents
// silently reimplementing the out-of-scope ACTIVE_WINDOW_MINUTES heuristic
// client-side. See test_plan.md's "Anti-Drift Test Guards" section.

function makeRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-guard',
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: null,
    end_ts: null,
    duration_s: null,
    agent_count: 1,
    is_inferred_active: false,
    inferred_start_ts: null,
    ...overrides,
  }
}

describe('GanttBar — no client-side activity re-derivation', () => {
  it('never calls Date.now() or constructs a new Date() to judge activity', () => {
    expect(GANTT_BAR_SOURCE).not.toMatch(/Date\.now\(\)/)
    expect(GANTT_BAR_SOURCE).not.toMatch(/new Date\(/)
  })

  it('branches on run.is_inferred_active directly rather than a locally recomputed value', () => {
    expect(GANTT_BAR_SOURCE).toMatch(/if\s*\(\s*run\.is_inferred_active\s*\)/)
  })

  it('renders the authoritative branch when is_inferred_active is false even though start_ts is recent and end_ts is null', () => {
    const recentlyStartedButNotFlaggedActive = makeRun({
      is_inferred_active: false,
      start_ts: new Date(Date.now() - 5_000).toISOString(),
      end_ts: null,
    })
    const nowIso = new Date().toISOString()
    const windowStartIso = new Date(Date.now() - 60_000).toISOString()

    render(
      <GanttBar
        run={recentlyStartedButNotFlaggedActive}
        nowIso={nowIso}
        windowStartIso={windowStartIso}
        windowEndIso={nowIso}
      />,
    )

    const bar = document.querySelector(
      `[data-run-id="${recentlyStartedButNotFlaggedActive.run_id}"]`,
    )!
    expect(bar.className).toContain('gantt-bar--authoritative')
    expect(bar.className).not.toContain('gantt-bar--inferred')
  })

  it('renders the inferred branch when is_inferred_active is true even though inferred_start_ts is hours old', () => {
    const staleButFlaggedActive = makeRun({
      is_inferred_active: true,
      inferred_start_ts: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    })
    const nowIso = new Date().toISOString()
    const windowStartIso = new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()

    render(
      <GanttBar
        run={staleButFlaggedActive}
        nowIso={nowIso}
        windowStartIso={windowStartIso}
        windowEndIso={nowIso}
      />,
    )

    const bar = document.querySelector(`[data-run-id="${staleButFlaggedActive.run_id}"]`)!
    expect(bar.className).toContain('gantt-bar--inferred')
    expect(bar.className).not.toContain('gantt-bar--authoritative')
  })
})

// Regression guard for the on-chart label crowding bug (found during live verification of
// TCK-20260717-GANTT-TIME-AXIS): a long, hyphen-heavy run_id inside a narrow (<1%-wide)
// absolutely-positioned bar was soft-wrapping at each hyphen with no white-space/overflow
// constraint, stacking many lines that bled vertically into neighboring rows.
describe('GanttBar — on-chart label never wraps or grows unbounded', () => {
  const LONG_RUN_ID = 'TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT-VERY-LONG-EXAMPLE-ID'

  it('renders the authoritative-branch label with whitespace-nowrap and a bounded max-width', () => {
    const run = makeRun({ run_id: LONG_RUN_ID, final_status: 'DONE' })
    const nowIso = new Date().toISOString()
    const windowStartIso = new Date(Date.now() - 60_000).toISOString()

    render(
      <GanttBar run={run} nowIso={nowIso} windowStartIso={windowStartIso} windowEndIso={nowIso} />,
    )

    const label = document.querySelector('[data-testid="gantt-bar-run-label"]')!
    expect(label.className).toContain('whitespace-nowrap')
    expect(label.className).toMatch(/max-w-\[\d+px\]/)
    expect(label.className).toContain('overflow-hidden')
  })

  it('renders the inferred-branch label with whitespace-nowrap and a bounded max-width', () => {
    const run = makeRun({
      run_id: LONG_RUN_ID,
      is_inferred_active: true,
      inferred_start_ts: new Date(Date.now() - 60_000).toISOString(),
    })
    const nowIso = new Date().toISOString()
    const windowStartIso = new Date(Date.now() - 120_000).toISOString()

    render(
      <GanttBar run={run} nowIso={nowIso} windowStartIso={windowStartIso} windowEndIso={nowIso} />,
    )

    const label = document.querySelector('[data-testid="gantt-bar-run-label"]')!
    expect(label.className).toContain('whitespace-nowrap')
    expect(label.className).toMatch(/max-w-\[\d+px\]/)
    expect(label.className).toContain('overflow-hidden')
  })
})
