---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-PROGRESS-TIMELINE-VIEW
artifact_type: plan
tags: [dashboard, observability]
---

# Implementation Plan — TCK-20260720-PROGRESS-TIMELINE-VIEW

## Summary

Replace `RecentActivityGantt.tsx`'s DOM/CSS-percent Gantt rendering with a new
`ProgressTimelineView.tsx` that wraps `echarts-for-react`'s tree-shaken `EChartsReactCore`
(`echarts-for-react/lib/core`, not the default `echarts-for-react` export — see Resolved Decision
1, a load-bearing correction to the ticket's own "wrapping echarts-for-react's `<ReactECharts>`"
phrasing). Five independent moving parts: (1) a new `useRunTimelinesPolling(sinceIso)` hook in
`api.ts`, sibling to `useRunsPolling`, polling the already-DONE bulk `GET /api/runs/timeline`
endpoint; (2) a new pure `dashboard-frontend/src/lib/toChartOption.ts` module exporting
`toChartOption(runs, entriesByRun, nowIso, glossary?)` (one y-axis category per `run_id`,
newest-first via a locally re-implemented sort comparator — never calling the unexported
`mergeAndSortRuns`) and `buildTooltipHtml(params, glossary)`, plus a component-local
`LIVE_SEGMENT_COLOR` constant kept out of `phasePalette.ts`'s governed 21-key set; (3) the new
`ProgressTimelineView.tsx`, wiring both `useRunsPolling` and `useRunTimelinesPolling` (two
independent polls — the bulk endpoint carries no `RunSummary` fields) plus `useGlossary()`, two
client-side `dataZoom` instances, and an `onEvents.click` handler forwarding the clicked segment's
`run_id` to `onSelectRun`; (4) an `App.tsx` swap that preserves the `'activity'` `PageView` value
and `'Recent Activity'` button label verbatim while renaming the view root's `data-testid` from
`"recent-activity-gantt"` to `"progress-timeline-view"`; and (5) deletion of `GanttBar.tsx`,
`TimeAxis.tsx`, `Legend.tsx`, `RecentActivityGantt.tsx`, their three test files, and
`index.css`'s now-dead `.gantt-bar--inferred-pattern` rule. A genuine ambiguity in the ticket's own
AC text vs. `test_plan.md`'s edge-case list (whether settled runs get a trailing completion
segment to `end_ts`) was raised to the user rather than decided unilaterally — **resolved: settled
runs also get a trailing segment extending to `run.end_ts`**, so every one of the N phases in a
run (settled or live) always has a visible rendered segment on the chart; see Resolved Decision 10
and Step 2.

## Resolved Decisions

Plan-time calls on details `investigation.md`/`test_plan.md` left open or only recommended:

1. **`echarts-for-react` entry point — tree-shaking correction not explicit in investigation.md.**
   Confirmed by reading `node_modules/echarts-for-react/esm/index.js`: the package's *default*
   export (`import ReactECharts from 'echarts-for-react'`) internally does `import * as echarts
   from 'echarts'` — i.e. it always pulls in the full bare `echarts` bundle, regardless of what
   `ProgressTimelineView.tsx` itself imports. `test_no_source_file_imports_full_echarts_bundle`
   would NOT catch this (it only regexes `dashboard-frontend/src/**/*.{ts,tsx}`, never
   `node_modules/`), so the guard would pass even while defeating the tree-shaking the palette
   ticket's original Scope text required (`CustomChart`/`TooltipComponent`/`DataZoomComponent`/
   `GridComponent`/`CanvasRenderer`, named explicitly). The correct, package-documented pattern
   (`node_modules/echarts-for-react/README.md:70-73`) is the **core** entry point:
   ```ts
   import ReactEChartsCore from 'echarts-for-react/lib/core'
   import * as echarts from 'echarts/core'
   import { CustomChart } from 'echarts/charts'
   import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
   import { CanvasRenderer } from 'echarts/renderers'
   echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])
   ```
   `ProgressTimelineView.tsx` renders `<ReactEChartsCore echarts={echarts} option={...} .../>`, not
   `<ReactECharts option={...} />`. Confirmed the three named exports (`CustomChart` from
   `echarts/charts`, `TooltipComponent`/`GridComponent`/`DataZoomComponent` from
   `echarts/components`) exist in the installed `echarts@6.1.0`'s type exports
   (`node_modules/echarts/types/src/export/{charts,components}.d.ts`).
2. **`toChartOption`'s signature gains a 4th, optional `glossary` parameter.** The ticket's own
   Scope text writes the signature as `toChartOption(runs, entriesByRun, nowIso)` (3 params), but
   the tooltip.formatter must surface glossary descriptions per investigation's Open Question 1
   recommendation, and a pure function cannot call the `useGlossary()` React hook itself. Resolved:
   `toChartOption(runs: RunSummary[], entriesByRun: Record<string, TimelineEntry[]>, nowIso: string,
   glossary: GlossaryTerms = {})` — the 4th param defaults to `{}`, so any 3-arg call (matching the
   literal ticket text, and `test_plan.md`'s New Test #1/#2 which don't exercise glossary) still
   works and produces a tooltip with the seven base fields and no description lines, satisfying the
   "gracefully omit missing entries" contract. `ProgressTimelineView` calls `useGlossary()` and
   passes the result through.
3. **Tooltip formatter is extracted as a separately-exported `buildTooltipHtml`, not inlined.**
   Matches `test_plan.md`'s explicit recommendation ("keeps it independently testable without
   mounting the chart"). Lives in the same `toChartOption.ts` file. `toChartOption`'s returned
   `tooltip.formatter` is a thin closure: `(params) => buildTooltipHtml(params, glossary)`.
