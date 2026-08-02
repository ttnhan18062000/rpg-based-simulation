---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX
phase: done
date: 2026-07-30
tags: [dashboard, observability, bug]
---

# TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX

## Title
Fix ProgressTimelineView rendering regressions found in first real-browser verification (y-axis label overflow, missing color legend, tooltip dismissed by live-tick redraw)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`ProgressTimelineView.tsx` (added by `TCK-20260720-PROGRESS-TIMELINE-VIEW`, extended by
`TCK-20260720-TIMELINE-RANGE-CONTROL`) could not get real-browser verification during its own
implementation (no browser tooling was available in that environment — an honestly-documented,
user-accepted gap at the time). The user has now manually verified it in a real browser and found
three real defects, all confirmed here by direct source inspection (not guessed):

1. **Y-axis run_id labels overflow and break the layout.** `toChartOption.ts`'s returned option has
   no `grid.containLabel: true` and no `yAxis.axisLabel.width`/`overflow` config — ECharts renders
   category labels at full, untruncated width and does not reserve grid space for them. Given how
   long real `run_id`s are in this project (e.g. `FOLDER-tickets-todos-progress-timeline`,
   `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`), long labels visibly overlap/clip the plot area.
2. **No color legend exists anywhere.** The old, now-deleted `Legend.tsx` (retired by
   `TCK-20260720-PROGRESS-TIMELINE-VIEW`, confirmed via `git show` of its pre-deletion content) showed
   a swatch+label row explaining what each rendered color meant (then: status-bucket colors). Its
   functionality was never replaced when the phase-color scheme (`phasePalette.ts`, 21 phases / 8
   families) took over — `toChartOption.ts`'s returned option has no `legend` field, and no separate
   legend UI exists. Users have no way to know what a given segment color represents.
3. **Hovering a segment shows the tooltip, which then disappears within ~1 second.** Root cause
   confirmed by direct inspection of `ProgressTimelineView.tsx`: `NOW_TICK_MS = 1000` drives a
   `setInterval` that updates `nowIso` state every second; `option` is recomputed on every render
   from that state; `<ReactEChartsCore ... notMerge>` is passed `notMerge` unconditionally. Every
   second, ECharts fully reinitializes the chart from a brand-new option object — which wipes any
   active tooltip/hover DOM state almost immediately after it appears. **Related, same-root-cause
   regression also found and in scope here:** the same per-second full-reinitialize also silently
   resets any in-progress `dataZoom` pan/zoom position the user has made, since the returned option
   never carries the current zoom `start`/`end` forward — a user cannot meaningfully use the
   dataZoom slider/inside-zoom for more than ~1 second before it snaps back to the default 0-100%
   view. This was not caught by `TCK-20260720-PROGRESS-TIMELINE-VIEW`'s or
   `TCK-20260720-TIMELINE-RANGE-CONTROL`'s own tests because both only assert `dataZoom`'s *shape*
   (two declarative entries) is unperturbed by a `sinceIso`/`untilIso` change — neither test
   exercises the recurring `nowIso` tick's own effect on interactive chart state, since the mocked
   `echarts-for-react/lib/core` in those tests never actually re-invokes ECharts' real
   `setOption`/`notMerge` behavior.

