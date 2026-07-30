---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-TIMELINE-RANGE-CONTROL
phase: done
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-TIMELINE-RANGE-CONTROL

## Title
Range-control component for the timeline (quick-range presets + custom picker)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a range-control UI placed above the timeline chart offering quick-range presets (1h/6h/24h/7d) plus a custom start/end picker, replacing today's hardcoded SINCE_WINDOW_MS = 24h default. Sets sinceIso/untilIso, which bounds what the bulk timeline endpoint fetches from the server — a distinct layer from the chart's own client-side dataZoom, and the two must not be conflated or made to drive each other.

## Scope
- Add a range-control component placed above the ProgressTimelineView chart, offering quick-range presets (1h/6h/24h/7d) plus a custom start/end picker
- Replace the hardcoded SINCE_WINDOW_MS = 24h default with the range-control's sinceIso/untilIso state, wired into useRunTimelinesPolling's fetch and bounding the bulk endpoint request via its `until` param
- Quick-range preset selection sets sinceIso = now - <preset duration> and untilIso = now, passed to the bulk timeline fetch (not just applied to chart dataZoom)
- Custom start/end picker emits zero-padded ISO 8601 UTC strings matching the backend's lexical-string-comparison convention; use a plain <input type="datetime-local"> to stay consistent with the dashboard's zero-new-npm-dependency precedent (Stats tab), since no existing date/time picker component exists today
- On initial mount with no user interaction, sinceIso/untilIso reproduce today's default (now-24h to now) — drop-in replacement with no default-behavior regression
- Keep the range-control's sinceIso/untilIso state independent from the chart's own client-side dataZoom state, verified as two separate, non-interacting layers

