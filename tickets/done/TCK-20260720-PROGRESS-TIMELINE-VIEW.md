---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-PROGRESS-TIMELINE-VIEW
phase: done
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-PROGRESS-TIMELINE-VIEW

## Title
New ProgressTimelineView component replacing the Gantt-style Recent Activity view

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a new ProgressTimelineView.tsx component that replaces RecentActivityGantt.tsx, dropping the 'Gantt' naming. Wraps echarts-for-react's <ReactECharts>, retiring GanttBar.tsx, TimeAxis.tsx, Legend.tsx, and GanttBar's toPercent() math. Scope includes: a useRunTimelinesPolling(sinceIso) hook (sibling to useRunsPolling) polling the new bulk timeline endpoint; a pure toChartOption(runs, entriesByRun, nowIso) transform producing one y-axis category per run_id (newest-first) with one custom-series segment per phase, plus a trailing 'live' segment for in-progress runs; two dataZoom instances (inside + slider); a tooltip.formatter (run_id, tier, workflow, phase, agent, status, duration); and a rewrite of the existing Gantt test suite.

## Scope
- Create dashboard-frontend/src/views/ProgressTimelineView.tsx replacing RecentActivityGantt.tsx in App.tsx, wrapping echarts-for-react's <ReactECharts>
- Add useRunTimelinesPolling(sinceIso) hook (sibling to useRunsPolling) polling the bulk GET /api/runs/timeline endpoint, mirroring useRunsPolling's polling/merge/sort pattern
- Add pure toChartOption(runs, entriesByRun, nowIso) transform producing one y-axis category per run_id (newest-first, matching mergeAndSortRuns' sort), one custom-series segment per phase using the new phase-color palette module, plus a trailing 'live' segment for is_inferred_active runs
- Wire two dataZoom instances (type 'inside' + type 'slider'), both purely client-side (no new network requests triggered by zoom/pan)
- Add tooltip.formatter surfacing run_id, tier, workflow, phase, agent, status, duration
- Delete GanttBar.tsx, TimeAxis.tsx, Legend.tsx and GanttBar's toPercent() math once no longer imported
- Rewrite the Gantt test suite to assert toChartOption's returned data structure directly plus a smoke test that ReactECharts receives a non-null option, dropping DOM left/width percentage and gantt-bar--* CSS class assertions
- Explicitly decide whether the new ECharts tooltip.formatter surfaces GlossaryTooltip phase/agent glossary text, given tooltip.formatter runs in a non-React/HTML-string context and existing GlossaryTooltip hover copy cannot be reused verbatim

## Out of Scope
- Implementing the bulk timeline endpoint or the echarts dependency/palette module themselves — this ticket only consumes them
- The range-control UI (quick-range presets + custom picker) — covered by a separate ticket
- Updating docs/observability/agent_ops_dashboard_contract.md and docs/guides/agent_ops_dashboard.md, which name the retiring components — deferred to the separate C5 docs-update follow-up
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [x] toChartOption(runs, entriesByRun, nowIso) returns an EChartsOption with one y-axis category per run_id, ordered newest-first (matching mergeAndSortRuns' sort), independent of DOM rendering
- [x] for N settled entries, toChartOption produces exactly N-1 segments (one per consecutive entries[i].ts -> entries[i+1].ts pair) plus, for is_inferred_active runs, exactly one additional trailing 'live' segment from the last known timestamp to nowIso, visually distinguishable from settled segments — per Resolved Decision 10 (user-decided during Plan), settled runs also get a trailing segment to end_ts, so every run always renders N segments for N entries; live-color distinguishability verified at the data/itemStyle.color level (see Implementation Notes re: Step 11 visual-verification gap)
- [x] ProgressTimelineView renders exactly one ReactECharts instance with two dataZoom entries (type 'inside' + type 'slider'), both purely client-side (no new network requests triggered by zoom/pan)
- [x] the rewritten test suite no longer asserts DOM left/width percentages or gantt-bar--* CSS classes via toPercent, asserting toChartOption's returned data structure directly plus a smoke test that ReactECharts receives a non-null option
- [x] GanttBar.tsx, TimeAxis.tsx, Legend.tsx and toPercent() are deleted/no longer imported once ProgressTimelineView.tsx replaces RecentActivityGantt.tsx in App.tsx, with the 'activity' view and onSelectRun row-click-through to Replay preserved

## Related Tickets
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC
- TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE
- TCK-20260720-BULK-RUN-TIMELINE
- TCK-20260720-ECHARTS-PHASE-PALETTE

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_progress_timeline.md
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/RecentActivityGantt.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- dashboard-frontend/src/components/TimeAxis.tsx
- dashboard-frontend/src/components/Legend.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/App.tsx
- dashboard-frontend/package.json
- dashboard-frontend/src/test/RecentActivityGantt.test.tsx
- dashboard-frontend/src/test/GanttBar.test.tsx
- dashboard-frontend/src/test/TimeAxis.test.tsx
- dashboard-frontend/src/test/App.test.tsx
- dashboard-frontend/src/test/useRunsPolling.test.ts
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py
- src/api/agent_ops_dashboard/ingest.py

## Assumptions / Open Questions
- Hard dependency on TCK-20260720-BULK-RUN-TIMELINE and TCK-20260720-ECHARTS-PHASE-PALETTE — both must land before this ticket can be implemented; this ticket cannot proceed standalone
- docs/observability/agent_ops_dashboard_contract.md and docs/guides/agent_ops_dashboard.md both describe the retiring components (RecentActivityGantt/GanttBar/Legend/TimeAxis) by name and will stay stale until the deferred C5 docs-update ticket lands; this is an explicit known-gap, not silently left unstated
- App.tsx hardcodes 'activity' as the nav view name/label tied to RecentActivityGantt — whether the nav label/testid ('Recent Activity' button text) also changes is an open implementation decision to resolve during this ticket; if changed, App.test.tsx's nav-click-flow assertions must be updated in the same ticket
- GanttBar's tooltip content was a '·'-joined string; ECharts tooltip.formatter runs in a non-React/HTML-string context, so existing GlossaryTooltip-based hover copy cannot be reused verbatim and needs its own string-formatting path
- The dataviz skill discoverability gap noted on the palette ticket is not blocking at the orchestrator level for this ticket either

## Implementation Notes

Implemented all 13 steps of `staging_artifacts/TCK-20260720-PROGRESS-TIMELINE-VIEW/plan.md` in
dependency order, following the plan's code sketches closely with the adjustments noted below.

**Step 1** — Added `BulkRunTimeline`, `fetchRunTimelines`, `fetchAllRunTimelinesSince` (100-row
offset-loop pagination, union-by-`run_id` merge across pages), and `useRunTimelinesPolling`
directly below `useRunsPolling` in `dashboard-frontend/src/api.ts` (lines 450-524), mirroring its
poll/cleanup/`isLoading`/`error` shape exactly. `useRunsPolling`, `mergeAndSortRuns`,
`fetchAllRunsSince` untouched.

**Step 2** — Created `dashboard-frontend/src/lib/toChartOption.ts` per the plan's sketch:
`LIVE_SEGMENT_COLOR` (`#5b6178`, component-local, not a `PHASE_PALETTE` key), `buildTooltipHtml`
(seven base fields + glossary description lines, gracefully omitted when absent),
`sortRunsNewestFirst` (locally reproduced comparator, does not import `mergeAndSortRuns`), and
`toChartOption` implementing Resolved Decision 10's N-segments-per-N-entries construction
(N-1 inter-entry segments via the `entries[i]->entries[i+1]` loop, plus one trailing segment —
`LIVE_SEGMENT_COLOR`/`nowIso` for `is_inferred_active` runs, or the last entry's own phase
color/`run.end_ts` for settled runs with a non-null `end_ts`). Confirmed via the installed
`echarts@6.1.0` package that `echarts/core`'s `graphic` named export includes `clipRectByRect`
(re-exported from `echarts/lib/export/api.js`'s `graphic_1`), so `ganttRenderItem` imports
`{ graphic } from 'echarts/core'` and calls `graphic.clipRectByRect(...)` rather than a separate
top-level import, since `echarts/core`'s public type surface does not export
`CustomSeriesRenderItemParams`/`CustomSeriesRenderItemAPI` directly.

**Step 3** — Created `dashboard-frontend/src/views/ProgressTimelineView.tsx` per the plan's sketch
verbatim: `echarts-for-react/lib/core` + `echarts/core` + `CustomChart`/`TooltipComponent`/
`GridComponent`/`DataZoomComponent`/`CanvasRenderer` tree-shaken imports, `echarts.use([...])`,
two independent polling hooks (`useRunsPolling`, `useRunTimelinesPolling`) plus `useGlossary()`,
`onEvents.click` forwarding `params.data.runId` to `onSelectRun`, `notMerge` on the chart so the
live segment's end time actually advances each 1s tick.

**Step 4** — `App.tsx`: swapped the `RecentActivityGantt` import/render for `ProgressTimelineView`
(2 lines only). `PageView` union, `NAV_ITEMS`, `handleSelectRun`, and every other view's wiring
untouched.

**Step 5** — Deleted `GanttBar.tsx`, `TimeAxis.tsx`, `Legend.tsx`, `RecentActivityGantt.tsx`, and
their three test files via `git rm`. Removed `index.css`'s `.gantt-bar--inferred-pattern` rule
(the exact 10-line block flagged as an unlisted-but-confirmed dead-CSS target in
`investigation.md` Risk 7); left the `@theme` block and everything else in `index.css` untouched.

**Step 6-9 (tests)** — Wrote `toChartOption.test.ts` (newest-first ordering; N-segments-per-N-
entries for both the settled-trailing-to-`end_ts` and live-trailing-to-`nowIso` cases, plus edge
cases A/A2 — zero entries + null `inferred_start_ts` fallback to `nowIso`, not in the original
edge-case list but added for full branch coverage of the `lastEntry ? ... : ...` fallback —, B, and
C; `buildTooltipHtml` with/without glossary and with absent `params.data`; the anti-drift
`Date.now()`/`new Date(`/`is_inferred_active` source-regex guard via a `?raw` import),
`useRunTimelinesPolling.test.ts` (pagination union-merge across two pages — 101 total keys, not
last-page-wins —, single-page no-second-request, and an explicit fetch-rejection error-handling
test not itemized in the plan's 3-bullet list but matching `useRunsPolling.test.ts`'s established
coverage shape), and `ProgressTimelineView.test.tsx` (mocking `echarts-for-react/lib/core`'s
default export specifically, plus `@/api`'s three hooks; asserts exactly one render, two `dataZoom`
entries, no `datazoom`/`dataZoom` key on `onEvents`, click-to-`onSelectRun`, and the root testid).

Updated `App.test.tsx`: renamed all 7 `'recent-activity-gantt'` occurrences to
`'progress-timeline-view'`; added a `vi.mock('echarts-for-react/lib/core', ...)` capturing
`onEvents`/`option`, and extended the existing `vi.mock('../api', ...)` to also stub
`useRunTimelinesPolling`/`useGlossary` (not itemized in the plan's App.tsx-mock guidance, but
necessary — `ProgressTimelineView` now calls these two hooks in addition to the already-mocked
`useRunsPolling`, and leaving them un-stubbed would have every 'activity'-view test hit the real
`fetch`, which is undefined/unroutable in jsdom); rewrote the row-click test (renamed to
`'Progress timeline row click navigates...'`) to capture and invoke `onEvents.click` on the mocked
component instead of the deleted `data-run-id`/`.relative.h-6` DOM query.

**Deviation from the plan's literal sketch (minor, test-infrastructure only, not itemized in
plan.md as a step but required to make the tests deterministic):** the row-click test in both
`ProgressTimelineView.test.tsx`-adjacent and `App.test.tsx` needed the click dispatched inside
`await act(async () => { onEvents.click(...) })` rather than a bare synchronous call. A bare call
left a transient loading-state DOM node referenced by `screen.findByTestId('replay-timeline-view')`
before `ReplayTimelineView`'s own `fetchRunTimeline` effect resolved and swapped in the loaded-state
tree (a different root node, since the loading branch returns a plain `<div>` while the loaded
branch returns a `<Tooltip.Provider><div>...`), causing a `document.body.contains(node) === false`
failure on an otherwise-valid-looking element. This is a test-only fix (no production code
changed) and is noted here since it wasn't in the plan's Step 8/9 sketches.

**Step 10** — Added `test_gantt_components_fully_retired` to
`tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, verbatim per the plan's sketch,
reusing `_frontend_source_files()`.

**Step 11 (MANDATORY browser verification) — could not be completed end-to-end; recorded as
Revision 2 in `plan.md`'s Deviations section.** No real browser, `claude-in-chrome` connection
(the skill itself reported "the Claude in Chrome extension is not set up"), Playwright/Puppeteer
install, or system browser binary was available in this execution environment (all checked
explicitly: `ToolSearch` for `mcp__claude-in-chrome__*`, invoking the `claude-in-chrome` skill,
`npx playwright`/`npx puppeteer` — both declined to auto-install, `command -v`/`dpkg -l` for
`google-chrome`/`chromium`/`chromium-browser` — none found). In place of the full 6-item visual
checklist, the following non-visual verification was performed and is the strongest available
substitute:
- Started the real dashboard backend (`.venv/bin/python3 -m uvicorn
  src.api.agent_ops_dashboard.main:app --host 127.0.0.1 --port 8471`) and the Vite dev server
  (`npm run dev`, port 5174) together, both came up cleanly with no errors.
- `GET /api/runs` and `GET /api/runs/timeline` against the live backend returned real,
  non-empty data from the actual agent-monitoring corpus (100 runs in the default page; sample
  entries with real `phase`/`agent`/`status` values `toChartOption`/`buildTooltipHtml` consume
  directly).
- Confirmed `App.tsx`, `ProgressTimelineView.tsx`, and `toChartOption.ts` are served by Vite with
  HTTP 200 (no compile/transform 500s).
- **Directly load-bearing for Resolved Decision 1**: inspected Vite's dependency pre-bundle
  directory (`dashboard-frontend/node_modules/.vite/deps/`) and confirmed it contains only
  `echarts_core.js`, `echarts_charts.js`, `echarts_components.js`, `echarts_renderers.js`, and
  `echarts-for-react_lib_core.js` — no bare `echarts.js` and no default-export
  `echarts-for-react` bundle — confirming the tree-shaken entry point choice holds at the real
  dev-server dependency-resolution level, not only via the source-file regex guard.
- No run in the live corpus was `is_inferred_active` at verification time, so the live-segment
  color check (checklist item 3) could not be exercised against real data regardless of tooling.

**Not verified** (checklist items 2, 4, 5, 6 of Step 11 specifically, and the visual half of item
3): actual on-screen chart rendering/legibility, real mouse-hover tooltip content rendering,
drag-based `dataZoom` interaction, the Network-tab no-new-request check during a drag, and
canvas-level click-through in a live rendered chart. The equivalent behavior for all of these is
covered by the mocked-`echarts-for-react` vitest suite (option shape, `onEvents` wiring, tooltip
HTML string content) but that is not the same as an actual rendered-pixel/interaction check the
plan mandates. This is a genuine, stated gap — not silently skipped — and should be closed by a
human or an environment with browser tooling before this ticket is treated as fully verified in
the sense Step 11 intended. Both background servers were stopped cleanly after verification
(`kill` on the uvicorn and vite PIDs); no dangling processes left running.

**Step 12** — Full scoped regression run, all green: `npm run test -- --run` (103/103 passed, all
12 test files, including the 4 new/modified files above), `npx tsc -b --noEmit` (clean, no
errors), `npm run build` (succeeds; single ~846 KB gzip-279 KB JS chunk — Vite warns on chunk size
but this is pre-existing/expected for this SPA and out of this ticket's scope; no automated bundle
size-diff assertion exists per the plan), and
`python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_ingest.py -q`
(56/56 passed, using `.venv/bin/python3` — the system `python3` lacks `pydantic` and cannot import
`tests/conftest.py`).

**Step 13** — Re-verified `INFRA-303` as the true next-free id (file still ended at `INFRA-302`,
no other in-flight branch work claimed it). Added the new entry to
`docs/parity_ledger/infrastructure.yaml` with `status: verified`, `priority: P2`,
`proof_type: regression`, `test_path: dashboard-frontend/src/test/toChartOption.test.ts`, and a
`support_boundary` note that explicitly states the Step 11 visual-verification gap (see above)
rather than silently omitting it. Validated the full YAML parses (`yaml.safe_load`, 308 top-level
entries) and the new entry's required fields (`v2_evidence`, `test_path` for `status: verified`)
satisfy `schema.json`. `INFRA-301`/`INFRA-302` untouched.

## Test Summary

- `cd dashboard-frontend && npx vitest run src/test/toChartOption.test.ts
  src/test/useRunTimelinesPolling.test.ts src/test/ProgressTimelineView.test.tsx
  src/test/App.test.tsx` — 25/25 passed (4 files).
- `cd dashboard-frontend && npm run test -- --run` — 103/103 passed (12 files, full frontend
  suite: zero regressions in `useRunsPolling.test.ts`, `phasePalette.test.ts`,
  `GlossaryTooltip.test.tsx`, `TicketsView.test.tsx`, `StatsView.test.tsx`,
  `ReplayTimelineView.test.tsx`).
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean, no errors.
- `cd dashboard-frontend && npm run build` — succeeds.
- `.venv/bin/python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
  tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_ingest.py -q`
  — 56/56 passed, including the new `test_gantt_components_fully_retired`.
- Step 11 mandatory browser verification: **partially completed** — see Implementation Notes for
  what was and was not verified, and `plan.md`'s Deviations "Revision 2" for the full record.

## Files Changed

**Added:**
- `dashboard-frontend/src/lib/toChartOption.ts`
- `dashboard-frontend/src/views/ProgressTimelineView.tsx`
- `dashboard-frontend/src/test/toChartOption.test.ts`
- `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts`
- `dashboard-frontend/src/test/ProgressTimelineView.test.tsx`

**Modified:**
- `dashboard-frontend/src/api.ts` (added `BulkRunTimeline`, `useRunTimelinesPolling`)
- `dashboard-frontend/src/App.tsx` (import/render swap)
- `dashboard-frontend/src/index.css` (removed dead `.gantt-bar--inferred-pattern` rule)
- `dashboard-frontend/src/test/App.test.tsx` (testid rename, echarts mock, row-click rewrite)
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` (added
  `test_gantt_components_fully_retired`)
- `docs/parity_ledger/infrastructure.yaml` (added `INFRA-303`)
- `staging_artifacts/TCK-20260720-PROGRESS-TIMELINE-VIEW/plan.md` (Deviations: Revision 2)

**Deleted:**
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`
- `dashboard-frontend/src/components/GanttBar.tsx`
- `dashboard-frontend/src/components/TimeAxis.tsx`
- `dashboard-frontend/src/components/Legend.tsx`
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
- `dashboard-frontend/src/test/GanttBar.test.tsx`
- `dashboard-frontend/src/test/TimeAxis.test.tsx`

## Completion Summary

All 13 plan steps implemented; all automated gates (vitest, tsc, build, scoped pytest) pass with
zero regressions across the frontend and dashboard backend/architecture-guard suites. The
mandatory Step 11 browser verification could **not** be completed end-to-end because no browser,
`claude-in-chrome` connection, or headless-automation tooling was available in this execution
environment — a real, stated gap, substituted with the strongest available non-visual evidence
(live backend+dev-server smoke checks against real corpus data, and direct inspection of Vite's
dependency pre-bundle confirming the tree-shaken `echarts-for-react/lib/core` entry point choice
holds in practice, not just in source). This is recorded in `plan.md`'s Deviations (Revision 2) and
above in Implementation Notes. Recommend a follow-up manual visual pass (real browser or
`claude-in-chrome` once connected) against the 6-item Step 11 checklist before treating this
ticket's UI-rendering correctness as fully closed in the sense the plan originally intended.