4. **Tooltip content uses inline `style` attributes, not Tailwind utility classes.** ECharts
   renders `tooltip.formatter`'s returned string as `innerHTML` of a floating DOM node it manages
   itself, appended to `document.body` outside React's tree. Tailwind v4's build-time class
   scanner may not reliably pick up class-name-shaped substrings assembled inside a template
   literal at runtime; inline styles (reusing the exact hex values already declared in
   `index.css`'s `@theme` block, e.g. `#8b8fa8` for the secondary-text color) avoid depending on
   that scan succeeding.
5. **`LIVE_SEGMENT_COLOR` lives in `toChartOption.ts`, not `ProgressTimelineView.tsx` or
   `phasePalette.ts`.** Per investigation Risk 4 / Anti-Drift Hazards: a new, separately-named,
   component-local constant, never a 22nd key in `PHASE_PALETTE`. Value: `#5b6178` — a desaturated
   blue-gray roughly at the same OKLCH lightness band as the dark palette's mid-tones, distinct
   from all 21 `PHASE_PALETTE` hex values (visually a "not yet a settled color" neutral, echoing
   the old CSS diagonal-stripe treatment's intent without reintroducing a pattern fill — the
   palette ticket's own Anti-Drift Notes reserve pattern/texture for the accessibility/print
   channel, never on by default). Not re-validated against `validate_palette.js` — it is a single
   non-categorical marker color, not a member of the 21-phase categorical set that validator
   governs.
6. **`toChartOption` re-implements the sort comparator locally; does not import/call
   `mergeAndSortRuns`.** `mergeAndSortRuns` is not exported from `api.ts` (confirmed by reading the
   file) and the Anti-Drift Hazards explicitly forbid touching it. `toChartOption` sorts its own
   copy of `runs` with the identical comparator (`(a.start_ts ?? a.inferred_start_ts ?? '')` vs.
   `(b...)`, `localeCompare` descending) — duplicated, not shared, matching the AC's own "matching
   mergeAndSortRuns' sort" (behavior parity) rather than "matching mergeAndSortRuns' output"
   (function identity). No dedup-by-`run_id` step is added (dedup is `useRunsPolling`'s
   responsibility upstream; `toChartOption` receives already-deduped `runs` in production, and the
   AC only asks for sort-order parity, not dedup, from the pure function itself).
7. **Retirement architecture guard: extended into the existing
   `test_agent_ops_dashboard_frontend_api_surface.py`, not a new sibling file.** Matches this same
   file's own precedent (the palette ticket added two new test functions to it rather than
   spinning up a new file) and reuses its existing `_frontend_source_files()` walk helper, per
   `test_plan.md`'s own steer ("avoid duplicating the file-walk helper").
8. **`ProgressTimelineView.tsx` keeps the same fixed `SINCE_WINDOW_MS = 24h` / `NOW_TICK_MS = 1s`
   constants `RecentActivityGantt.tsx` used.** The range-control UI (quick-range presets/custom
   picker) is explicitly out of scope (a separate ticket); until that lands, the view needs *some*
   window bound to pass to both polling hooks, and reusing the existing constants is the smallest
   change that satisfies "no filtering/range UI added" (Anti-Drift Hazards) without inventing a new
   default.
9. **Parity ledger: new entry `INFRA-303`**, re-verify the true next-free ID at implementation
   time (`INFRA-302` is the last entry as of planning; other in-flight branch work could claim it
   first) — following the same "new entry per ticket, never edit priors" precedent `INFRA-301`/
   `INFRA-302` themselves used.
