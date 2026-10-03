---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-TIMELINE-RANGE-CONTROL
artifact_type: test_plan
tags: [dashboard, observability]
---

# Test Plan — TCK-20260720-TIMELINE-RANGE-CONTROL

## Regression Surface

Existing tests that must keep passing, grouped by type. All are frontend (Vitest); no Python regression surface — the backend `until` param is already fully implemented and tested by INFRA-301's suite, out of scope to re-verify here except as a pass-through consumer.

**Unit (hooks, `dashboard-frontend/src/test/`):**
- `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts` — all 3 existing tests (pagination union-merge, single-page-no-second-request, error handling) call `useRunTimelinesPolling(sinceIso, intervalMs)` positionally with 2 args (`'2026-07-15T00:00:00Z', 999_999_999`). **These calls must keep working unchanged** after the signature change (this pins down which signature-shape option from investigation.md's Open Question 1 is safe vs. destructive — see New Tests below).
- `dashboard-frontend/src/test/useRunsPolling.test.ts` — both existing tests, same positional-2-arg shape. Only needs re-verification if Plan decides to extend `useRunsPolling` too (investigation.md Open Question 2).

**Integration (component, `dashboard-frontend/src/test/`):**
- `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` — all 4 existing tests (single-echarts-instance + 2-dataZoom-entries, no-datazoom-onEvents-handler, row-click-navigates, root data-testid). These mock `useRunsPolling`/`useRunTimelinesPolling`/`useGlossary` entirely via `vi.mock('@/api', ...)`, so they are largely insulated from internal hook signature changes — but the **new range-control markup added above the chart must not break `screen.getAllByTestId('mocked-echarts')` returning exactly 1** or any other existing assertion in this file.
- `dashboard-frontend/src/test/App.test.tsx` — full-app integration tests including `navTargetTimeline()`/`mockStatsFetch()`/ProgressTimelineView-as-default-view assertions. Must keep passing with the range-control mounted.
- `dashboard-frontend/src/test/toChartOption.test.ts` — untouched by this ticket (confirmed `toChartOption.ts` is out of scope); must still pass as a pure regression check that nothing here accidentally touched it.

**Architecture guard:**
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_gantt_components_fully_retired` — confirms `GanttBar`/`TimeAxis`/`Legend`/`RecentActivityGantt` stay deleted and unreferenced. Must keep passing; this ticket must not resurrect any import of them (guards against the stale-Related-Code-Areas hazard flagged in investigation.md).
- `tests/tools/test_agent_ops_dashboard_api.py::test_bulk_run_timeline_route_since_until_pass_through_to_cache` and `::test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id` — backend `until` plumbing this ticket depends on; not modified by this ticket, run as a dependency-sanity check, not because this ticket changes them.

## New Tests Required

Per acceptance criteria (ticket's 5 checkboxes):

1. **Test name:** `quick-range preset click sets sinceIso/untilIso and triggers a bounded fetch`
   **Category:** integration
   **Verifies:** AC #1 — selecting each of 1h/6h/24h/7d calls `useRunTimelinesPolling` (or the underlying `fetchRunTimelines`/mocked fetch, depending on final component boundary) with `sinceIso` ≈ `now - <preset duration>` and `untilIso` ≈ `now`, not just a `dataZoom`/chart-only effect. Use fake timers (`vi.useFakeTimers()` + `vi.setSystemTime(...)`) to make "now" deterministic and assert exact ISO values, not approximate/tolerant ranges.
   **Where:** `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` (if range-control stays inline) or a new `dashboard-frontend/src/test/RangeControl.test.tsx` (if extracted per investigation.md Open Question 4) plus an integration assertion in `ProgressTimelineView.test.tsx` either way.

2. **Test name:** `custom start/end datetime-local input emits zero-padded UTC ISO strings and triggers a refetch bounded by those exact values`
   **Category:** unit (if the local→UTC conversion is extracted as a pure helper function — recommended, see investigation.md Risk 5) + integration (wiring)
   **Verifies:** AC #2 — the exact conversion from `<input type="datetime-local">`'s naive local-time value string to a UTC ISO string matching the backend's lexical-comparison convention (zero-padded `YYYY-MM-DDTHH:mm:ss.sssZ`). Test with at least one input whose local-time-to-UTC conversion crosses a date boundary (e.g., late-evening local time in a UTC+ timezone) to catch an off-by-one-day conversion bug, plus a straightforward same-day case. If jsdom's `datetime-local` input support proves too limited in this test environment (flagged as a real risk in investigation.md), the pure conversion helper must be unit-tested directly with string inputs rather than simulated through a real `fireEvent.change` on the input element — do not silently skip coverage if the DOM-level path is awkward to simulate.
   **Where:** new pure helper (e.g. `dashboard-frontend/src/lib/` or co-located with the range-control component) gets its own `*.test.ts`; wiring assertion goes in the range-control's own test file or `ProgressTimelineView.test.tsx`.

3. **Test name:** `initial mount with no user interaction reproduces today's default window (now-24h to now)`
   **Category:** unit or integration (regression-shaped)
   **Verifies:** AC #3 — with fake timers pinning "now", assert `sinceIso === now-24h` and `untilIso === now` on first render with zero user interaction, matching the pre-ticket `SINCE_WINDOW_MS = 24h` hardcoded behavior bit-for-bit. This is the single highest-value regression guard in this ticket — a subtle drift here (e.g. off-by-a-tick, or `untilIso` defaulting to `undefined` instead of `now`) silently changes production default behavior for every dashboard user.
   **Where:** `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` or the range-control's own test file.

4. **Test name:** `changing sinceIso/untilIso does not reset or read dataZoom state` / `dataZoom and range-control state remain independent`
   **Category:** architecture guard / anti-drift
   **Verifies:** AC #4 — extends the existing "does not wire any datazoom/dataZoom onEvents handler" test's spirit: after a range-control interaction (preset click or custom picker change) that changes `sinceIso`/`untilIso` and triggers a re-render/refetch, assert the chart option's `dataZoom` array is still exactly `[{type:'inside',...},{type:'slider',...}]` with no injected `start`/`end`/`startValue`/`endValue` derived from the range-control state, and that no `dataZoom`-reading code path exists that could feed back into `sinceIso`/`untilIso`. A static/source-level guard (grep-style architecture test asserting the range-control component/module never imports or references `dataZoom`) is a reasonable supplement if a runtime assertion is hard to construct.
   **Where:** `dashboard-frontend/src/test/ProgressTimelineView.test.tsx`, alongside the existing dataZoom tests.

5. **Test name:** `blocked-without-until-param acknowledgment is a documentation/precondition check, not a runtime test`
   **Category:** N/A — AC #5 ("this ticket's server-side bounding depends on the bulk timeline endpoint supporting an `until` query param; if that support is not yet landed, this ticket is blocked on it") is already satisfied as a precondition: confirmed via `main.py:77-84`/`ingest.py:737-770` and INFRA-301 (`status: verified`) that `until` support has already landed. No new test is needed for this AC — it is a scoping/sequencing statement already resolved by the investigation, not a behavior to assert at runtime.

6. **Test name:** `useRunTimelinesPolling forwards until to the bulk fetch query string; existing 2-arg positional call sites keep behaving as sinceIso+intervalMs`
   **Category:** unit
   **Verifies:** the hook-signature-change decision from investigation.md Open Question 1. Regardless of which shape Plan picks, this test must prove: (a) a call passing `until` results in `until=<value>` appearing in the `/api/runs/timeline?...` query string via the mocked `fetch`, and (b) every *existing* 2-positional-arg call site in `useRunTimelinesPolling.test.ts` continues to mean `(sinceIso, intervalMs)`, not `(sinceIso, untilIso)` — i.e. this test should assert against the specific chosen shape's contract, not merely "it compiles."
   **Where:** `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts` (extend existing file — new `it()` blocks, not a new file, per that file's existing convention).

7. **Test name:** `useRunsPolling / GET-/api/runs until-bounding decision is explicitly resolved` (conditional — depends on Open Question 2's resolution)
   **Category:** unit or architecture guard
   **Verifies:** whichever path Plan chooses for investigation.md Open Question 2. If `useRunsPolling` is extended with `until`: mirror test #6's shape for `useRunsPolling.test.ts`. If deliberately left `sinceIso`-only: an architecture-guard/anti-drift test asserting `FetchRunsParams`/`fetchRuns`/`useRunsPolling` still have no `until` field, so a future accidental partial-add doesn't silently create an inconsistent half-bounded state without a corresponding decision record. Either branch must be documented as an explicit choice in plan.md, not left implicit.
   **Where:** `dashboard-frontend/src/test/useRunsPolling.test.ts`.

## Scoped Pytest Commands

This ticket is frontend-only (Vitest, not pytest) for all new behavior. Scoped verification:

```
cd dashboard-frontend && npx vitest run src/test/ProgressTimelineView.test.tsx src/test/useRunTimelinesPolling.test.ts src/test/useRunsPolling.test.ts src/test/App.test.tsx src/test/toChartOption.test.ts
```

Plus, if any new standalone range-control/helper test files are created, include them explicitly by path in the same `vitest run` invocation (do not run the full `dashboard-frontend` suite unscoped).

Python regression check (dependency sanity only, not modified by this ticket — confirms the backend `until` plumbing this ticket depends on hasn't regressed):

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```

Never: `pytest tests/` or an unscoped `npx vitest run` (whole `dashboard-frontend/src/test/` directory) — both are broader than this ticket's affected domain.

## Anti-Drift Test Guards

- **`dataZoom` shape immutability test** (New Test #4 above) doubles as an anti-drift guard against the most likely scope-creep in this ticket: coupling the range-control to `dataZoom`. Keep it in the regression-run set permanently, not just as a one-time acceptance check.
- **`test_gantt_components_fully_retired`** (existing architecture guard) must be re-run as part of this ticket's verification even though this ticket doesn't touch those files, specifically because investigation.md found the ticket's own stale Related Code Areas section pointing at the deleted files — this guard is the safety net if an implementer follows the stale list instead of the real current file.
- **Default-window bit-for-bit test** (New Test #3) is the anti-regression guard for AC #3's "no default-behavior regression" — treat any change to this test's expected values as a signal requiring explicit sign-off, not a routine update.
- **`toChartOption.test.ts`'s existing "anti-drift no-`Date.now()` guard"** (referenced in INFRA-303's v2_evidence) — re-run unmodified as confirmation this ticket didn't introduce a second, inconsistent "now" source into the chart-rendering path while adding the range-control's own "now" computation for preset calculation.
