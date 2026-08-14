---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-PROGRESS-TIMELINE-VIEW
artifact_type: test_plan
tags: [dashboard, observability]
---

# Test Plan — TCK-20260720-PROGRESS-TIMELINE-VIEW

## Regression Surface

This is a `dashboard-frontend`-only change (no `src/` simulation code; the backend bulk endpoint
and phase-palette module are already DONE and untouched here). No Python simulation test suite
outside `tests/tools/` is affected.

**Unit/integration (frontend, vitest) — must keep passing, several with required edits called out:**
- `dashboard-frontend/src/test/App.test.tsx` — **requires edits, not just a pass-through.** 7
  occurrences of `getByTestId`/`queryByTestId('recent-activity-gantt')` (L130, 142, 145, 150, 187,
  197, 200) must become `'progress-timeline-view'` per this ticket's nav-testid recommendation
  (see investigation.md, Open Question 2). The `'Gantt row click navigates...'` test (L174-188)
  must be rewritten around whatever click-dispatch mechanism `ProgressTimelineView` wires (see New
  Tests Required #6) — a testid swap alone will not make it pass, since it currently drives the
  click via `data-run-id`/`.relative.h-6` DOM queries that ECharts' canvas rendering does not
  reproduce. `getByRole('button', { name: 'Recent Activity' })` assertions need no change.
- `dashboard-frontend/src/test/useRunsPolling.test.ts` — unmodified; `useRunsPolling` itself is not
  touched by this ticket.
- `dashboard-frontend/src/test/phasePalette.test.ts` — unmodified; `phasePalette.ts`'s 21-key
  `PHASE_PALETTE`/`PHASE_FAMILY` exports must not change.
- `dashboard-frontend/src/test/GlossaryTooltip.test.tsx` — unmodified; `GlossaryTooltip.tsx` itself
  is not touched (only its underlying glossary *data* is reused via `useGlossary()`).
- `dashboard-frontend/src/test/TicketsView.test.tsx`, `StatsView.test.tsx`,
  `ReplayTimelineView.test.tsx` — unrelated views sharing the same tree; must not regress from this
  change (no import of anything this ticket touches, but included since a build-breaking change
  anywhere in `dashboard-frontend/src` would surface here too).

**Deleted wholesale, not "must keep passing" — replaced by this ticket:**
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (rewritten per Scope/AC #4, effectively
  a new file testing `ProgressTimelineView`/`toChartOption` instead)
- `dashboard-frontend/src/test/GanttBar.test.tsx`, `dashboard-frontend/src/test/TimeAxis.test.tsx`
  (deleted — their source files are deleted)

**Architecture guard (Python, pytest) — scans `dashboard-frontend/src/**/*.{ts,tsx}` by glob, so it
automatically covers the new/deleted files with no test-file changes required:**
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_dashboard_frontend_never_references_simulation_api_surface`
  — confirms `ProgressTimelineView.tsx`/`useRunTimelinesPolling` never reference
  `src/api/server.py`/`src/api/read_model_cache.py`/`src/api/routes/history.py`/`src/api/ws/stream.py`.
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle`
  — **directly load-bearing for this ticket**, since `ProgressTimelineView.tsx` is the first real
  ECharts consumer. Must use `echarts/core` + tree-shaken submodule imports only
  (`echarts/charts`, `echarts/components`, `echarts/renderers` — confirmed present in
  `node_modules/echarts/` — for `CustomChart`/`TooltipComponent`/`DataZoomComponent`/
  `GridComponent`/`CanvasRenderer` respectively; exact submodule paths must be confirmed against
  the installed package's own typings during Implement).
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_echarts_dependencies_declared_in_package_json`
  — unaffected (dependency already declared by the prerequisite ticket) but re-run for completeness.
- `tests/tools/test_agent_ops_dashboard_api.py` (full file, especially
  `test_bulk_run_timeline_route_*` tests) and `tests/tools/test_agent_ops_dashboard_ingest.py` —
  backend regression surface for the bulk endpoint this ticket consumes; not modified by this
  ticket but must stay green as a sanity check that the contract this frontend work assumes is
  unchanged.

**Build/typecheck (not pytest/vitest, but part of "tests were run" per CLAUDE.md):**
- `npx tsc -b --noEmit` (project's typecheck gate)
- `npm run build` (confirms tree-shaken-only ECharts imports don't balloon the bundle; also the
  first real check that `<ReactECharts>` + `dataZoom` + `custom` series types compile against the
  installed `echarts`/`echarts-for-react` version)

## New Tests Required

Per acceptance criteria and the two resolved open questions:

1. **`toChartOption` — one y-axis category per run_id, newest-first, matching mergeAndSortRuns' sort**
   - Category: unit (vitest, pure function)
   - Verifies: given an array of `RunSummary` with distinct `start_ts`/`inferred_start_ts` values,
     `toChartOption(runs, entriesByRun, nowIso).yAxis.data` (or wherever the category axis lives in
     the returned `EChartsOption`) lists `run_id`s in the same order `mergeAndSortRuns()` would
     (descending on `start_ts ?? inferred_start_ts ?? ''`), independent of any DOM rendering.
   - Where: new `dashboard-frontend/src/test/toChartOption.test.ts` (or co-located with the view's
     test file — Plan's call; recommend a dedicated file since this is the pure-transform surface
     the AC repeatedly singles out).

2. **`toChartOption` — N settled entries produce exactly N-1 segments, plus one trailing 'live' segment for is_inferred_active runs**
   - Category: unit (vitest, pure function)
   - Verifies AC #2 literally: for a run with entries `[e0, e1, ..., e(N-1)]`, the returned custom
     series data contains exactly N-1 segments, one per consecutive `entries[i].ts →
     entries[i+1].ts` pair; for `is_inferred_active` runs, exactly one additional segment from the
     last known timestamp to `nowIso`, and that segment is visually distinguishable (different
     `itemStyle`/series identity) from any settled-phase segment — assert on the actual style/color
     value used, not just its presence.
   - Edge cases: a run with zero entries (only the live segment, or nothing if not active); a run
     present in `runs` but absent from `entriesByRun` (per investigation.md Risk 6 — must not
     throw); a settled (non-active) run whose last entry's `ts` should extend to `end_ts`, not
     `nowIso`.
   - Where: same file as #1.

3. **`ProgressTimelineView` renders exactly one `<ReactECharts>` with two dataZoom entries, no network calls on zoom/pan**
   - Category: integration/smoke (vitest + React Testing Library, with `echarts-for-react` mocked)
   - Verifies: `ReactECharts` receives a non-null `option` prop whose `dataZoom` array has exactly
     two entries, `type: 'inside'` and `type: 'slider'`; renders exactly once (`getAllByTestId` or
     mock call-count assertion, not real canvas inspection — see investigation.md Risk 5 on jsdom's
     lack of canvas support); confirms no `fetch`/polling call is triggered by simulating a
     `dataZoom` event on the mocked component (`onEvents` handlers, if any, must not call
     `fetch`/the polling hooks).
   - Where: new `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` — the direct
     replacement for `RecentActivityGantt.test.tsx`.

4. **`toChartOption` — tooltip.formatter surfaces run_id/tier/workflow/phase/agent/status/duration**
   - Category: unit (vitest, pure function or extracted formatter helper)
   - Verifies: calling the returned `tooltip.formatter` (or an extracted, independently-testable
     helper it delegates to) with a representative ECharts params object returns a string
     containing all seven required fields' values; when a glossary lookup for the segment's
     `phase`/`agent` is available, the formatter output additionally contains that description
     text (HTML-escaped); when the glossary entry is missing/not yet loaded, the formatter still
     returns the seven base fields with no thrown error and no glossary line.
   - Where: same file as #1/#2, or a dedicated `tooltipFormatter.test.ts` if the formatter is
     factored into its own exported function (recommended — keeps it independently testable
     without mounting the chart).

5. **`ProgressTimelineView`/`GanttBar`/`TimeAxis`/`Legend`/`toPercent` are fully retired**
   - Category: architecture guard
   - Verifies: `GanttBar.tsx`, `TimeAxis.tsx`, `Legend.tsx` no longer exist under
     `dashboard-frontend/src/components/`; no file under `dashboard-frontend/src` imports from any
     of those three paths or contains a `toPercent(` call; `App.tsx` imports `ProgressTimelineView`
     and no longer imports `RecentActivityGantt`.
   - Where: extend `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` with a new test
     function (same glob-scan structure it already has), or a new sibling
     `tests/tools/test_dashboard_gantt_retirement.py` — Plan's call, avoid duplicating the file-walk
     helper (same guidance the palette ticket's own test_plan.md gave for its tree-shaking guard).

6. **Row click navigates to Replay, scoped to that run's run_id (App.tsx wiring preserved)**
   - Category: integration (vitest + RTL, `echarts-for-react` mocked)
   - Verifies AC #5's "onSelectRun row-click-through to Replay preserved": with `echarts-for-react`
     mocked to capture the `onEvents` prop passed to `<ReactECharts>`, invoke the captured `click`
     handler with a synthetic params object identifying a known `run_id`, and assert
     `handleSelectRun`/`onSelectRun` was called with exactly that `run_id` — this replaces
     App.test.tsx's current DOM-`data-run-id`-query-based click test (see investigation.md Risk 3),
     which cannot be adapted by a testid rename alone.
   - Where: `App.test.tsx` (replacing the existing `'Gantt row click navigates...'` test) and/or
     `ProgressTimelineView.test.tsx` for the narrower, view-local version of the same assertion —
     Plan should pick where the canonical assertion lives to avoid duplicating the mock setup.

7. **`useRunTimelinesPolling` — pagination and merge, mirroring `useRunsPolling.test.ts`**
   - Category: unit (vitest, `renderHook`)
   - Verifies: paginates when a since-window page reaches the bulk endpoint's page limit (same
     shape as `useRunsPolling.test.ts`'s existing "paginates when... reaches the page limit" test,
     adapted to `entries_by_run` merging instead of a flat array — merged result must be a union
     across pages, not last-page-wins); does not issue a second request when the first page is
     under the limit; error handling matches `useRunsPolling`'s `isLoading`/`error` shape.
   - Where: new `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts`.

8. **Never re-derives `is_inferred_active` from raw timestamps (anti-drift guard carried forward)**
   - Category: unit (vitest, source-regex, mirrors the deleted `GanttBar.test.tsx` guard)
   - Verifies: `ProgressTimelineView.tsx`'s and `toChartOption`'s source never call `Date.now()` or
     construct `new Date()` to judge run activity; the live-segment branch is driven by
     `run.is_inferred_active` read directly from the `RunSummary`, not recomputed.
   - Where: same file as #1/#2, or folded into `ProgressTimelineView.test.tsx`.

## Scoped Pytest Commands

This ticket is entirely frontend; the only Python-side tests to re-run are the dashboard
architecture guards plus the bulk-timeline backend regression suite this ticket's frontend code
assumes is unchanged:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_ingest.py -q
```

If test #5 above is added as a new sibling file instead of extended into the existing one:

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_dashboard_gantt_retirement.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_ingest.py -q
```

Never `pytest tests/` — scope stays to the dashboard-facing guard/backend files. No other Python
test file references `dashboard-frontend/`, `RecentActivityGantt`, or the bulk timeline route.

**Frontend (primary regression surface for this ticket — not pytest, but the actual gate):**

```
cd dashboard-frontend && npm run test -- --run
npx tsc -b --noEmit
npm run build
```

Scoped narrower during active development:

```
cd dashboard-frontend && npx vitest run \
  src/test/toChartOption.test.ts \
  src/test/ProgressTimelineView.test.tsx \
  src/test/useRunTimelinesPolling.test.ts \
  src/test/App.test.tsx
```

## Anti-Drift Test Guards

- **Test 5 (retirement guard)** is the direct guard against leaving `GanttBar.tsx`/`TimeAxis.tsx`/
  `Legend.tsx`/`toPercent()` half-deleted or half-referenced — without it, a stray leftover import
  (e.g. in a forgotten test file) would only surface as a build failure, not a named, intentional
  assertion.
- **Test 8 (no client-side activity re-derivation)** carries forward the exact anti-drift contract
  `GanttBar.test.tsx` enforced today; deleting that file without an equivalent replacement would
  silently drop this guard rather than intentionally retire it — the underlying rule
  (`is_inferred_active` is backend-authoritative) still applies to the new component.
- **Test 2's "run present in `runs` but absent from `entriesByRun`" edge case** guards against the
  two-independent-polling-hooks hazard flagged in investigation.md Risk 6 — a naive
  `entriesByRun[run.run_id]` lookup with no fallback would throw or silently drop a just-started
  run from the chart the moment the two 5s polls land out of sync.
- **Test 3's "no network call on dataZoom" assertion** guards the explicit AC/proposal requirement
  that both `dataZoom` instances stay purely client-side — a future edit that wires `dataZoom` to
  re-fetch (e.g. mistakenly treating it like the separate, out-of-scope range-control component)
  would regress this silently otherwise.
- **Test 1/4's "matches mergeAndSortRuns' sort" / "no hardcoded description text" assertions** guard
  against two specific behavior-preservation requirements the ticket calls out by name — a
  different sort order or a hardcoded tooltip string would both be silent, easy-to-miss
  regressions relative to established dashboard conventions (`api.ts`'s own header comment forbids
  hardcoded glossary text anywhere in `dashboard-frontend/src/*.tsx`).
- **No test should assert on `<canvas>` pixel output or ECharts' internal rendering** — per
  investigation.md Risk 5 (jsdom has no real canvas support), every new test must operate either at
  the pure-`toChartOption`-data level or through a mocked `echarts-for-react`, never by inspecting
  real canvas pixels.
- **Existing `useRunsPolling.test.ts`, `phasePalette.test.ts`, `GlossaryTooltip.test.tsx` must show
  zero diff-driven failures** — none of their underlying modules are touched by this ticket; any
  red test there signals accidental scope creep into work explicitly owned by other, already-DONE
  tickets.