10. **Settled runs get a trailing completion segment to `run.end_ts` (user decision, not resolved
    unilaterally).** This plan's original draft raised a genuine tension between the ticket's AC #2
    text ("N settled entries -> exactly N-1 segments") and `test_plan.md`'s edge case ("a settled
    run's last entry's `ts` should extend to `end_ts`, not `nowIso`") as an Unresolved Question
    rather than picking a reading unilaterally. The user resolved it: settled (non-live) runs also
    get one additional trailing segment, from the last entry's `ts` to `run.end_ts`, colored by the
    last entry's own phase (not `LIVE_SEGMENT_COLOR`, which is reserved for genuinely in-progress
    runs). Net effect: every run, live or settled, always renders exactly N segments for N phase
    entries — no phase is ever invisible on the chart. This changes Step 2's segment-building loop
    (now unconditionally appends a trailing segment for every run with `entries.length > 0`,
    choosing between `LIVE_SEGMENT_COLOR`/`nowMs` for `is_inferred_active` runs and the last
    entry's phase color/`end_ts` for settled ones) and Step 6's test 2 (now asserts N segments, not
    N-1, and adds an explicit assertion for the settled-run trailing-segment case).

## Steps

### Step 1 — Add `BulkRunTimeline` type + `useRunTimelinesPolling` hook
**Files:** `dashboard-frontend/src/api.ts`

**Change:** Add, directly below `useRunsPolling` (after line 447), mirroring its exact
polling/merge/cleanup shape and `fetchAllRunsSince`'s pagination-loop shape:

```ts
export interface BulkRunTimeline {
  entries_by_run: Record<string, TimelineEntry[]>
}

async function fetchRunTimelines(params: {
  since?: string
  until?: string
  limit?: number
  offset?: number
}): Promise<BulkRunTimeline> {
  const query = new URLSearchParams()
  if (params.since !== undefined) query.set('since', params.since)
  if (params.until !== undefined) query.set('until', params.until)
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))

  const response = await fetch(`/api/runs/timeline?${query.toString()}`)
  if (!response.ok) {
    throw new Error(`GET /api/runs/timeline failed with status ${response.status}`)
  }
  return (await response.json()) as BulkRunTimeline
}

const RUN_TIMELINES_PAGE_LIMIT = 100

async function fetchAllRunTimelinesSince(sinceIso: string): Promise<Record<string, TimelineEntry[]>> {
  const merged: Record<string, TimelineEntry[]> = {}
  let offset = 0

  for (;;) {
    const page = await fetchRunTimelines({ since: sinceIso, limit: RUN_TIMELINES_PAGE_LIMIT, offset })
    const pageRunCount = Object.keys(page.entries_by_run).length
    Object.assign(merged, page.entries_by_run)
    if (pageRunCount < RUN_TIMELINES_PAGE_LIMIT) {
      break
    }
    offset += RUN_TIMELINES_PAGE_LIMIT
  }

  return merged
}

export interface UseRunTimelinesPollingResult {
  entriesByRun: Record<string, TimelineEntry[]>
  isLoading: boolean
  error: Error | null
}

export function useRunTimelinesPolling(sinceIso: string, intervalMs = 5000): UseRunTimelinesPollingResult {
  const [entriesByRun, setEntriesByRun] = useState<Record<string, TimelineEntry[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const merged = await fetchAllRunTimelinesSince(sinceIso)
        if (!cancelled) {
          setEntriesByRun(merged)
          setError(null)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    poll()
    const intervalId = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [sinceIso, intervalMs])

  return { entriesByRun, isLoading, error }
}
```

Note the merge semantics differ deliberately from `mergeAndSortRuns`: `Object.assign(merged,
page.entries_by_run)` is a union-by-`run_id` across pages (a later page's key for the same
`run_id` would overwrite, but pages are `offset`-partitioned by distinct run selections so this
should not collide in practice) — this satisfies `test_plan.md` New Test #7's "merged result must
be a union across pages, not last-page-wins" requirement.

**Do NOT touch:** `useRunsPolling`, `mergeAndSortRuns`, `fetchAllRunsSince`, `fetchRuns`,
`RUNS_PAGE_LIMIT` — all untouched, read only as the pattern template. Do not add a `status`/
`workflow` param to `fetchRunTimelines` (the bulk endpoint route itself only accepts
`since`/`until`/`limit`/`offset`, confirmed in investigation).

**Verify:** Step 7's `useRunTimelinesPolling.test.ts`.

---

### Step 2 — Create `toChartOption.ts` (pure transform + tooltip formatter)
**Files:** `dashboard-frontend/src/lib/toChartOption.ts` (new)

**Change:** New file. Full sketch (implementer should adjust exact `EChartsOption`/`CustomSeriesOption`
generic typings to what `echarts/core` + `echarts/charts` actually export, confirmed present in
Resolved Decision 1):

```ts
import type { RunSummary, TimelineEntry, GlossaryTerms } from '@/api'

// Marker color for the trailing "live"/in-progress segment. Deliberately NOT a member of
// phasePalette.ts's governed 21-key PHASE_PALETTE (that module's scope is closed — see
// TCK-20260720-ECHARTS-PHASE-PALETTE) — a distinct, non-categorical constant local to this file.
export const LIVE_SEGMENT_COLOR = '#5b6178'

interface ChartSegmentDatum {
  runId: string
  tier: string
  workflow: string
  phase: string | null
  agent: string | null
  status: string
  startMs: number
  endMs: number
  isLive: boolean
}

function sortRunsNewestFirst(runs: RunSummary[]): RunSummary[] {
  // Duplicated, not imported: api.ts's mergeAndSortRuns() is not exported and must not be
  // touched. This reproduces its comparator only (behavior parity, not function identity).
  return [...runs].sort((a, b) => {
    const aTs = a.start_ts ?? a.inferred_start_ts ?? ''
    const bTs = b.start_ts ?? b.inferred_start_ts ?? ''
    return bTs.localeCompare(aTs)
  })
}

function formatDurationMs(ms: number): string {
  const totalSeconds = Math.max(Math.floor(ms / 1000), 0)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}m ${seconds}s`
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function buildTooltipHtml(
  params: { data?: ChartSegmentDatum },
  glossary: GlossaryTerms,
): string {
  const d = params.data
  if (!d) return ''
  const lines = [
    `<strong>${escapeHtml(d.runId)}</strong>`,
    `${escapeHtml(d.tier)} &middot; ${escapeHtml(d.workflow)}`,
    `Phase: ${escapeHtml(d.phase ?? 'unknown')}`,
    `Agent: ${escapeHtml(d.agent ?? 'unknown')}`,
    `Status: ${escapeHtml(d.status)}`,
    `Duration: ${escapeHtml(formatDurationMs(d.endMs - d.startMs))}`,
  ]
  const phaseDesc = d.phase ? glossary[d.phase]?.description : undefined
  if (phaseDesc) {
    lines.push(`<div style="color:#8b8fa8;font-size:11px">${escapeHtml(phaseDesc)}</div>`)
  }
  const agentDesc = d.agent ? glossary[d.agent]?.description : undefined
  if (agentDesc) {
    lines.push(`<div style="color:#8b8fa8;font-size:11px">${escapeHtml(agentDesc)}</div>`)
  }
  return lines.join('<br/>')
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- EChartsOption's CustomSeriesOption
// renderItem signature comes from echarts/core; kept loose here rather than importing its exact
// generic params, matched precisely during Implement against the installed echarts@6.1.0 types.
export function toChartOption(
  runs: RunSummary[],
  entriesByRun: Record<string, TimelineEntry[]>,
  nowIso: string,
  glossary: GlossaryTerms = {},
): any {
  const sortedRuns = sortRunsNewestFirst(runs)
  const nowMs = Date.parse(nowIso)

  const data: Array<{ value: [number, number, number]; runId: string; itemStyle: { color: string }; name: string } & ChartSegmentDatum> = []

  sortedRuns.forEach((run, runIndex) => {
    const entries = entriesByRun[run.run_id] ?? []
    for (let i = 0; i < entries.length - 1; i++) {
      const from = entries[i]
      const to = entries[i + 1]
      const startMs = Date.parse(from.ts)
      const endMs = Date.parse(to.ts)
      data.push({
        value: [runIndex, startMs, endMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: from.phase,
        agent: from.agent,
        status: from.status,
        startMs,
        endMs,
        isLive: false,
        itemStyle: { color: getPhaseSegmentColor(from.phase) },
        name: from.phase ?? 'unknown',
      })
    }
    // Resolved Decision 10 (user-decided, not the plan's original default): every run — live or
    // settled — always gets one trailing segment covering its final phase, so no phase is ever
    // invisible on the chart. A live run's trailing segment runs to `nowIso` in
    // `LIVE_SEGMENT_COLOR`; a settled run's trailing segment runs to `run.end_ts` in its last
    // entry's own phase color. If a settled run has no `end_ts` yet (still null — should not
    // happen for a genuinely non-active run, but guarded defensively), no trailing segment is
    // added rather than fabricating an end time.
    if (run.is_inferred_active) {
      const lastEntry = entries[entries.length - 1]
      const startMs = lastEntry ? Date.parse(lastEntry.ts) : Date.parse(run.inferred_start_ts ?? nowIso)
      data.push({
        value: [runIndex, startMs, nowMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: lastEntry?.phase ?? null,
        agent: lastEntry?.agent ?? null,
        status: run.final_status,
        startMs,
        endMs: nowMs,
        isLive: true,
        itemStyle: { color: LIVE_SEGMENT_COLOR },
        name: 'live',
      })
    } else if (entries.length > 0 && run.end_ts !== null) {
      const lastEntry = entries[entries.length - 1]
      const startMs = Date.parse(lastEntry.ts)
      const endMs = Date.parse(run.end_ts)
      data.push({
        value: [runIndex, startMs, endMs],
        runId: run.run_id,
        tier: run.tier,
        workflow: run.workflow,
        phase: lastEntry.phase,
        agent: lastEntry.agent,
        status: run.final_status,
        startMs,
        endMs,
        isLive: false,
        itemStyle: { color: getPhaseSegmentColor(lastEntry.phase) },
        name: lastEntry.phase ?? 'unknown',
      })
    }
  })

  return {
    yAxis: { type: 'category', data: sortedRuns.map((r) => r.run_id) },
    xAxis: { type: 'time' },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0 },
      { type: 'slider', xAxisIndex: 0 },
    ],
    tooltip: {
      formatter: (params: { data?: ChartSegmentDatum }) => buildTooltipHtml(params, glossary),
    },
    series: [
      {
        type: 'custom',
        renderItem: ganttRenderItem,
        encode: { x: [1, 2], y: 0 },
        data,
      },
    ],
  }
}
```

`getPhaseSegmentColor` imports `getPhaseColor`/`PHASE_PALETTE` from `@/lib/phasePalette` and falls
back to a neutral gray for a `null`/unrecognized phase string (defensive only — every real phase
string in `entriesByRun` should already be one of the 21 governed keys):

```ts
import { getPhaseColor, type WorkflowPhase } from '@/lib/phasePalette'

function getPhaseSegmentColor(phase: string | null): string {
  if (phase === null) return '#5c6070'
  try {
    return getPhaseColor(phase as WorkflowPhase)
  } catch {
    return '#5c6070'
  }
}
```

`ganttRenderItem` is the standard ECharts custom-series Gantt `renderItem` pattern (matches
ECharts' own documented "Profile"/Gantt example — implementer should confirm the exact
`echarts.graphic.clipRectByRect` import path against the installed `echarts@6.1.0`'s
`echarts/core` exports during Implement):

```ts
function ganttRenderItem(params: any, api: any) {
  const categoryIndex = api.value(0)
  const start = api.coord([api.value(1), categoryIndex])
  const end = api.coord([api.value(2), categoryIndex])
  const height = api.size([0, 1])[1] * 0.6

  const rectShape = clipRectByRect(
    { x: start[0], y: start[1] - height / 2, width: end[0] - start[0], height },
    { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height },
  )

  return rectShape && { type: 'rect', transition: ['shape'], shape: rectShape, style: api.style() }
}
```

**Per Resolved Decision 10** (user-decided), this Step's segment-building loop produces N segments
for N entries, not N-1: the `entries[i]→entries[i+1]` loop produces N-1 inter-entry segments as
before, and the `else if` branch above adds the Nth (final) segment for every settled run with at
least one entry and a real `end_ts` — matching the live-run branch's shape (which already produced
its own final segment via the `is_inferred_active` path). No run's final phase is ever left
unrendered.

**Do NOT touch:** `phasePalette.ts`'s existing exports (`getPhaseColor`/`PHASE_PALETTE`/
`PHASE_FAMILY` read-only, never modified). Do not import `mergeAndSortRuns` from `api.ts` (not
exported; see Resolved Decision 6).

**Verify:** Step 6's `toChartOption.test.ts`.

---

### Step 3 — Create `ProgressTimelineView.tsx`
**Files:** `dashboard-frontend/src/views/ProgressTimelineView.tsx` (new)

**Change:** New file, replacing `RecentActivityGantt.tsx`'s role:

```tsx
import { useEffect, useState } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useRunsPolling, useRunTimelinesPolling, useGlossary } from '@/api'
import { toChartOption } from '@/lib/toChartOption'

echarts.use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const SINCE_WINDOW_MS = 24 * 60 * 60 * 1000
const NOW_TICK_MS = 1000

export interface ProgressTimelineViewProps {
  onSelectRun: (runId: string) => void
}

export function ProgressTimelineView({ onSelectRun }: ProgressTimelineViewProps) {
  const [sinceIso] = useState(() => new Date(Date.now() - SINCE_WINDOW_MS).toISOString())
  const [nowIso, setNowIso] = useState(() => new Date().toISOString())
  const { runs } = useRunsPolling(sinceIso)
  const { entriesByRun } = useRunTimelinesPolling(sinceIso)
  const glossary = useGlossary()

  useEffect(() => {
    const timer = setInterval(() => setNowIso(new Date().toISOString()), NOW_TICK_MS)
    return () => clearInterval(timer)
  }, [])

  const option = toChartOption(runs, entriesByRun, nowIso, glossary)

  const onEvents = {
    click: (params: { data?: { runId?: string } }) => {
      const runId = params?.data?.runId
      if (typeof runId === 'string') {
        onSelectRun(runId)
      }
    },
  }

  return (
    <div data-testid="progress-timeline-view" className="flex flex-col h-full p-4">
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        onEvents={onEvents}
        style={{ height: '100%', width: '100%' }}
        notMerge
      />
    </div>
  )
}
```

`notMerge` is set so each `nowIso`-driven re-render replaces the option wholesale (needed for the
live segment's end-time to actually advance each tick — ECharts' default merge behavior would
otherwise not extend an existing data point's value array reliably across renders).

**Do NOT touch:** `RecentActivityGantt.tsx` in this step (still exists, still wired into `App.tsx`
until Step 4). Do not add filtering/grouping-by-tier/workflow controls, or any range-picker UI —
both explicitly out of scope.

**Verify:** Step 8's `ProgressTimelineView.test.tsx` smoke test.

---

### Step 4 — Wire `ProgressTimelineView` into `App.tsx`, preserving `'activity'`/`'Recent Activity'`
**Files:** `dashboard-frontend/src/App.tsx`

**Change:** Two edits only:

1. Replace the import: `import { RecentActivityGantt } from '@/views/RecentActivityGantt'` →
   `import { ProgressTimelineView } from '@/views/ProgressTimelineView'`.
2. Replace the render line (currently `{currentView === 'activity' && <RecentActivityGantt
   onSelectRun={handleSelectRun} />}`) with `{currentView === 'activity' && <ProgressTimelineView
   onSelectRun={handleSelectRun} />}`.

**Do NOT touch:** `PageView` type union, `NAV_ITEMS` (the `'activity'`/`'Recent Activity'` entry
stays exactly as-is per Resolved Decision in investigation.md's Open Question 2 and this ticket's
AC #5), `handleSelectRun`, or any other view's wiring (`TicketsView`/`StatsView`/
`ReplayTimelineView` untouched).

**Verify:** Step 9's updated `App.test.tsx` (testid-renamed assertions); manual smoke via Step 11.

---

### Step 5 — Delete retired components, their tests, and the dead CSS rule
**Files:**
- `dashboard-frontend/src/views/RecentActivityGantt.tsx` (delete)
- `dashboard-frontend/src/components/GanttBar.tsx` (delete)
- `dashboard-frontend/src/components/TimeAxis.tsx` (delete)
- `dashboard-frontend/src/components/Legend.tsx` (delete)
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (delete — replaced by
  `ProgressTimelineView.test.tsx`, Step 8)
- `dashboard-frontend/src/test/GanttBar.test.tsx` (delete)
- `dashboard-frontend/src/test/TimeAxis.test.tsx` (delete)
- `dashboard-frontend/src/index.css` (edit — remove lines 37-46, the `.gantt-bar--inferred-pattern`
  rule)

**Change:** Delete the seven files above wholesale. In `index.css`, remove only the
`.gantt-bar--inferred-pattern` block (lines 37-46) — leave the `@theme` block, `body`/`#root`
rules, and everything else untouched. This rule is not in the ticket's own Related Code Areas list
(investigation.md Risk 7 flagged it as an unlisted-but-confirmed-dead deletion target — its only
consumer, `GanttBar.tsx`, is deleted in this same step).

**Do NOT touch:** any other file under `dashboard-frontend/src/components/` or
`dashboard-frontend/src/test/` — this step is deletion-only, no other file's content changes.

**Verify:** Step 10's retirement architecture guard; `npx tsc -b --noEmit` (Step 12) reports no
dangling imports.

---

### Step 6 — `toChartOption.test.ts`
**Files:** `dashboard-frontend/src/test/toChartOption.test.ts` (new)

**Change:** Pure-function unit tests, no rendering, covering `test_plan.md`'s New Tests #1, #2,
and #4 (folded into one file per its own "same file as #1" suggestion) plus #8 (anti-drift
source-regex guard):