## Out of Scope
- Implementing the bulk endpoint's `until` param itself — this ticket only consumes it once available
- Implementing the ProgressTimelineView chart itself — this ticket only places the range-control above it and coordinates rather than independently modifying RecentActivityGantt.tsx/TimeAxis.tsx while they are being retired
- Any change to the chart's own client-side dataZoom behavior
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [x] selecting a quick-range preset (1h/6h/24h/7d) sets sinceIso = now - <preset duration> and untilIso = now, passed to the bulk timeline fetch (not just applied to chart dataZoom)
- [x] selecting a custom start/end value sets sinceIso/untilIso to ISO 8601 UTC strings (zero-padded, matching the backend's lexical-string-comparison convention) and triggers a refetch bounded by those exact values
- [x] on initial mount with no user interaction, sinceIso/untilIso reproduce today's default (now-24h to now) — drop-in replacement for SINCE_WINDOW_MS with no default-behavior regression
- [x] changing the range control's sinceIso/untilIso does not reset or couple to the chart's independent client-side dataZoom state (verified as two separate, non-interacting state layers)
- [x] this ticket's server-side bounding depends on the bulk timeline endpoint supporting an `until` query param; if that support is not yet landed, this ticket is blocked on it rather than reimplementing bounding independently

## Related Tickets
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260720-BULK-RUN-TIMELINE
- TCK-20260720-PROGRESS-TIMELINE-VIEW

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_progress_timeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/ProgressTimelineView.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/components/RangeControl.tsx
- dashboard-frontend/src/lib/timeRangePresets.ts

(Corrected during Implement per plan.md Step 9 — the ticket's original list named
`RecentActivityGantt.tsx`/`TimeAxis.tsx`/`GanttBar.tsx`/`src/api/agent_ops_dashboard/main.py`, all
either deleted by `TCK-20260720-PROGRESS-TIMELINE-VIEW` or untouched by this ticket's actual
frontend-only scope.)

## Assumptions / Open Questions
- Hard dependency on TCK-20260720-BULK-RUN-TIMELINE adding an `until` query param — its originally proposed signature (since/limit/offset only) does not list one; this ticket depends on that ticket providing it rather than independently assuming it exists
- Depends on TCK-20260720-PROGRESS-TIMELINE-VIEW's chart existing first, since the range-control is placed above it — sequencing dependency
- Backend since is compared lexically as a string, never parsed to datetime — the custom picker must emit correctly formatted, zero-padded ISO 8601 UTC strings or lexical bounding silently misbehaves
- No existing date/time picker component or npm dependency exists in dashboard-frontend/src today; a plain <input type="datetime-local"> is assumed to stay consistent with this dashboard's zero-new-npm-dependency precedent, though the original proposal doesn't state this explicitly
- TCK-20260720-PROGRESS-TIMELINE-VIEW already rewrites RecentActivityGantt.test.tsx and retires RecentActivityGantt.tsx/TimeAxis.tsx — this ticket should coordinate with that ticket rather than independently modify the same soon-to-be-retired files
- `layer: observability` chosen because this is a dashboard-frontend UI control for the agent-ops observability dashboard; no more specific registered layer fits

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260720-TIMELINE-RANGE-CONTROL/plan.md`'s 9 steps
in dependency order. No deviations from the plan's code blocks or Resolved Decisions were made;
see `plan.md`'s own "Deviations" note below for the one implementation-time clarification recorded
(line-number precision in the Step 8 parity entry, not a behavior/scope change).

**Resolved Decision 1** (hook signature shape): `useRunTimelinesPolling(sinceIso, intervalMs =
5000, untilIso?: string)` — `untilIso` appended as an optional 3rd positional parameter after the
already-defaulted `intervalMs`, per the plan. Every existing 2-arg call site
(`useRunTimelinesPolling.test.ts`'s three pre-existing tests) continues to mean
`(sinceIso, intervalMs)` unchanged — proven directly by the new "2-argument call omits until"
test. `fetchAllRunTimelinesSince(sinceIso, untilIso?)` forwards unchanged into
`fetchRunTimelines({ since, until, limit, offset })`.

**Resolved Decision 2** (`useRunsPolling` scope boundary): `useRunsPolling`/`GET /api/runs`/
`FetchRunsParams`/`fetchRuns` were left entirely untouched — no `until` param added. This is a
deliberate, permanent decision, not a gap: a new architecture-guard test in `useRunsPolling.test.ts`
reads `api.ts`'s own source via a `?raw` Vite import (mirroring `toChartOption.test.ts`'s existing
guard pattern) and asserts neither `FetchRunsParams`'s interface body nor `useRunsPolling`'s
signature line contains the word `until`. This guards against a future implementer silently
"fixing" the documented y-axis-row inconsistency (a custom picker with a past `untilIso` still
lists runs with no visible segments in-window) without a new decision record.

**Resolved Decision 3** (component extraction): `RangeControl` was extracted to its own file,
`dashboard-frontend/src/components/RangeControl.tsx`, not defined inline in
`ProgressTimelineView.tsx`, so its two independent pure concerns (preset math, datetime-local<->UTC
conversion) could be unit-tested in isolation from the mocked-ECharts view tree.

**Resolved Decision 4** (preset control shape): implemented as a button group with `aria-pressed`
toggle state, not a `<select>` — supports "no preset currently matches" (after a custom edit)
without `FilterSelect`'s defensive missing-option fallback machinery.

`timeRangePresets.ts`'s `DEFAULT_WINDOW_MS` (derived from the `'24h'` `RANGE_PRESETS` entry) is the
single source of truth for the 24h default — `ProgressTimelineView.tsx`'s old
`SINCE_WINDOW_MS = 24 * 60 * 60 * 1000` local literal was removed entirely, not duplicated.

**Step 7 (browser verification) outcome — honest substitution, tooling gap confirmed again in
this session:** Before attempting Step 7, availability was re-checked per the plan's instruction:
the `claude-in-chrome` skill reported the Chrome extension is not set up; `ToolSearch` for
`mcp__claude-in-chrome__*` returned no matching tools; `command -v google-chrome chromium
chromium-browser` all failed (exit 1). This matches the prior ticket
(`TCK-20260720-PROGRESS-TIMELINE-VIEW`)'s finding in this same environment. Per the plan's
mandated fallback, the following non-visual verification was substituted and performed for real
(not simulated):
- Started the real dashboard backend (`uvicorn src.api.agent_ops_dashboard.main:app` on
  `127.0.0.1:8471`, via the project's `.venv`) and the real Vite dev server (`npm run dev` on
  `:5174`, proxying `/api` to the backend per `vite.config.ts`).
- Confirmed all 4 changed/new frontend files transform cleanly through Vite with no compile/
  transform errors: `GET /src/components/RangeControl.tsx` → 200, `GET /src/lib/
  timeRangePresets.ts` → 200, `GET /src/views/ProgressTimelineView.tsx` → 200, `GET /src/api.ts` →
  200, plus the app root `GET /` → 200.
- Issued real `GET /api/runs/timeline` requests (both directly against :8471 and through the Vite
  proxy at :5174, i.e. the exact path a real browser would take) with `since`/`until` query values
  computed the same way the range-control's `'24h'` preset and `'1h'` preset would (real
  `date -u`-computed ISO timestamps) — both returned 200 with real production entries from the
  actual `agent-monitoring/*.jsonl` corpus, bounded correctly.
- Issued a real `GET /api/runs?since=...` request (no `until`, per Resolved Decision 2) through the
  same Vite proxy — 200, confirming `useRunsPolling`'s unbounded-above behavior still functions
  end-to-end against the live backend.
- Both servers were cleanly torn down afterward (`8471`/`5174` confirmed freed via `ss -tlnp`).

**Not verified** (same class of gap as the prior ticket, explicitly not claimed as passed): actual
rendered chart/range-control legibility and layout on screen, real mouse click/hover interaction
with the preset buttons and datetime inputs, drag-based `dataZoom` interaction, and the Network-tab
level "range-control change does not perturb dataZoom" visual check. Vitest's `RangeControl.test.tsx`
and `ProgressTimelineView.test.tsx`'s range-control-integration tests exercise the equivalent logic
under jsdom + Testing Library (real `fireEvent.click`/`fireEvent.change` against real rendered DOM
nodes, not mocked), which is a meaningfully stronger substitute than a pure unit test but is still
not the same as a human/automation-driven real browser session. A human or an environment with
browser tooling should complete the remaining visual checks before treating Step 7's original intent
as fully satisfied.

## Test Summary

All new and existing tests pass. Scoped regression run (per plan.md Step 6 — never the unscoped
full suite):

```
cd dashboard-frontend && npx vitest run src/test/ProgressTimelineView.test.tsx \
  src/test/useRunTimelinesPolling.test.ts src/test/useRunsPolling.test.ts src/test/App.test.tsx \
  src/test/toChartOption.test.ts src/test/timeRangePresets.test.ts src/test/RangeControl.test.tsx
```
→ 7 files, 54 tests, all passed.

```
cd dashboard-frontend && npx tsc -b --noEmit
```
→ clean, no errors.

```
cd dashboard-frontend && npm run build
```
→ succeeded (pre-existing >500kB chunk-size warning only, unrelated to this ticket).

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```
(run via `.venv/bin/python3` — system `python3` lacks `pydantic`/project deps)
→ 16 passed, including `test_bulk_run_timeline_route_since_until_pass_through_to_cache`,
`test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id`, and
`test_gantt_components_fully_retired` (all pre-existing, unmodified by this ticket, confirmed
still green as dependency-sanity checks).

New tests added:
- `useRunTimelinesPolling.test.ts`: 2 new tests (until forwarding, 2-arg backward compatibility) —
  5 total in file now.
- `useRunsPolling.test.ts`: 1 new architecture-guard test (no-`until` regression guard) — 3 total
  in file now.
- `timeRangePresets.test.ts` (new file): 12 tests across 4 groups (computePresetRange x5,
  datetimeLocalToUtcIso x4, utcIsoToDatetimeLocalValue x2, DEFAULT_WINDOW_MS x1).
- `RangeControl.test.tsx` (new file): 7 tests (4 preset-click tests, one per preset per
  test_plan.md's per-preset coverage intent, plus custom-input emission, preset-highlight-clearing,
  inverted-range rejection).
- `ProgressTimelineView.test.tsx`: 5 new tests under a new `range-control integration` describe
  block (default-window bit-for-bit, preset-click bounded fetch, custom-picker bounded fetch,
  dataZoom independence, range-control-renders-above-chart) — 9 total in file now.

## Files Changed

- `dashboard-frontend/src/api.ts` — `fetchAllRunTimelinesSince`/`useRunTimelinesPolling` extended
  with optional `untilIso`/`until` forwarding (Step 1).
- `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts` — 2 new tests (Step 1b).
- `dashboard-frontend/src/test/useRunsPolling.test.ts` — 1 new architecture-guard test (Step 2).
- `dashboard-frontend/src/lib/timeRangePresets.ts` — new file (Step 3).
- `dashboard-frontend/src/test/timeRangePresets.test.ts` — new file (Step 3b).
- `dashboard-frontend/src/components/RangeControl.tsx` — new file (Step 4).
- `dashboard-frontend/src/test/RangeControl.test.tsx` — new file (Step 4b).
- `dashboard-frontend/src/views/ProgressTimelineView.tsx` — wired `RangeControl` + live
  `sinceIso`/`untilIso` state, removed `SINCE_WINDOW_MS` (Step 5).
- `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` — 5 new integration tests (Step 5b).
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-304` entry (Step 8).
- `tickets/inprogress/TCK-20260720-TIMELINE-RANGE-CONTROL.md` — this file, ticket hygiene (Step 9).

## Completion Summary

Added a range-control UI (four quick-range preset buttons — 1h/6h/24h/7d — plus a custom start/end
`<input type="datetime-local">` pair) above `ProgressTimelineView.tsx`'s chart, replacing the
component's fixed `SINCE_WINDOW_MS = 24h` window with live `sinceIso`/`untilIso` React state that
actually bounds the bulk timeline fetch server-side via the `until` param landed by
`TCK-20260720-BULK-RUN-TIMELINE` (INFRA-301). All 4 independent pieces from the plan were built:
`timeRangePresets.ts` (pure preset math + datetime-local<->UTC-ISO conversion, single source of
truth for the 24h default), `RangeControl.tsx` (styled per `TicketsView.tsx`'s real filter-bar
precedent), the `api.ts` hook signature extension (backward-compatible, 3rd optional positional
param), and the `ProgressTimelineView.tsx` wiring. `useRunsPolling`/`GET /api/runs` were
deliberately, permanently left un-extended with `until` (Resolved Decision 2), now guarded by a
regression test. All 5 acceptance criteria satisfied and checked off. Full scoped regression (54
Vitest tests across 7 files, clean `tsc -b`, clean `npm run build`, 16 passing scoped pytest tests)
is green. Step 7's mandatory browser verification tooling was unavailable in this environment (same
gap as the immediately-prior ticket); an honest non-visual substitution (live backend + Vite dev
server smoke test, real bounded `/api/runs/timeline` requests, clean file transforms) was performed
and is explicitly documented above and in `plan.md`'s Deviations section — actual visual/interactive
browser confirmation remains outstanding and is flagged, not silently skipped or falsely claimed.
New parity ledger entry `INFRA-304` added (add-only; `INFRA-301`/`INFRA-303` untouched).
