---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-GANTT-TIME-AXIS
artifact_type: plan
tags: [observability, agent-monitoring]
---

# Implementation Plan — TCK-20260717-GANTT-TIME-AXIS

## RESTART NOTICE

This plan overwrites the stale interrupted-session `plan.md`. That prior plan's Steps 1-3 (export `toPercent`, build `TimeAxis`, wire `TimeAxis` into `RecentActivityGantt.tsx`) are **already fully implemented and tested** in the current working tree — `TimeAxis.test.tsx` is 3/3 passing, and the two axis-related tests appended to `RecentActivityGantt.test.tsx` pass. This plan covers only the remaining work: the on-chart run-id label in `GanttBar.tsx` (previously "Step 4"), plus final regression closure. The prior plan's truncation design ("12 chars + ellipsis") is explicitly **rejected** — the already-written test in `RecentActivityGantt.test.tsx` asserts `label.textContent).toBe('run-completed')`, the full untruncated 13-character fixture `run_id`. This plan's Step 1 renders the raw `run.run_id` with no truncation.

## Summary

Two steps remain to close this ticket. Step 1 adds a `<span data-testid="gantt-bar-run-label">{run.run_id}</span>` to both of `GanttBar.tsx`'s render branches (inferred-active and authoritative), rendering the untruncated `run_id` as a plain DOM text node, additive to the existing hover tooltip and kept out of the outer `<div>`'s `classNames` array so the authoritative/inferred zero-shared-class-token guarantee stays intact. Step 2 is a full regression and anti-drift closure pass — `npx vitest run` (full suite), `npx tsc -b --noEmit`, `npm run build`, plus the scoped Python architecture-guard test — confirming all 45 frontend tests pass (including the 3 currently-failing ones) and every anti-drift guard named in `test_plan.md` holds. No new test authorship is required; the tests already exist in the working tree and define the exact contract.

## Steps

### Step 1 — Add on-chart run-id label to both GanttBar render branches

**Files:** `dashboard-frontend/src/components/GanttBar.tsx`

**Change:**
- In the inferred-active branch (currently lines 63-73, the `<div className="gantt-bar--inferred gantt-bar--inferred-pattern" ...>` block that already contains `<span className="gantt-bar__estimate-label">~est.</span>`), add a second child span alongside the existing estimate-label span:
  ```tsx
  <span data-testid="gantt-bar-run-label">{run.run_id}</span>
  ```
- In the authoritative branch (currently lines 92-100, a self-closing `<div className={classNames.join(' ')} ... />`), the div must become non-self-closing so it can carry a child, and gain the same label span:
  ```tsx
  <div
    className={classNames.join(' ')}
    data-run-id={run.run_id}
    data-start={startTs}
    data-end={endTs}
    style={{ ...BAR_POSITION_STYLE, left: `${left}%`, width: `${width}%` }}
  >
    <span data-testid="gantt-bar-run-label">{run.run_id}</span>
  </div>
  ```
- Render `run.run_id` verbatim — do **not** truncate, slice, or ellipsize it. No `truncateRunId`-style helper is needed at all; this is a direct prop-to-text-node render.
- If any styling class is added to the new `<span>` (not required to satisfy tests, but permissible for legibility, e.g. a text-overflow/ellipsis CSS class), it must be applied to the `<span>` only — never appended to either branch's outer `<div>`'s `className`/`classNames` array.
- Do not touch `BAR_POSITION_STYLE`, `STATUS_BUCKET_CLASS`, `STATUS_BUCKET_COLOR_CLASS`, `classifyFinalStatus`, or the exported `toPercent` function — all unrelated to this change.

**Do NOT touch:**
- `dashboard-frontend/src/components/TimeAxis.tsx`, `dashboard-frontend/src/test/TimeAxis.test.tsx` — complete and passing, no rework.
- The `export` keyword on `toPercent` (already exported) — do not re-touch this line.
- `dashboard-frontend/src/views/RecentActivityGantt.tsx` — the `TimeAxis` import/wiring (imports block and the `<Legend />` / `<TimeAxis .../>` / row-list render order) is already correct; the tooltip `Tooltip.Content` block (~L91-93) must not be modified, renamed, or restructured.
- `dashboard-frontend/src/components/Legend.tsx` — out of scope, untouched by this ticket throughout.
- Do not introduce any `Date.now()` or `new Date()` call anywhere in `GanttBar.tsx` — `GanttBar.test.tsx`'s raw-source regex guard scans the whole file; the label needs no date/time logic since it only renders `run.run_id`.
- Do not add the new `<span>`'s class name (if any) to either branch's outer `<div>`'s `className`/`classNames` array — this would break the "never shares styling between an inferred-active bar and an authoritative-completed bar" test in `RecentActivityGantt.test.tsx`.