1. **Newest-first y-axis ordering** — construct `RunSummary[]` with distinct `start_ts`/
   `inferred_start_ts` in scrambled input order; assert `toChartOption(runs, {}, nowIso).yAxis.data`
   lists `run_id`s in the same descending order the `start_ts ?? inferred_start_ts ?? ''`/
   `localeCompare` comparator produces (reimplement the comparator directly in the test file to
   compute the expected order — do not import a private helper).
2. **N entries → N segments (per Resolved Decision 10); is_inferred_active run gets a live final
   segment instead of a settled one** — build a run with 4 `TimelineEntry` objects and a real
   `end_ts`, assert the returned `series[0].data` has exactly 4 entries for that run's `runIndex`:
   3 inter-entry segments (`isLive: false`, phase-colored) plus 1 trailing settled segment
   (`isLive: false`, colored by the 4th entry's own phase, spanning from `entries[3].ts` to
   `run.end_ts`). For an `is_inferred_active` run with the same 4 entries, assert the same 3
   inter-entry segments plus exactly one trailing entry with `isLive: true` and
   `itemStyle.color === LIVE_SEGMENT_COLOR` (imported from `toChartOption.ts`), spanning from the
   last entry's `ts` to the passed `nowIso` — the live branch replaces, not adds to, the settled
   trailing segment.
   - Edge case A: run with zero entries and `is_inferred_active: true` → exactly one live segment,
     spanning `inferred_start_ts` (or `nowIso` if null) to `nowIso`, no crash.
   - Edge case B: `run_id` present in `runs` but absent from `entriesByRun` (no key at all, not
     just an empty array) → `entriesByRun[run.run_id] ?? []` must not throw; produces zero settled
     segments (plus a live segment only if `is_inferred_active`).
   - Edge case C: settled run (not `is_inferred_active`) with `end_ts: null` → no trailing segment
     appended (only the N-1 inter-entry segments), per Step 2's defensive `end_ts !== null` guard —
     this should not occur for a genuinely non-active run in production, but must not crash if it
     does.