`notMerge` was a deliberate choice recorded in `TCK-20260720-PROGRESS-TIMELINE-VIEW`'s own plan.md
(the live segment's end-time needs to visibly advance each tick, and ECharts' default merge
behavior was found not to reliably extend an existing data point's value array across renders) — so
the fix must preserve that live-advancing behavior while no longer wiping interactive UI state
every second, not simply flip `notMerge` off.

## Scope
- `dashboard-frontend/src/lib/toChartOption.ts`: add `grid: { containLabel: true, ... }` and a
  `yAxis.axisLabel` config (`width`, `overflow: 'truncate'`, `ellipsis`) so long `run_id` category
  labels are truncated with an ellipsis rather than overflowing/clipping the plot area. The full
  untruncated `run_id` remains available via the existing tooltip (`buildTooltipHtml` already
  includes it) — do not remove or shorten `run_id` data itself, only its on-axis label rendering.
- `dashboard-frontend/src/lib/toChartOption.ts` and/or a new small legend module: add a color
  legend explaining segment colors. Given `phasePalette.ts`'s own design intent (21 phases
  deliberately clustered into 8 hue families specifically because a 21-entry legend would be
  excessive/illegible — see that module's header comment), the legend should show one swatch per
  family (using each family's base/lightest hex, already recorded in `phasePalette.ts`'s own
  comments) plus one additional swatch for the "live" segment color
  (`LIVE_SEGMENT_COLOR` from `toChartOption.ts`) — 9 entries total, not all 21 raw phases. Render as
  a compact row (reuse the visual convention the old, deleted `Legend.tsx` used: small rounded
  swatch + `text-[11px] text-text-secondary` label, `flex flex-wrap gap-x-4`) placed above or below
  the chart in `ProgressTimelineView.tsx`, consistent with `RangeControl`'s own placement pattern.
- `dashboard-frontend/src/views/ProgressTimelineView.tsx`: fix the tooltip/dataZoom-reset regression
  without breaking the live segment's per-second end-time advancement. Concrete approach: stop
  passing `notMerge` unconditionally on every render. Instead, capture the ECharts instance (via
  `ReactEChartsCore`'s `onChartReady`/`ref`) and drive the per-tick live-segment update through a
  lighter-weight, non-`notMerge` `setOption` call scoped to only the live data point's end value
  (or equivalent — the implementer should verify empirically in a real browser which specific
  approach actually preserves both live-segment advancement and tooltip/dataZoom stability, since
  this is exactly the kind of thing static analysis/mocked tests cannot fully validate). Only use
  `notMerge: true` for structural option changes (new run set, new entries, range-control change),
  never for the routine per-second tick.
- Investigate other related issues while in this code (explicitly requested) — in particular:
  confirm whether `RangeControl`'s own inputs or any other UI element is similarly affected by the
  per-second re-render (e.g. losing focus/cursor position while typing in a custom datetime input
  during a tick), and fix if found. Do not expand scope beyond genuinely related regressions
  discovered during this fix.

## Out of Scope
- Any change to the underlying data model, `toChartOption`'s segment-count/trailing-segment logic
  (Resolved Decision 10 from the prior ticket), or the bulk timeline endpoint.
- Any change to `RangeControl`'s own preset/custom-picker logic beyond the re-render-stability
  investigation above.
- A full per-phase (21-entry) legend — deliberately rejected per `phasePalette.ts`'s own
  design rationale; family-level (8+1) is the correct scope.
- C5 docs update (`docs/guides/agent_ops_dashboard.md`,
  `docs/observability/agent_ops_dashboard_contract.md`) — still deferred, unrelated to this fix.

## Acceptance Criteria
- [x] A `run_id` longer than the y-axis label's configured width renders truncated with an ellipsis,
  not overlapping/clipping the plot area or any other UI element; the full `run_id` remains visible
  in the tooltip.
- [x] A legend is visibly rendered (above or below the chart) showing one swatch+label per phase
  family (8 entries) plus one for the live/in-progress segment color, using the exact colors
  `toChartOption`'s segments actually render with.
- [x] Hovering a segment and holding the mouse still keeps the tooltip visible continuously for as
  long as the mouse remains over that segment — it must not disappear on its own after ~1 second
  while the mouse hasn't moved off the segment. **Verified against a real (non-mocked) ECharts
  instance's actual tooltip DOM node** (`liveTickMerge.test.ts`), not just reasoned about — see
  Implementation Notes for why a literal browser session did not additionally confirm this.
- [x] The live segment's end-time still visibly advances each second for an in-progress run (no
  regression to the behavior `notMerge` was originally added to guarantee). Verified against a real
  ECharts instance's `getOption()` output across a simulated tick.
- [x] Dragging/adjusting the `dataZoom` slider or inside-zoom holds its position for longer than one
  tick interval — it must not snap back to the default 0-100% view on its own. Verified against a
  real ECharts instance's `dataZoom` state across a simulated tick, with a control case proving the
  old `notMerge`-every-tick behavior genuinely resets it (confirming this was the real bug).
- [x] All existing `ProgressTimelineView.test.tsx`/`toChartOption.test.ts`/`RangeControl.test.tsx`
  tests continue to pass; new tests are added for whichever of the above are unit-testable
  (legend rendering, axis label truncation config, live-segment-update-without-full-reset logic).
- [x] Manually verified in a real browser (this is achievable now — the user has working browser
  access) for all five items above, not just vitest/tsc. **Checked 2026-08-02: rebuilt `dist/` fresh,
  ran the production server locally (`src/api/agent_ops_dashboard/serve.py`, port 8420), and the user
  confirmed via their own browser check against the "Recent Activity" tab that y-axis label
  truncation, the legend, tooltip-hold, and dataZoom-drag persistence all look correct. Claude in
  Chrome was considered as an automated path but is not available in this environment, so this was a
  user-performed manual check rather than an agent-driven one.**

## Related Tickets
- TCK-20260720-PROGRESS-TIMELINE-VIEW (introduced the regressions; browser verification was
  unavailable in that ticket's implementation environment)
- TCK-20260720-TIMELINE-RANGE-CONTROL (added the range-control UI now sharing the view; also
  unable to get real-browser verification)
- TCK-20260720-ECHARTS-PHASE-PALETTE (source of the 21-phase/8-family color scheme this legend
  must reflect)
- TCK-20260720-BULK-RUN-TIMELINE (source of the timeline entries this view renders)

## Related Docs
None new — no doc changes are in scope for this hotfix.

## Related Stored Artifacts
- stored_artifacts/TCK-20260720-PROGRESS-TIMELINE-VIEW/ (plan.md's Deviations/Revision 2 documents
  the original browser-verification gap this hotfix directly resolves)
- stored_artifacts/TCK-20260720-TIMELINE-RANGE-CONTROL/ (same gap, second occurrence)
- stored_artifacts/TCK-20260720-ECHARTS-PHASE-PALETTE/ (phasePalette.ts's family-clustering design
  rationale, directly informs this ticket's legend scope)

## Related Code Areas
- dashboard-frontend/src/lib/toChartOption.ts
- dashboard-frontend/src/views/ProgressTimelineView.tsx
- dashboard-frontend/src/lib/phasePalette.ts (read-only reference — do not modify its governed
  21-key/8-family exports)
- dashboard-frontend/src/components/RangeControl.tsx (read-only, unless the re-render-stability
  investigation finds a genuine related issue there)
- dashboard-frontend/src/test/ProgressTimelineView.test.tsx
- dashboard-frontend/src/test/toChartOption.test.ts

## Assumptions / Open Questions
- The exact mechanism to preserve dataZoom/tooltip stability while still advancing the live segment
  each second is left to Implement to determine empirically (via real browser testing, now
  available) rather than prescribed exactly here — ECharts' React wrapper has more than one valid
  pattern for this (imperative `getEchartsInstance()` calls, `notMerge: false` with careful data
  keying via each item's stable identity, etc.) and the right one should be chosen based on what
  actually works when tested live, not guessed from documentation alone.
- The legend's exact visual placement (above vs. below the chart, or beside `RangeControl`) is an
  implementation-time layout decision — follow the existing `RangeControl` placement convention
  unless a real usability problem is found.

## Implementation Notes

**Note on process:** this ticket's implementation was started by a subagent that was interrupted
mid-task by a session usage limit before it could finalize the ticket's own paperwork or attempt
real-browser verification. The code changes and new tests it left behind were independently
re-reviewed and re-verified (diffs read in full, tests re-run, `tsc`/`npm run build` re-run) by the
orchestrating session before this ticket was marked ready for the user's review — not rubber-stamped.

**Issue 1 (y-axis label overflow) — fixed.** `toChartOption.ts`'s returned option now sets
`grid: { containLabel: true }` and `yAxis.axisLabel: { width: 160, overflow: 'truncate', ellipsis:
'...' }`. Registering `containLabel` required adding `LegacyGridContainLabel` from
`echarts/features` to `ProgressTimelineView.tsx`'s `echarts.use([...])` call — confirmed this
export genuinely exists in the installed `echarts@6.1.0` package (echarts 6.1 split
`grid.containLabel`'s implementation into an explicit opt-in feature; without registering it,
echarts logs a console deprecation warning and falls back to a different heuristic). The
underlying `run_id` data itself is untouched — only its axis-label rendering truncates; the full
value remains in the tooltip.

**Issue 2 (missing legend) — fixed.** New `CHART_LEGEND_ENTRIES` export in `toChartOption.ts`,
derived programmatically from `phasePalette.ts`'s governed `PHASE_FAMILY`/`PHASE_PALETTE` exports
(never hand-copied hex values, so it can't silently drift) — 8 family swatches (each family's
first-listed/base-hue member) plus 1 for `LIVE_SEGMENT_COLOR`, matching `phasePalette.ts`'s own
explicit design rationale against a 21-entry legend. Rendered via a new `ChartLegend` component in
`ProgressTimelineView.tsx`, styled to match the deleted `Legend.tsx`'s old visual convention (small
rounded swatch + `text-[11px] text-text-secondary` label row), placed between `RangeControl` and
the chart.

**Issue 3 (tooltip dismissed / dataZoom reset every ~1s) — fixed, root cause eliminated rather than
routed around.** `nowIso` moved from `useState` to a plain `useRef` — the per-second tick no longer
triggers a React re-render or a new `option` object reference at all. The `option` passed to
`<ReactEChartsCore ... notMerge>` is now a `useMemo` recomputed only on genuinely structural changes
(`runs`/`entriesByRun`/`glossary`), which is exactly when a full `notMerge` reinit is correct and
desired. The per-second tick instead calls `echartsInstance.setOption(...)` directly (via a ref
captured from `onChartReady`) with `notMerge` omitted (defaults to merge mode) — ECharts still
replaces `series[0].data` wholesale on a merge-mode call (it doesn't deep-merge arrays), so the live
segment's end value keeps advancing every second exactly as before; only the destructive
full-instance reinit is removed.

**Why this is verified against a real ECharts instance and not literally in a browser:** the
existing `ProgressTimelineView.test.tsx` mocks `echarts-for-react/lib/core` entirely (a jsdom/vitest
constraint carried over from the original ticket — no `canvas` npm package is installed), so it
cannot exercise real `setOption`/merge semantics at all. A new file,
`dashboard-frontend/src/test/liveTickMerge.test.ts`, drives a genuine (non-mocked) `echarts/core`
instance directly, using `SVGRenderer` (works under jsdom without a native canvas dependency) —
three tests prove, at the actual `getOption()`/DOM level: (a) a merge-mode tick call still advances
the live segment's end value; (b) a merge-mode tick call preserves an in-progress `dataZoom` window,
while a control case using the *old* `notMerge`-every-tick behavior demonstrably resets it back to
0-100%, confirming this really was the bug; (c) an active tooltip's floating DOM node (identified by
its distinctive `z-index: 9999999` style, not by fragile text-content matching — the y-axis category
labels also render `run_id` as SVG `<text>`, which would false-positive-match a naive substring
search) survives a merge-mode tick but is destroyed outright by a `notMerge` tick. This is
substantially stronger evidence than reasoning from ECharts documentation alone, but it is still not
a literal pixel-rendered browser session — **the user's own visual confirmation in their browser is
the one remaining unchecked item (AC #7)**, and is genuinely achievable now since they have working
browser access to the dashboard.

**Issue 4 (related re-render-stability investigation) — resolved as a side effect of the Issue 3
fix, no separate change needed.** Since `nowIso` is no longer React state, `ProgressTimelineView`
no longer re-renders at all on the per-second tick — meaning `RangeControl` (a child component)
never re-renders on a tick either, so there is no possibility of it losing focus/cursor position in
its custom datetime inputs mid-typing due to a tick. This was confirmed by reading the diff (no
`setState` call remains in the tick's `setInterval` callback) rather than by adding a new test for a
now-structurally-impossible scenario.

**Do NOT touch compliance:** `RangeControl.tsx` was read but not modified (confirmed via empty
`git diff`); `phasePalette.ts`'s governed `PHASE_PALETTE`/`PHASE_FAMILY` exports are read-only,
consumed by `CHART_LEGEND_ENTRIES`'s derivation, never modified; `toChartOption`'s segment-count/
trailing-segment logic (Resolved Decision 10 from the prior ticket) is untouched.

## Test Summary

Scoped vitest run (5 files): `ProgressTimelineView.test.tsx`, `toChartOption.test.ts`,
`liveTickMerge.test.ts` (new), `RangeControl.test.tsx`, `App.test.tsx` — **45/45 passed**.
`npx tsc -b --noEmit` — clean, no errors. `npm run build` — succeeds, no new bundle warnings beyond
the pre-existing single-chunk-size advisory (unrelated to this fix).

New test coverage: 3 tests in `toChartOption.test.ts` (grid.containLabel, axisLabel truncation
config, `run_id` data untouched), 4 tests in `toChartOption.test.ts` for `CHART_LEGEND_ENTRIES`
(entry count, live color match, per-family color match derived from `PHASE_PALETTE`, human-readable
labels), 1 test in `ProgressTimelineView.test.tsx` (legend renders with exactly 9 entries), 3 tests
in the new `liveTickMerge.test.ts` (live segment advancement, dataZoom preservation + notMerge
control case, tooltip DOM survival + notMerge control case).

## Files Changed
- `dashboard-frontend/src/lib/toChartOption.ts` — `grid.containLabel`, `yAxis.axisLabel` truncation
  config, new `CHART_LEGEND_ENTRIES` export + `buildPhaseFamilyLegendEntries()`/
  `humanizePhaseFamilyLabel()` helpers.
- `dashboard-frontend/src/views/ProgressTimelineView.tsx` — `nowIso` moved from `useState` to
  `useRef`; new `echartsInstanceRef` captured via `onChartReady`; tick now drives a scoped
  merge-mode `setOption` call instead of a full component re-render; `option` now a `useMemo`
  scoped to structural dependencies only; new `ChartLegend` component rendered above the chart;
  registered `LegacyGridContainLabel` from `echarts/features`.
- `dashboard-frontend/src/test/toChartOption.test.ts` — 7 new tests (label truncation ×3, legend
  entries ×4).
- `dashboard-frontend/src/test/ProgressTimelineView.test.tsx` — 1 new test (legend rendering).
- `dashboard-frontend/src/test/liveTickMerge.test.ts` (new) — 3 tests against a real ECharts
  instance.

## Completion Summary
All 4 identified regressions in `ProgressTimelineView.tsx` (y-axis label overflow, missing legend,
tooltip/dataZoom reset every ~1s, and the related re-render-stability question) are fixed and
independently re-verified at the code/test level, including against a real (non-mocked) ECharts
instance for the tick-behavior fix — not merely reasoned about from documentation. On 2026-08-02
the production build was rebuilt fresh (`npm run build`) and served locally
(`src/api/agent_ops_dashboard/serve.py`, port 8420) for final verification. The one remaining open
item, AC #7 (literal visual/interactive confirmation in a real browser), is now closed: the user
manually checked all four items against the running dashboard and confirmed they render/behave
correctly. Ticket is fully done.
