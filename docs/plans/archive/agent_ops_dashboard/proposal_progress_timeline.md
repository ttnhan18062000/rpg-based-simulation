---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-20
archived: 2026-08-04
tags: [dashboard, observability, agent-monitoring]
---

# Proposal: Progress Timeline — replace the Recent Activity tab's single-color Gantt-style bars with phase/agent-segmented, zoomable timeline rows

**Maturity: PROPOSAL** — scoped through an interactive brainstorming session with the user (not
a written proposal doc authored ahead of time; this document is the output of that session,
written up for `create-tickets` to consume). User's own framing at close: "we not only find a
chart library focusing on timeline, but support timeline, in the future, we may using many other
charts" — i.e. this is explicitly scoped as an incremental feature on the existing Recent
Activity tab, but the library choice is deliberately made with future dashboard charts in mind,
not narrowly for this one view.

## Background investigation (already done, feed this to Investigate — do not redo)

**Current state of the Recent Activity tab**
(`dashboard-frontend/src/views/RecentActivityGantt.tsx`): renders one bar per run
(`RunSummary`) over a fixed 24h window, colored only by `final_status` bucket
(done/failed/neutral, via `GanttBar.tsx`'s `classifyFinalStatus`). Positioning is hand-rolled
percent math (`GanttBar.tsx`'s `toPercent()`), rendered as absolutely-positioned divs.
`TimeAxis.tsx` and `Legend.tsx` are small sibling components serving this one view. Data comes
from `useRunsPolling()` in `api.ts` (`GET /api/runs`, 5s poll interval, `since` query param
bounding the window).

**Existing single-run detail view — out of scope, do not touch.**
`ReplayTimelineView.tsx` + `PlaybackScrubber.tsx` already give an index-scrubbed (not
time-scaled) deep-dive into one run's `TimelineEntry` sequence, opened via `onSelectRun(runId)`
from the Recent Activity tab. It fetches `GET /api/runs/{run_id}/timeline`
(`fetchRunTimeline()` in `api.ts`), returning `RunTimeline{run_id, is_live, entries:
TimelineEntry[], live_tail: RawToolCall[], files_touched}`. Each `TimelineEntry` already carries
`seq, phase, agent, status, summary, ts, tool_call_count, cost_proxy_score, reason_code,
tool_calls` — this is exactly the per-phase/agent granularity this proposal needs for the main
timeline's colored segments, and it already exists; this proposal is about surfacing it in the
aggregate multi-run view, not inventing new instrumentation. This view, its component, and its
single-run endpoint are unchanged by this proposal.

**Phase vocabulary.** Phase strings originate from `tools/agent-monitoring/vocabulary.py`'s
`WORKFLOW_PHASES` — 21 deduplicated phase strings across 4 workflows (`implement-ticket`: 11
phases `Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity,
Security-Review, Verify, Finalize`; `create-tickets`: 5; `implement-epic`: 1; `simq-audit`: 7).
Each workflow's set is a Python `set` — **no defined order** — so a phase→color mapping must be
a deterministic, explicitly-authored assignment (e.g. a hand-curated ordered list per workflow,
or a stable sort), not reliant on set iteration order. `GET /api/glossary` already has a
`category="phase"` entry per phase string (`TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`,
88 total glossary terms) with authored descriptions — reuse these for tooltip/legend copy,
do not re-author phase descriptions.

**No charting library exists yet.** `dashboard-frontend/package.json` has only
`@radix-ui/react-{scroll-area,slider,slot,tabs,tooltip}`, `class-variance-authority`, `clsx`,
`react`, `tailwind-merge` — no D3/visx/echarts/vis-timeline. This proposal is the first to
introduce one.

## Library decision (already made, do not re-litigate in Investigate)

Evaluated three routes for the zoomable, phase-segmented timeline requirement, in order of
consideration:

1. **Hand-rolled extension** of `GanttBar`/`TimeAxis`'s existing percent-position div/CSS
   pattern (zero new deps). Rejected: user explicitly wants a real library rather than
   hand-building zoom/pan/range-select interaction from scratch.
2. **`timelines-chart`** (vasturiano) — a D3-based library purpose-built for exactly this data
   shape (parallel swimlanes, each with colored segments over time, built-in zoom + brush/
   overview range selector). Data model was an excellent fit, but rejected on maintenance
   grounds: ~600 GitHub stars, single maintainer, quiet since ~2024.
3. **`react-calendar-timeline`** — considered and rejected: its own repo says it is "seeking
   maintainers," and its data model (draggable/resizable items per resource row) is shaped for
   project-management Gantt charts, not dense adjacent segments per row.

**Decision: Apache ECharts (`echarts` + `echarts-for-react`).** 66k+ GitHub stars, Apache
Foundation project, ~3.2M weekly npm downloads, active release cadence. Not purpose-built for
timelines specifically, but has every needed piece as a first-class, mature feature:
- `series: [{type: 'custom', renderItem: ...}]` — the documented ECharts pattern for building
  Gantt/timeline-shaped charts: one rect per data point, time-value x-axis, category y-axis
  (one category per run = one swimlane).
- `dataZoom` component, two instances: `type: 'inside'` (scroll/pinch zoom-and-pan in place) and
  `type: 'slider'` (bottom brush/overview strip) — covers the zoom/pan and (client-side) range
  requirements as built-in, tested behavior rather than something this proposal has to build.
- Canvas renderer — scales better than hundreds of positioned DOM divs as run/segment count
  grows, which matters once a time range is zoomed in wide enough that rendered width exceeds
  viewport width (the user's own stated concern: "the actual width is much larger than the
  screen").
- `echarts.registerTheme` for mapping the dashboard's existing light/dark Tailwind tokens in.
- General-purpose: opens the door to reusing ECharts for other dashboard charts later (e.g. the
  Stats tab's `phase_status_distribution`/`spend_proxy_by_phase` tables), rather than adding a
  single-purpose dependency.

Import ECharts **tree-shaken** (`echarts/core` + only `CustomChart`, `TooltipComponent`,
`DataZoomComponent`, `GridComponent`, `CanvasRenderer`) — not the full bundle — to keep the
bundle-size cost proportionate for a project that currently has zero heavy frontend
dependencies.

**Before writing any chart/color code, load the `dataviz` skill** for phase-palette selection
discipline (categorical color formula, light/dark theming) — same constraint this dashboard's
Stats tab proposal already established for its charts.

## Architectural constraints (carry forward from the existing dashboard)

- API responses must be typed Pydantic models (`models.py`), never raw dicts — the dashboard's
  established, tested rule (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- `src/api/agent_ops_dashboard/main.py` never reads a file directly — the new bulk timeline
  endpoint's data loading belongs wherever the existing single-run
  `GET /api/runs/{run_id}/timeline` loading logic already lives (`ingest.py` or its sibling) —
  reuse that logic for the bulk path, do not duplicate entry-parsing.
- `DashboardCache`'s existing `RLock`-per-method pattern and mtime-triggered rebuild should
  extend naturally; investigate whether the bulk timeline read needs its own cache entry or can
  reuse what backs the existing per-run endpoint.
- This dashboard is read-only over `tickets/**` and `agent-monitoring/*.jsonl` — the new
  endpoint must not write anything.
- Mirror `dashboard-frontend/src/api.ts`'s own established convention: new response interfaces
  there must mirror `models.py` field-for-field (see the file's own header comment enforcing
  this), and the new bulk endpoint should follow `GET /api/runs`'s existing
  `since`/`limit`/`offset` pagination shape (`fetchAllRunsSince`'s loop-until-short-page pattern
  in `api.ts` is the precedent to mirror client-side).

## Concerns for Comprehend/Investigate to turn into child tickets

1. **New bulk run-timeline backend endpoint.** `GET /api/runs/timeline?since=&limit=&offset=`
   returning `{entries_by_run: Record<run_id, TimelineEntry[]>}` for every run in the requested
   window — a bulk sibling of the existing per-run `GET /api/runs/{run_id}/timeline`, reusing its
   entry-loading logic rather than reimplementing it, paginated the same way `GET /api/runs`
   already is. New typed Pydantic response model in `models.py`.

2. **Add the ECharts dependency and a phase→color palette module.** Add `echarts` +
   `echarts-for-react` to `dashboard-frontend/package.json` (tree-shaken imports only, per the
   Library Decision section above). Define a deterministic phase→color mapping covering all 21
   `WORKFLOW_PHASES` strings (source of truth: `tools/agent-monitoring/vocabulary.py`) — must be
   an explicitly-authored deterministic assignment, not reliant on Python `set` iteration order.
   Load the `dataviz` skill before authoring the palette. This is a prerequisite for concern 3.

3. **New `ProgressTimelineView.tsx` component, replacing `RecentActivityGantt.tsx`.** Drop
   "Gantt" naming for this feature (it is explicitly not a project-management Gantt with
   dependencies/drag-resize — it's a timeline view of run progress). Wraps `echarts-for-react`'s
   `<ReactECharts>`. Retires `GanttBar.tsx`, `TimeAxis.tsx`, `Legend.tsx`, and `GanttBar`'s
   `toPercent()` — ECharts owns axis rendering, positioning, zoom, and legend. Includes:
   - `useRunTimelinesPolling(sinceIso)` hook in `api.ts` (sibling to `useRunsPolling`), polling
     concern 1's bulk endpoint on the same interval.
   - Pure transform function `toChartOption(runs, entriesByRun, nowIso) → EChartsOption`: one
     y-axis category per `run_id` (newest-first, matching `mergeAndSortRuns`'s existing sort),
     one custom-series data point per phase segment computed from consecutive
     `entries[i].ts → entries[i+1].ts` (last entry runs to `end_ts`; for `is_inferred_active`
     runs, settled phases render as normal colored segments followed by one visually-distinct
     trailing "live" segment covering unattributed `live_tail` activity to `nowIso`, mirroring
     today's `~est.` treatment).
   - Two `dataZoom` instances (`inside` + `slider`) operating client-side on already-fetched
     data.
   - `tooltip.formatter` showing `run_id`, `tier`, `workflow`, `phase`, `agent`, `status`,
     duration — equivalent info to today's Radix tooltip content in `RecentActivityGantt.tsx`.
     This replaces Radix Tooltip for this view only; Radix Tooltip is unaffected elsewhere
     (`ReplayTimelineView`, `GlossaryTooltip`).
   - Rewrite `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (and any
     `GanttBar`/`TimeAxis`-specific tests) against the new pure transform function's output shape
     and light integration/smoke tests for the chart wrapper — the existing suite asserts DOM
     position/CSS classes via `toPercent()`, which no longer applies once ECharts owns internal
     rendering.

4. **Range-control component**: quick-range presets (1h/6h/24h/7d, replacing today's hardcoded
   `SINCE_WINDOW_MS = 24h` default) plus a custom start/end picker, placed above the timeline
   chart. Sets `sinceIso`/`untilIso`, which bounds what concern 1's bulk endpoint fetches — a
   distinct layer from the chart's own client-side `dataZoom`, not a competing control.

5. **Docs update.** Whichever doc(s) describe the Recent Activity tab today (check
   `docs/guides/agent_ops_dashboard.md` and `docs/observability/agent_ops_dashboard_contract.md`,
   mirroring how the Stats tab's own addition was documented) need updating to describe the new
   Progress Timeline view, the new bulk endpoint, and the retirement of the Gantt-named
   components.

## Explicitly out of scope

- Filtering by phase/agent/tier/status — user explicitly declined this ("no need to filter
  anything, we just need timeline-related features").
- Grouping/lanes by tier or workflow beyond the natural one-lane-per-run layout — not requested.
- Any change to `ReplayTimelineView.tsx` / `PlaybackScrubber.tsx` — stays exactly as-is, still
  opened via the same `onSelectRun` click, confirmed explicitly with the user ("Keep
  ReplayTimelineView as-is, unchanged").
- Any change to the single-run `GET /api/runs/{run_id}/timeline` endpoint — concern 1 adds a
  bulk sibling, it does not modify the existing endpoint.
- Any new agent-monitoring instrumentation or schema change — this proposal only surfaces
  `TimelineEntry` data that already exists in `agent-monitoring/*.jsonl` via the existing
  ingest/cache path.