3. **Tooltip formatter (via `buildTooltipHtml`)** — call `buildTooltipHtml({ data: <fixture> },
   glossary)` directly: (a) with a populated `glossary` containing entries for the fixture's
   `phase`/`agent`, assert the returned HTML string contains `run_id`, `tier`, `workflow`, `phase`,
   `agent`, `status`, and a formatted duration, plus both description lines (HTML-escaped); (b)
   with `glossary = {}`, assert the same seven base fields are present with no description
   `<div>` line and no thrown error.
4. **Anti-drift: no `Date.now()`/`new Date()` re-derivation of activity** — source-regex the raw
   text of `toChartOption.ts` (via a `?raw` Vite import, mirroring the deleted `GanttBar.test.tsx`
   guard's approach) asserting no `Date.now()` or `new Date(` call appears, and that the live-
   segment branch is gated on `run.is_inferred_active` (regex for that literal conditional).

**Do NOT touch:** any other test file in this step.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/toChartOption.test.ts`.

---

### Step 7 — `useRunTimelinesPolling.test.ts`
**Files:** `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts` (new)

**Change:** Mirror `useRunsPolling.test.ts`'s exact structure (`renderHook`, mocked
`globalThis.fetch`), adapted to the bulk shape per `test_plan.md` New Test #7:

1. **Paginates when a page reaches `RUN_TIMELINES_PAGE_LIMIT`** — first page returns
   `entries_by_run` with 100 keys, second page returns 1 more key; assert `mockFetch` called
   twice, final `entriesByRun` is the union of both pages' keys (101 total), not last-page-wins.
2. **Does not issue a second request when the first page is under the limit** — single page with
   1 key; assert `mockFetch` called once.
3. **Error handling** — `mockFetch` rejects; assert `error` is set and `isLoading` becomes `false`,
   matching `useRunsPolling`'s existing `isLoading`/`error` shape.

**Do NOT touch:** `useRunsPolling.test.ts` itself.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/useRunTimelinesPolling.test.ts`.

---

### Step 8 — `ProgressTimelineView.test.tsx`
**Files:** `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` (new)

**Change:** Mock `echarts-for-react/lib/core` (the exact module path `ProgressTimelineView.tsx`
imports — mocking the default `echarts-for-react` export instead would silently pass while the
real code path still runs the wrong entry point) to capture the `option`/`onEvents`/`echarts`
props passed to it, per investigation Risk 5 (jsdom has no real canvas support — no test may
inspect real canvas output):

```tsx
vi.mock('echarts-for-react/lib/core', () => ({
  default: vi.fn((props: any) => {
    capturedProps = props
    return <div data-testid="mocked-echarts" />
  }),
}))
```

Also mock `@/api`'s `useRunsPolling`, `useRunTimelinesPolling`, and `useGlossary` (same
`vi.mock('@/api', async (importOriginal) => ...)` pattern `RecentActivityGantt.test.tsx` already
uses for `useRunsPolling`).

