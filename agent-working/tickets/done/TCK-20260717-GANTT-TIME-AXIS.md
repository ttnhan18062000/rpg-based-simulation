---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-GANTT-TIME-AXIS
phase: done
date: 2026-07-17
tags: []
---

# TCK-20260717-GANTT-TIME-AXIS

## Title
Add a visible time axis and on-chart labels to the Recent Activity Gantt

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Recent Activity Gantt view renders bars as colored rectangles with zero text on them. The legend explains color meaning but nothing on the chart identifies which run a bar represents or when it happened. The hover tooltip does correctly show ticket ID, tier, workflow, duration, and agent count, but there is no time/date axis anywhere on the chart, so a user cannot tell where in the rolling window any bar falls without hovering each one individually. For a Gantt-style view this is a significant legibility gap.

## Scope
- Add a visible time axis (tick marks and/or date/time labels) to RecentActivityGantt.tsx spanning the current since/now window, computed via the same toPercent(ts, windowStartIso, windowEndIso) mapping GanttBar already uses so axis and bar positions never diverge.
- Add an on-chart text identifier (e.g. truncated run_id or start-time label) to each bar/row, additive to the existing hover tooltip — not a replacement of it.
- Handle narrow-bar label crowding (truncation/ellipsis or external label placement) for bars clamped to minimal width.

## Out of Scope
- Interactive time-window picker (Last 24h/7d/Custom) — SINCE_WINDOW_MS stays hardcoded at 24h per TCK-20260716-AGENTOPS-ACTIVITY-GANTT's existing scope guard.
- Any backend change to GET /api/runs's since-window semantics.