**Verify:**
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` — "each rendered bar carries an on-chart run-id label distinct from the tooltip" (asserts `label.textContent === 'run-completed'` and that the label is not the tooltip string).
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` — "narrow/clamped bar label is not dropped when the bar hits its minimum width" (asserts the label exists and is non-empty even at `width: 0.5%`).
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` — "existing hover-tooltip content is unchanged after the on-chart label addition" (asserts the tooltip's original string is intact and the tooltip node is distinct from the `gantt-bar-run-label` node).
- Run scoped: `cd dashboard-frontend && npx vitest run src/test/RecentActivityGantt.test.tsx src/test/GanttBar.test.tsx src/test/TimeAxis.test.tsx`

### Step 2 — Full regression and anti-drift closure pass

**Files:** none changed in this step — verification only.

**Change:** Run the full verification surface to confirm Step 1's change is complete and nothing regressed:
1. `cd dashboard-frontend && npx vitest run` — full 7-file suite must report all tests passing (45 tests total, up from 42 passed / 3 failed before Step 1).
2. `cd dashboard-frontend && npx tsc -b --noEmit` — typecheck must compile cleanly.
3. `cd dashboard-frontend && npm run build` — production build sanity, confirms no build-time regression.
4. `python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -m "not slow"` — scoped Python architecture guard, confirms no accidental import of `src/api/server.py`, `read_model_cache.py`, `routes/history.py`, or `ws/stream.py`.
5. Manually re-check each anti-drift guard named in `test_plan.md`'s "Anti-Drift Test Guards" section against the actual diff (not just described): `GanttBar.test.tsx`'s raw-source `Date`/`new Date()` scan, the zero-shared-class-token guarantee, `TimeAxis.test.tsx`'s `toPercent`-import guard (unaffected, but re-confirm it still passes), the tooltip-unchanged guard, the Python architecture-surface guard, and the two manual guards below.
6. Manual grep-based scope guard: `git diff --stat -- dashboard-frontend/src/components/GanttBar.tsx dashboard-frontend/src/views/RecentActivityGantt.tsx dashboard-frontend/src/components/TimeAxis.tsx` — confirm no change to `SINCE_WINDOW_MS`'s value or a second definition of it, and no new time-window-picker UI/state (both explicitly Out of Scope).
7. Manual commit-hygiene guard: confirm this ticket's eventual commit does not bundle `dashboard-frontend/src/index.css`, `dashboard-frontend/tsconfig.app.json`, `dashboard-frontend/tsconfig.json`, `dashboard-frontend/tsconfig.test.json`, or the `TicketsView.test.tsx` CSS-layer regression block — those belong to the separate, already-DONE `TCK-20260717-CSS-LAYER-PADDING-FIX` ticket sitting uncommitted in the same working tree, and must be committed (if at all, in this session) under their own ticket ID, never folded into this ticket's `Files Changed` or commit message.

**Do NOT touch:** any source file — this step is verification-only. If any test unexpectedly fails, the fix belongs back in Step 1's scope (the label rendering), not a new step; do not expand scope to fix unrelated pre-existing failures.

**Verify:** All commands in the "Change" list above exit 0 / report full pass. The 3 previously-failing tests (`gantt-bar-run-label` existence, narrow-bar label non-empty, tooltip-unchanged) must now be part of the passing 45.

## Scope Guards

- Do not touch `dashboard-frontend/src/components/TimeAxis.tsx` or `dashboard-frontend/src/test/TimeAxis.test.tsx` — complete, correct, fully tested (3/3 passing). No redesign, no "cleanup."
- Do not touch the `export function toPercent(...)` declaration or its clamping/percentage math in `GanttBar.tsx` — already correct; reuse only, never reimplement a parallel copy.
- Do not touch `dashboard-frontend/src/views/RecentActivityGantt.tsx`'s `TimeAxis` import or its render-order wiring (`<Legend />` → `<TimeAxis .../>` → row-list) — already correct and tested.
- Do not touch the `Tooltip.Content` block in `RecentActivityGantt.tsx` (~L91-93) — must remain byte-for-byte unchanged; AC #4 and its regression test depend on this.
- Do not touch `dashboard-frontend/src/components/Legend.tsx` — out of scope for this entire ticket.
- Do not implement any run-id truncation/ellipsis scheme — the existing test pins the untruncated `run_id` as the contract. If narrow-bar crowding is a visual concern, address it with CSS (`overflow`/`text-overflow` on the label span) only, never by slicing the string, since the "narrow/clamped bar label is not dropped" test only requires the label to exist with truthy content, and the "on-chart run-id label" test requires the exact untruncated string.
- Do not add a time-window picker (Last 24h/7d/Custom) or change `SINCE_WINDOW_MS` — explicitly Out of Scope per the ticket.
- Do not modify `src/api/server.py`, `read_model_cache.py`, `routes/history.py`, or `ws/stream.py` — this ticket is frontend-only; the Python architecture guard exists specifically to catch any accidental crossing of that boundary.
- Do not bundle `dashboard-frontend/src/index.css`, `tsconfig.app.json`, `tsconfig.json`, `tsconfig.test.json`, or the `TicketsView.test.tsx` CSS-layer regression block into this ticket's diff or commit — those belong to the separate `TCK-20260717-CSS-LAYER-PADDING-FIX` ticket, already DONE, merely uncommitted in the same working tree.
- Do not add `Date.now()` or `new Date()` calls to `GanttBar.tsx` — the raw-source anti-drift guard in `GanttBar.test.tsx` scans the whole file; the label needs no date logic.

## Dependency Map

- Step 2 depends on Step 1 (verification pass runs against Step 1's completed change).
- Step 1 has no internal dependencies — it is a single, self-contained two-branch edit to one file.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — visible time axis spanning since/now window, independent of hovering | Already implemented pre-restart (prior plan Steps 1-3, not part of this plan's remaining work); Step 2 re-confirms no regression | `RecentActivityGantt.test.tsx`: "renders a visible time axis independent of any hover state", "time axis end label updates as nowIso advances" |
| AC #2 — each bar carries an on-chart text identifier distinct from the tooltip | Step 1 | `RecentActivityGantt.test.tsx`: "each rendered bar carries an on-chart run-id label distinct from the tooltip", "narrow/clamped bar label is not dropped when the bar hits its minimum width" |
| AC #3 — axis tick positions computed via the same `toPercent(...)` mapping GanttBar uses | Already implemented pre-restart (prior plan Steps 1-2, not part of this plan's remaining work); Step 2 re-confirms no regression | `TimeAxis.test.tsx`: "imports toPercent from GanttBar rather than redeclaring it", "positions a known tick at exactly the value toPercent returns for that timestamp" |
| AC #4 — existing tooltip content and authoritative/inferred disjoint-styling behavior remain unchanged | Step 1 (label kept out of tooltip block and out of outer-div classNames); Step 2 (full regression confirms) | `RecentActivityGantt.test.tsx`: "existing hover-tooltip content is unchanged after the on-chart label addition", "never shares styling between an inferred-active bar and an authoritative-completed bar" (pre-existing, must stay passing) |

## Anti-Drift Notes

- **Truncation correction (the key divergence from the stale interrupted plan)**: the prior plan.md specified a 12-char+ellipsis truncation default for the run-id label. The already-written test in `RecentActivityGantt.test.tsx` asserts `label.textContent).toBe('run-completed')` — the full untruncated 13-character fixture ID. A 12-char+ellipsis scheme would render `'run-complete…'` and fail this test. This plan's Step 1 renders `run.run_id` verbatim with zero truncation logic. Do not reintroduce truncation.
- **Weak narrow-bar assertion**: the "narrow/clamped bar label is not dropped" test only checks `textContent` is truthy (non-empty) at `width: 0.5%` — it does not require any specific crowding-mitigation CSS. No additional design work beyond "the label element exists with the run_id as content" is required to satisfy it.
- **Outer-div classNames isolation**: the zero-shared-class-token guarantee test only inspects the outer `[data-run-id]` element's own `className`. A child `<span>` can safely carry its own class (e.g. for text truncation/ellipsis CSS) without risk — the risk is exclusively if that class were pushed into the outer div's `classNames` array/join.
- **Self-closing-to-container conversion**: the authoritative branch's `<div ... />` must become `<div ...>...</div>` to hold the new child span. This is a syntactic change only — no attribute on that div (`className`, `data-run-id`, `data-start`, `data-end`, `style`) should be altered in the process.
- **Commit-ordering housekeeping (not a plan blocker)**: the investigation found a second, unrelated ticket's (`TCK-20260717-CSS-LAYER-PADDING-FIX`) finished-but-uncommitted changes sitting in the same working tree (5 files: `index.css`, `TicketsView.test.tsx`, `tsconfig.app.json`, `tsconfig.json`, `tsconfig.test.json`). This does not affect what code to write in Step 1 or Step 2, but whoever runs `git commit`/Finalize for this ticket must not fold those 5 files into this ticket's commit — they need their own catch-up commit referencing `TCK-20260717-CSS-LAYER-PADDING-FIX`. This is a process note for Finalize, not an implementation step.
- **Doc follow-up (non-blocking)**: `docs/observability/agent_ops_dashboard_contract.md` and `docs/guides/agent_ops_dashboard.md` currently under-describe `RecentActivityGantt`'s composition (no axis/label mention). Not part of this plan's steps since it's a documentation update, not code — flag for whoever closes the ticket to update per the "Update related docs" Definition-of-Done item, or explicitly note deferral in the ticket's Completion Summary.
- **No new test file needed**: all tests this plan must satisfy already exist in the working tree (`RecentActivityGantt.test.tsx`). Step 1 is implementation-only; Step 2 is verification-only. Do not author a new test file.

## Deviations

None. Step 1 was implemented exactly as specified: `<span data-testid="gantt-bar-run-label">{run.run_id}</span>` added to both `GanttBar.tsx` render branches, untruncated, kept off the outer `<div>`'s `classNames`. The authoritative branch's `<div ... />` was converted from self-closing to a container with no other attribute changes, as specified. Step 2's full verification surface (`npx vitest run` → 45/45, `npx tsc -b --noEmit` → clean, `npm run build` → clean, the scoped Python architecture guard → 1/1 passing, and all manual anti-drift/scope-guard checks) all passed with no deviation from the plan's expected outcomes.