Tests (per `test_plan.md` New Test #3 and #6):

1. **Exactly one `ReactEChartsCore` render, with two dataZoom entries** — assert the mocked
   component was invoked exactly once per render cycle and `capturedProps.option.dataZoom` has
   exactly two entries, `type: 'inside'` and `type: 'slider'`.
2. **No network call triggered by a `dataZoom` interaction** — since both `dataZoom` entries are
   purely declarative option fields (no `onEvents.datazoom` handler is wired in
   `ProgressTimelineView.tsx`), assert `capturedProps.onEvents` has no `datazoom`/`dataZoom` key at
   all — a future accidental addition of such a handler that calls `fetch` is what this guards
   against.
3. **Row click navigates via `onSelectRun`** — invoke `capturedProps.onEvents.click({ data: {
   runId: 'run-nav-target', /* ...other ChartSegmentDatum fields... */ } })` directly (simulating
   an ECharts click event) and assert the `onSelectRun` prop mock was called with exactly
   `'run-nav-target'`.
4. **`data-testid="progress-timeline-view"` present on the root.**

**Do NOT touch:** `App.test.tsx` in this step (Step 9 handles it separately, though it may reuse
this file's mock setup pattern by reference, not by import).

**Verify:** `cd dashboard-frontend && npx vitest run src/test/ProgressTimelineView.test.tsx`.

---

### Step 9 — Update `App.test.tsx`: testid rename + row-click test restructure
**Files:** `dashboard-frontend/src/test/App.test.tsx`

**Change:**
1. Replace all 7 occurrences of `'recent-activity-gantt'` (lines 130, 142, 145, 150, 187, 197, 200
   per investigation.md's confirmed count) with `'progress-timeline-view'`. No change to any
   `getByRole('button', { name: 'Recent Activity' })` assertion.
2. Rewrite the test currently titled `'Gantt row click navigates to that run\'s Replay timeline,
   scoped to that run_id'` (L174-188). Its current body drives the click via
   `document.querySelector('[data-run-id="run-nav-target"]').closest('.relative.h-6')` — both
   artifacts of the deleted DOM/CSS rendering model, which do not exist once `ProgressTimelineView`
   renders via ECharts custom series (per investigation.md Risk 3, a testid rename alone cannot fix
   this). Replace with the same `echarts-for-react/lib/core` mock-and-capture approach as Step 8's
   click test: mock the module, render `<App />` with `useRunsPolling` returning a fixture run
   `{ run_id: 'run-nav-target', ... }`, capture the `onEvents.click` handler passed to the mocked
   `ReactEChartsCore`, invoke it with a synthetic `{ data: { runId: 'run-nav-target' } }` event
   object, then assert (same as before) `screen.findByTestId('replay-timeline-view')` resolves and
   `mockedFetchRunTimeline` was called with `'run-nav-target'`.
3. Rename the test title from `'Gantt row click navigates...'` to `'Progress timeline row click
   navigates to that run\'s Replay timeline, scoped to that run_id'` (drop stale "Gantt" naming
   from the test description itself, consistent with the ticket's own "dropping the 'Gantt'
   naming" framing).

**Do NOT touch:** the `'header wraps...'`, `'App-shell scaffold smoke test...'`, `'row-link
navigates...'` (Tickets-view-originated), or `'Stats tab renders...'` tests' core assertions beyond
the mechanical testid string swap — their `getByRole`/`getByText` assertions are unaffected by this
ticket.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/App.test.tsx`.

---

### Step 10 — Retirement architecture guard
**Files:** `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`

**Change:** Add one new test function, reusing the existing `_frontend_source_files()` helper
(per Resolved Decision 7):

```python
def test_gantt_components_fully_retired() -> None:
    import re

    retired_component_paths = [
        "dashboard-frontend/src/components/GanttBar.tsx",
        "dashboard-frontend/src/components/TimeAxis.tsx",
        "dashboard-frontend/src/components/Legend.tsx",
        "dashboard-frontend/src/views/RecentActivityGantt.tsx",
    ]
    for rel_path in retired_component_paths:
        assert not (_FRONTEND_ROOT.parent.parent / rel_path).exists(), (
            f"{rel_path} must be deleted — retired by TCK-20260720-PROGRESS-TIMELINE-VIEW"
        )

    forbidden_import = re.compile(
        r"""from\s+['"]@/(components/(GanttBar|TimeAxis|Legend)|views/RecentActivityGantt)['"]"""
    )
    to_percent_call = re.compile(r"\btoPercent\(")
    violations: list[str] = []
    for path in _frontend_source_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(_FRONTEND_ROOT.parent.parent)
        if forbidden_import.search(text):
            violations.append(f"{rel} imports a retired Gantt component")
        if to_percent_call.search(text):
            violations.append(f"{rel} still calls toPercent(), which was deleted with GanttBar.tsx")
    assert not violations, "\n".join(violations)
```

**Do NOT touch:** `test_dashboard_frontend_never_references_simulation_api_surface`,
`test_echarts_dependencies_declared_in_package_json`,
`test_no_source_file_imports_full_echarts_bundle`, `_FORBIDDEN_PATHS`, or
`_frontend_source_files()` itself — only add the one new function.

**Verify:** `python3 -m pytest
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q`.

---

### Step 11 — Browser verification (mandatory, distinct from vitest/tsc)

**This step is required before the ticket can be considered done.** For a rendering-heavy UI
change like this one, type checking and vitest suites verify code correctness, not feature
correctness. A mocked `echarts-for-react` smoke test (Step 8) proves the component *wires* ECharts
correctly; it does not prove the chart actually *renders* a legible, interactive Gantt-style
timeline in a real browser.

**Change:** none (verification only). From `dashboard-frontend/`:

```
npm run dev
```

Then, using a real browser (or a screenshot/browser-automation tool if available in this
environment — e.g. `claude-in-chrome`) against the dev server's local URL:

1. Click the **"Recent Activity"** nav button (label unchanged per Resolved Decisions) and confirm
   the view that renders is the new ECharts-based timeline, not the old div/CSS bars.
2. Confirm one row (y-axis category) per run visible in the current 24h window, with visually
   distinct phase-colored segments along each row.
3. If any run is currently active/in-progress (or trigger one via the existing dev workflow if
   the environment supports it), confirm its trailing segment renders in the distinct
   `LIVE_SEGMENT_COLOR` (`#5b6178`), visibly different from the 21 `PHASE_PALETTE` colors.
4. Hover a segment and confirm the tooltip shows `run_id`, `tier`, `workflow`, `phase`, `agent`,
   `status`, and duration — and, where a glossary entry exists for that phase/agent, the
   description line beneath.
5. Drag both the inside (in-chart) and slider (bottom) `dataZoom` controls and confirm the chart
   pans/zooms with no new network request fired (check the browser's Network tab — no new
   `/api/runs`-family request should appear beyond the existing 5s polling cadence already running
   in the background).
6. Click a segment and confirm the app navigates to the Replay tab scoped to that run (matching
   the preserved `onSelectRun` behavior).

If any of these fail visually even though vitest/tsc pass, treat it as a real defect in Steps 2-4,
not a test-authoring problem — fix the implementation, not just the mock. Record the outcome
(pass, or specific defects found and fixed) in the ticket's Implementation Notes before Finalize.

**Do NOT** substitute this step with only running `npm run test -- --run` and `npx tsc -b
--noEmit` — both are necessary but insufficient for a UI-rendering ticket.

**Verify:** direct visual/interactive confirmation of items 1-6 above, in a real browser against
the running dev server.

---

### Step 12 — Full scoped regression run
**Files:** none (verification only)

**Change:** none — run, in order:

```
cd dashboard-frontend && npm run test -- --run
npx tsc -b --noEmit
npm run build
```

then from the repo root:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_ingest.py -q
```

Never run the full `pytest tests/` — scope stays to the dashboard-facing guard/backend files per
`test_plan.md`'s Scoped Pytest Commands. `npm run build` also serves as the practical confirmation
that Resolved Decision 1's core-entry-point choice actually tree-shakes (a bundle-size regression
back to the full `echarts` bundle would be visible in its output, though no automated size-diff
assertion exists in this ticket's scope).

**Do NOT touch:** any file outside Steps 1-10 — this step is verification-only. Confirm zero
regressions in `useRunsPolling.test.ts`, `phasePalette.test.ts`, `GlossaryTooltip.test.tsx`,
`TicketsView.test.tsx`, `StatsView.test.tsx`, `ReplayTimelineView.test.tsx` (none import anything
this ticket touches).

**Verify:** all commands pass.

---

### Step 13 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add one new entry (per Resolved Decision 9). Re-check the true next-free ID at
implementation time (`grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5`).
Entry shape, following `INFRA-301`/`INFRA-302`'s exact field set:

- `status: verified`
- `priority: P2`
- `text`: describes `ProgressTimelineView.tsx` replacing `RecentActivityGantt.tsx`, the new
  `useRunTimelinesPolling` hook (two independent polling hooks feeding `toChartOption`), the pure
  `toChartOption`/`buildTooltipHtml` transform, the `echarts-for-react/lib/core` tree-shaken entry
  point correction (Resolved Decision 1), the component-local `LIVE_SEGMENT_COLOR`, and the
  deletion of `GanttBar`/`TimeAxis`/`Legend`/`toPercent()`.
- `v2_evidence`: cite post-implementation line numbers in `api.ts` (Step 1), `toChartOption.ts`
  (Step 2), `ProgressTimelineView.tsx` (Step 3), `App.tsx` (Step 4), and the deleted-file
  confirmations.
- `proof_type: regression`
- `test_path`: `dashboard-frontend/src/test/toChartOption.test.ts` (the segment-count/tooltip
  contract test) — or the retirement guard's pytest path if that reads more directly as the
  "did the migration actually happen" proof; pick whichever the implementer judges more directly
  verifies this entry's `text` claim.
- `divergence_note: null`
- `support_boundary`: same "no simulation behavior, Mechanics Bible chapter, or engine contract
  governs this module" framing `INFRA-301`/`INFRA-302` use.

**Do NOT touch:** `INFRA-301`, `INFRA-302`, or any other existing entry — add-only. Do NOT touch
any other parity ledger file.

**Verify:** manual cross-check that `test_path` exists and passes after Steps 1-12 land; YAML
validates against `docs/parity_ledger/schema.json`.

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope section and the investigation's Anti-Drift
Hazards — none of the following may be touched by this plan:

- **Do not implement the bulk timeline endpoint or the echarts dependency/palette module** —
  `src/api/agent_ops_dashboard/{main,ingest,models}.py` and `dashboard-frontend/src/lib/
  phasePalette.ts`/`chartPalette.ts` are already DONE; this ticket only consumes them, read-only.
- **Do not build the range-control UI** (quick-range presets, custom picker) — a separate ticket.
  `SINCE_WINDOW_MS` stays a fixed 24h constant (Resolved Decision 8).
- **Do not touch `docs/guides/agent_ops_dashboard.md` or
  `docs/observability/agent_ops_dashboard_contract.md`** — both name the retiring components by
  design and are deferred to the separate C5 docs-update follow-up ticket; resist "fixing" them
  here even though they will read as stale once this ticket lands.
- **Do not modify `phasePalette.ts`'s existing 21-key `PHASE_PALETTE`/`PHASE_FAMILY` exports** —
  `LIVE_SEGMENT_COLOR` is a separate, non-categorical constant in `toChartOption.ts` (Resolved
  Decision 5), never a 22nd palette key.
- **Do not modify `useRunsPolling`, `mergeAndSortRuns`, or `fetchAllRunsSince`** in `api.ts` —
  `useRunTimelinesPolling` is new and additive; the sort-order match in `toChartOption` is a
  duplicated comparator, not a shared/imported one (Resolved Decision 6).
- **Do not import the bare `'echarts'` bundle** in any `dashboard-frontend/src` file, and do not
  use the default `echarts-for-react` export (`import ReactECharts from 'echarts-for-react'`) —
  it transitively imports the full bundle regardless (Resolved Decision 1); use
  `echarts-for-react/lib/core` + `echarts/core` + tree-shaken submodules only.
- **Do not leave `RecentActivityGantt.test.tsx`, `GanttBar.test.tsx`, or `TimeAxis.test.tsx` as
  dead files** referencing deleted source — delete all three in Step 5, same commit as the source
  deletions.
- **Do not add filtering/grouping-by-tier/workflow controls** to `ProgressTimelineView` — both
  explicitly out of scope per the ticket and the originating proposal doc.
- **Do not wire a `dataZoom` event handler that issues a network request** — both `dataZoom`
  instances stay purely declarative/client-side (Step 8's Test 2 guards this explicitly).
- **Do not change `App.tsx`'s `'activity'` `PageView` value or the visible `'Recent Activity'`
  nav label** — only the `data-testid` changes.

## Dependency Map

- **Step 1** (`useRunTimelinesPolling` in `api.ts`) — independent; first step, no dependency.
- **Step 2** (`toChartOption.ts`) — independent of Step 1; can proceed in parallel. Depends only
  on already-DONE `phasePalette.ts` and existing `api.ts` types (`RunSummary`, `TimelineEntry`,
  `GlossaryTerms`).
- **Step 3** (`ProgressTimelineView.tsx`) — depends on **Step 1** (hook) and **Step 2**
  (`toChartOption`).
- **Step 4** (`App.tsx` wiring) — depends on **Step 3**.
- **Step 5** (deletions) — depends on **Step 4** (nothing may still import the retired files by
  the time they're deleted).
- **Step 6** (`toChartOption.test.ts`) — depends on **Step 2**; independent of Steps 3-5.
- **Step 7** (`useRunTimelinesPolling.test.ts`) — depends on **Step 1**; independent of Steps 2-6.
- **Step 8** (`ProgressTimelineView.test.tsx`) — depends on **Step 3**.
- **Step 9** (`App.test.tsx` update) — depends on **Step 4** (testid must exist) and benefits from
  **Step 8**'s mock pattern being established first (same `echarts-for-react/lib/core` mock
  approach), though not a hard technical dependency.
- **Step 10** (retirement guard) — depends on **Step 5** (asserts the files are actually gone).
- **Step 11** (browser verification) — depends on **all of Steps 1-9** (needs the full feature
  working end to end in a real dev server).
- **Step 12** (regression run) — depends on all of Steps 1-10 (Step 11 is a manual/visual step,
  not part of the automated regression run, but should precede or accompany it).
- **Step 13** (parity ledger) — depends on **Step 12** (cites real post-implementation evidence).

Steps 1, 2, and 7 (after 1) / 6 (after 2) may proceed in parallel with each other; Steps 3-5, 8-9
are strictly sequential after their stated dependencies.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `toChartOption(runs, entriesByRun, nowIso)` returns one y-axis category per `run_id`, newest-first matching `mergeAndSortRuns`' sort, independent of DOM | Step 2 | `toChartOption.test.ts` test 1 |
| N entries → exactly N segments per Resolved Decision 10 (N-1 inter-entry + 1 trailing: settled runs trail to `end_ts` in the last phase's color, `is_inferred_active` runs trail to `nowIso` in `LIVE_SEGMENT_COLOR`), visually distinguishable | Step 2 | `toChartOption.test.ts` test 2 |
| `ProgressTimelineView` renders exactly one `ReactEChartsCore` instance with two `dataZoom` entries (`inside` + `slider`), no network calls on zoom/pan | Step 3, Step 8 | `ProgressTimelineView.test.tsx` tests 1-2 |
| Rewritten test suite asserts `toChartOption`'s data structure directly plus a non-null-option smoke test, drops DOM percent/`gantt-bar--*` assertions | Step 6, Step 8 | `toChartOption.test.ts`, `ProgressTimelineView.test.tsx` |
| `GanttBar.tsx`/`TimeAxis.tsx`/`Legend.tsx`/`toPercent()` deleted/no longer imported; `ProgressTimelineView` replaces `RecentActivityGantt` in `App.tsx`; `'activity'` view + `onSelectRun` click-through preserved | Step 3, Step 4, Step 5 | Step 10's `test_gantt_components_fully_retired`; `App.test.tsx` |
| tooltip.formatter surfaces `run_id`/`tier`/`workflow`/`phase`/`agent`/`status`/`duration`, plus glossary description text when available, gracefully omitted when not (Open Question 1 resolution) | Step 2 | `toChartOption.test.ts` test 3 |
| Nav testid renamed to `progress-timeline-view`, `'Recent Activity'` label/`'activity'` view unchanged (Open Question 2 resolution) | Step 4 | `App.test.tsx` |

## Anti-Drift Notes

- **`is_inferred_active` is always read directly from `RunSummary`, never re-derived.** Neither
  `toChartOption.ts` nor `ProgressTimelineView.tsx` may call `Date.now()`/`new Date()` to judge
  whether a run is currently active — Step 6's test 4 carries forward the exact guard
  `GanttBar.test.tsx` enforced before its deletion.
- **The default `echarts-for-react` export is a trap, not a shortcut.** It compiles, passes
  `test_no_source_file_imports_full_echarts_bundle` (which only scans this repo's own source, not
  `node_modules`), and even renders correctly — but silently defeats the entire tree-shaking
  premise the palette ticket's Scope text established. Always import `ReactEChartsCore` from
  `echarts-for-react/lib/core`, never the bare `echarts-for-react` package.
- **`entriesByRun[run.run_id]` must always be accessed with a `?? []` fallback**, never a bare
  index — the two polling hooks are independent 5s polls and are not guaranteed to be in sync for
  a brand-new run (investigation Risk 6).
- **`LIVE_SEGMENT_COLOR` is deliberately outside `phasePalette.ts`'s governed set** — do not later
  "clean up" by moving it into `PHASE_PALETTE`; that module's 21-key/8-family completeness test
  (`phasePalette.test.ts`) would break, and its scope is explicitly closed per the palette ticket.
- **Both `dataZoom` instances must stay declarative-only** — no `onEvents.datazoom`/`dataZoom`
  handler should ever be added that calls `fetch` or either polling hook's refresh path; that is
  the separate, out-of-scope range-control ticket's job, not this one's.
- **The tooltip's glossary description lines must degrade gracefully to absent, never to a
  rendering crash or a hardcoded fallback string** — `buildTooltipHtml` must keep working
  identically whether `glossary` is `{}` (not yet loaded) or fully populated; this is the same
  contract `GlossaryTooltip.tsx` itself follows and `api.ts`'s header comment requires project-wide
  ("no hardcoded description text anywhere in `dashboard-frontend/src/*.tsx`").
- **jsdom has no real `<canvas>` support** — no test added by this plan may assert on rendered
  pixel output; every assertion operates either on `toChartOption`'s returned data structure
  directly, or on props captured from a mocked `echarts-for-react/lib/core`.

## Deviations

**Revision 1 (blocking question raised to user during Plan, resolved before Implement).** The
original plan draft found a genuine tension between the ticket's AC #2 text (read literally: N
settled entries -> N-1 segments, no trailing segment) and `test_plan.md`'s edge-case list (which
only makes sense if a trailing segment to `end_ts` exists for settled runs too), and raised it to
the user rather than picking a reading unilaterally, per the Uncertainty Rule and this project's
established pattern of surfacing plan-blocking ambiguities rather than silently resolving them.
**The user resolved it: settled runs also get a trailing segment to `run.end_ts`** — every run,
live or settled, always renders N segments for N phase entries, so no phase is ever invisible on
the chart. This is recorded as Resolved Decision 10 above; Step 2's segment-building loop and Step
6's test 2 were written directly against this resolution (not left as a "small additive follow-up"
placeholder) before this plan was submitted for architecture review.

**Revision 2 (implementation-time deviation, Step 11 — environment tooling gap, not a scope or
design change).** Step 11 mandates "using a real browser (or a screenshot/browser-automation tool
if available in this environment — e.g. claude-in-chrome)" and states the step must not be skipped
or claimed passed without actually doing it. During Implement, the following were confirmed
unavailable in this execution environment: (1) the `claude-in-chrome` skill itself reported "the
Claude in Chrome extension is not set up" when invoked to check availability; (2) no
`mcp__claude-in-chrome__*` tools were registered (checked via `ToolSearch`); (3) no
Playwright/Puppeteer packages installed in `dashboard-frontend/node_modules`, and `npx` refused to
auto-install them without an explicit `--yes`; (4) no system browser binary present
(`google-chrome`/`chromium`/`chromium-browser` all absent via `command -v` and `dpkg -l`). Rather
than silently skip Step 11 or falsely claim a visual pass, the following non-visual verification
was substituted and is recorded here plus in the ticket's Implementation Notes: both the real
dashboard backend (`uvicorn src.api.agent_ops_dashboard.main:app` on `:8471`) and the Vite dev
server (`:5174`) were started and confirmed serving; `GET /api/runs` and `GET /api/runs/timeline`
returned real, non-empty production data from the actual agent-monitoring corpus; `App.tsx`,
`ProgressTimelineView.tsx`, and `toChartOption.ts` were confirmed served by Vite with no
compile/transform errors (200, not 500); and — the most directly load-bearing check for Resolved
Decision 1 — Vite's dependency pre-bundle directory
(`dashboard-frontend/node_modules/.vite/deps/`) was inspected and confirmed to contain only the
tree-shaken `echarts_core.js`/`echarts_charts.js`/`echarts_components.js`/`echarts_renderers.js`/
`echarts-for-react_lib_core.js` chunks, with no bare `echarts.js` or default-export
`echarts-for-react` bundle present — directly confirming the tree-shaken entry point choice holds
at the real dev-server level, not merely via the source-file regex guard. No run was
`is_inferred_active` at verification time, so the live-segment-color check (checklist item 3)
could not be exercised against real data either way. **Not verified**: actual rendered chart
legibility/colors on screen, real mouse-hover tooltip rendering, drag-based `dataZoom` interaction,
the Network-tab no-new-request check, and canvas-level click-through in a live rendered chart. This
gap is surfaced explicitly (not silently) per the Uncertainty Rule and this project's established
pattern of raising blocking/partial-verification issues rather than resolving them unilaterally —
a human or an environment with browser tooling should complete the remaining visual checks before
this ticket is treated as fully done in the way Step 11 originally intended.