## Acceptance Criteria
- [ ] The Recent Activity chart renders a visible time axis (tick marks and/or date/time labels) spanning the current since/now window, independent of hovering any bar.
- [ ] Each rendered Gantt bar (or its row) carries an on-chart text identifier sufficient to distinguish it without hovering — at minimum a truncated run_id or start-time label rendered as a DOM text node, distinct from the existing tooltip content.
- [ ] Axis tick positions are computed via the same toPercent(ts, windowStartIso, windowEndIso) mapping already used by GanttBar, so axis labels and bar positions never visually diverge.
- [ ] Existing hover-tooltip content and existing authoritative/inferred bar disjoint-styling behavior (RecentActivityGantt.test.tsx's current assertions) remain unchanged/passing after the axis/label addition.

## Related Tickets
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/RecentActivityGantt.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- dashboard-frontend/src/components/Legend.tsx
- dashboard-frontend/src/test/RecentActivityGantt.test.tsx
- dashboard-frontend/src/test/GanttBar.test.tsx

## Assumptions / Open Questions
- UI_INTERACTION_SPEC.md never specified a rendered axis in the first place — this is a genuine spec gap being closed, not a regression from the original ticket.

## Implementation Notes

This ticket was implemented across two sessions (an interrupted first session and this closing session). Recorded here as the single authoritative account of the full end-to-end change.

**Session 1 (prior, interrupted after Step 3):**
- `dashboard-frontend/src/components/GanttBar.tsx`: exported the previously-module-private `toPercent(ts, windowStartIso, windowEndIso)` function (`export function toPercent(...)`), with no change to its clamping/percentage math. This let the new axis component reuse the exact same time-to-position mapping `GanttBar` uses for bar placement, satisfying AC #3 by construction (one function, two call sites) rather than by keeping two implementations in sync.
- `dashboard-frontend/src/components/TimeAxis.tsx` (new file): a presentational `TimeAxis({ windowStartIso, windowEndIso })` component rendering 7 evenly-spaced tick marks across the window. Ticks are computed as `startMs + ((endMs - startMs) * index) / (TICK_COUNT - 1)` (a duration-fraction split, not a fixed wall-clock interval), each positioned via `toPercent(tickIso, windowStartIso, windowEndIso)` imported from `GanttBar` (never redeclared), and labeled with `toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })`. Root carries `data-testid="gantt-time-axis"`; each tick carries `data-testid="gantt-time-axis-tick"`.
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`: added the `TimeAxis` import and rendered `<TimeAxis windowStartIso={sinceIso} windowEndIso={nowIso} />` as a fixed row between `<Legend />` and the scrollable Tooltip-wrapped row list, so the axis is visible independent of any hover state (AC #1) and re-renders as `nowIso` advances on the existing 1s poll tick. The existing `Tooltip.Content` block was left byte-for-byte unchanged.
- `dashboard-frontend/src/test/TimeAxis.test.tsx` (new file, 3 tests): anti-drift source-text guard (asserts the component imports `toPercent` from `@/components/GanttBar` and contains no local `function toPercent` redeclaration), a numeric-match test (a known mid-window timestamp's rendered tick `left` equals `toPercent(...)` computed directly in the test), and a no-hover-required render test.
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`: 4 tests appended (2 axis tests passing at end of session 1; 3 on-chart-label tests, added but failing, since the label itself wasn't implemented yet).

**Session 2 (this session, closing Steps 4-5 of the original plan / Steps 1-2 of the restart plan):**
- `dashboard-frontend/src/components/GanttBar.tsx`: added `<span data-testid="gantt-bar-run-label">{run.run_id}</span>` to both render branches. In the inferred-active branch it sits alongside the existing `~est.` estimate-label span. In the authoritative branch, the outer `<div>` was converted from self-closing to a container (no attribute on that div was altered) to hold the new child span. The label renders `run.run_id` verbatim with zero truncation/ellipsis logic — the already-written test asserts the full untruncated 13-character fixture id (`'run-completed'`), which a truncation scheme would have broken. The label's own testid/class is scoped to the `<span>` only, never added to either branch's outer `<div>` `className`/`classNames`, preserving the pre-existing zero-shared-class-token guarantee between inferred-active and authoritative-completed bars.
- No changes were needed to `TimeAxis.tsx`, `TimeAxis.test.tsx`, `Legend.tsx`, or the `TimeAxis` import/wiring in `RecentActivityGantt.tsx` — verified correct and left untouched.
- Full regression pass run and confirmed clean (see Test Summary).

**Session 3 (this Verify-fix round):** the doc-completeness gap flagged after Session 2 (`docs/observability/agent_ops_dashboard_contract.md` and `docs/guides/agent_ops_dashboard.md` both under-described `RecentActivityGantt`'s current composition — no mention of the axis or on-chart label) was actioned rather than left deferred. `docs/guides/agent_ops_dashboard.md`'s Recent Activity Gantt section gained a paragraph describing the fixed time axis and on-chart run-id label. `docs/observability/agent_ops_dashboard_contract.md`'s frontend SPA structure section was updated to list `TimeAxis` in `RecentActivityGantt`'s composition, document `GanttBar`'s exported `toPercent` and the new `data-testid="gantt-bar-run-label"` span, and add a `components/TimeAxis.tsx` entry. Neither is a Mechanics Bible parity issue (this view is dashboard tooling, not simulation gameplay); both are doc-only changes with no code/test impact.

**Commit-hygiene note:** the working tree also contained a separate, already-DONE ticket's (`TCK-20260717-CSS-LAYER-PADDING-FIX`) finished-but-uncommitted changes (`index.css`, `TicketsView.test.tsx`, `tsconfig.app.json`, `tsconfig.json`, `tsconfig.test.json`). These are explicitly excluded from this ticket's Files Changed and must not be folded into this ticket's commit.

**Session 4 (post-close live verification addendum):** Session 2's Implementation Notes stated the label renders `run_id` "with zero truncation/ellipsis logic," explicitly deferred because an already-written test asserted the full untruncated fixture id. That was a real gap against this ticket's own third scope bullet ("Handle narrow-bar label crowding... for bars clamped to minimal width") — confirmed live via headless-browser screenshots of `make dashboard-serve` with the full ticket corpus: long, hyphen-heavy `run_id`s inside narrow (often <1%-wide) absolutely-positioned bars were soft-wrapping at each hyphen (the browser's default line-break behavior, with no `white-space`/`overflow` constraint on the label), stacking many short lines that bled vertically into neighboring rows and made the chart unreadable.

Fix applied to `dashboard-frontend/src/components/GanttBar.tsx`: added a shared `RUN_LABEL_CLASS` (`absolute left-full top-0 ml-1 max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap text-[10px] leading-4 text-text-secondary pointer-events-none`) applied to both render branches' label span. This is CSS-only visual truncation — `position: absolute` detaches the label from the bar's own (possibly near-zero) width so it no longer inherits that width for wrapping purposes, `whitespace-nowrap` stops hyphen soft-wrapping, and `overflow-hidden`/`text-ellipsis`/`max-w-[180px]` bound it horizontally. The DOM's `textContent` is untouched (still the full, untruncated `run_id`), so Session 2's `label.textContent).toBe('run-completed')` assertion and all other existing text-content assertions remain valid and pass unmodified — only the CSS class changed.

Added 2 new tests to `GanttBar.test.tsx` (`describe('GanttBar — on-chart label never wraps or grows unbounded', ...)`) asserting both branches' label carries `whitespace-nowrap`, a `max-w-[...]` class, and `overflow-hidden`. Verified live post-fix at both 1440px and 480px viewport widths: labels now truncate cleanly with ellipsis, stay on their own row, and never overlap neighboring rows even under the full ~15-run real ticket corpus. Full regression re-run clean: 58/58 vitest (up from 45/45 — 13 net new tests across this ticket's four sessions), 47/47 backend pytest.

## Test Summary

- `cd dashboard-frontend && npx vitest run` — full 7-file suite: **45/45 passing** (up from 42 passed / 3 failed before this session's change). The 3 previously-failing tests now pass: "each rendered bar carries an on-chart run-id label distinct from the tooltip", "narrow/clamped bar label is not dropped when the bar hits its minimum width", "existing hover-tooltip content is unchanged after the on-chart label addition".
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean, no errors.
- `cd dashboard-frontend && npm run build` — production build succeeds.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -m "not slow"` — 1/1 passing; confirms no accidental import of `src/api/server.py`, `read_model_cache.py`, `routes/history.py`, or `ws/stream.py` from the frontend.
- Anti-drift guards manually re-confirmed against the actual diff: `GanttBar.test.tsx`'s raw-source `Date.now()`/`new Date()` scan (grep confirms zero matches in `GanttBar.tsx`), the zero-shared-class-token guarantee (label span's testid never added to either outer `<div>`'s `className`), `TimeAxis.test.tsx`'s `toPercent`-import guard, the tooltip-unchanged guard, and the `git diff --stat` scope guard (confirms no `SINCE_WINDOW_MS` change and no time-window-picker UI added).

## Files Changed

- `dashboard-frontend/src/components/GanttBar.tsx` (export `toPercent`; on-chart run-id label in both render branches; Session 4: `RUN_LABEL_CLASS` truncation/no-wrap styling)
- `dashboard-frontend/src/components/TimeAxis.tsx` (new)
- `dashboard-frontend/src/views/RecentActivityGantt.tsx` (`TimeAxis` import/wiring)
- `dashboard-frontend/src/test/TimeAxis.test.tsx` (new)
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (axis tests + on-chart-label tests)
- `dashboard-frontend/src/test/GanttBar.test.tsx` (Session 4: 2 new label-truncation regression tests)
- `docs/guides/agent_ops_dashboard.md` (documented the time axis and on-chart run-id label)
- `docs/observability/agent_ops_dashboard_contract.md` (documented `TimeAxis`, exported `toPercent`, and the run-id label span)

## Completion Summary

All 4 acceptance criteria are met: a visible time axis renders independent of hover and advances as `nowIso` ticks (AC #1); every bar carries an on-chart `data-testid="gantt-bar-run-label"` span, distinct from the tooltip, whose full `run_id` remains in `textContent` but is now visually truncated with ellipsis rather than left to wrap/overflow (AC #2, closed in Session 4 — see note below); axis ticks and bar positions both route through the same exported `toPercent(ts, windowStartIso, windowEndIso)` function, so they can never visually diverge (AC #3); the pre-existing tooltip content and the authoritative/inferred disjoint-styling guarantee are unchanged and still covered by passing tests (AC #4). Full regression (58/58 vitest, 47/47 backend pytest, clean `tsc -b`, clean production build) confirms no collateral breakage. `docs/guides/agent_ops_dashboard.md`'s Recent Activity Gantt section and `docs/observability/agent_ops_dashboard_contract.md`'s frontend SPA structure section were both updated to describe the new `TimeAxis` component and on-chart run-id label, closing the completeness gap flagged during Verify.

**Session 4 note:** the third scope bullet ("Handle narrow-bar label crowding... for bars clamped to minimal width") was initially shipped unimplemented — Session 2 rendered the label with no truncation, which produced hyphen-based text wrapping and cross-row visual overlap under a real, dense ticket corpus. This was caught during a post-close live-browser verification pass (not by the test suite, which only checked `textContent` presence, never visual overflow) and fixed the same day — see the Implementation Notes' Session 4 entry for the concrete CSS fix and its regression tests.
