---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-GANTT-TIME-AXIS
artifact_type: test_plan
tags: [observability, agent-monitoring]
---

# Test Plan — TCK-20260717-GANTT-TIME-AXIS

## RESTART NOTICE

Overwrites the interrupted attempt's `test_plan.md`. All "New Tests Required" below **already exist in the working tree** — they were written during the interrupted session and are part of what needs to be made to pass, not net-new test authorship. Confirmed by direct `npx vitest run` inside `dashboard-frontend/` during this investigation: **3 failed / 42 passed, 7 files, 45 tests total.** All 3 failures are in `RecentActivityGantt.test.tsx` and share one root cause: `GanttBar.tsx` does not yet render the `data-testid="gantt-bar-run-label"` element the tests query for.

## Regression Surface

Existing tests that must keep passing (all currently passing; must remain so after the remaining implementation work lands):

**dashboard-frontend/ (unit/integration, Vitest):**
- `dashboard-frontend/src/test/GanttBar.test.tsx` — 4 tests, raw-source anti-drift guards (no `Date.now()`/`new Date()`, direct `is_inferred_active` branching) plus authoritative/inferred branch-selection tests. Currently passing; zero diff from HEAD.
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`'s original 6 tests (byte-identical to HEAD): completed-run rendering, inferred-run rendering, zero-shared-class-token disjointness, settle-transition update, click→`onSelectRun`. All currently passing.
- `dashboard-frontend/src/test/TimeAxis.test.tsx` — 3 tests (new this ticket, already fully implemented and passing): `toPercent` reuse anti-drift guard, numeric tick-position match, immediate render with no interaction.
- `dashboard-frontend/src/test/TicketsView.test.tsx` — includes a CSS-layer/padding regression block added by the sibling `TCK-20260717-CSS-LAYER-PADDING-FIX` ticket (already in the working tree, uncommitted, unrelated to this ticket's own changes but present in the same suite run). Must remain passing; do not modify.
- `dashboard-frontend/src/test/App.test.tsx`, `dashboard-frontend/src/test/useRunsPolling.test.ts` — untouched by this ticket; part of the full-suite regression baseline.

**Python (architecture guard, must stay green, scoped run only):**
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — guards that `dashboard-frontend/` never references the simulation engine's own API surface (`src/api/server.py`, `read_model_cache.py`, `routes/history.py`, `ws/stream.py`). Not touched by this ticket's frontend-only diff, but must be re-run as part of the full scoped verification since it is the one Python test with `agent_ops_dashboard` + `frontend` in scope together.

**arena-combat:** none — this ticket has zero overlap with combat/simulation code; no arena-combat regression surface applies.

## New Tests Required

All of the following are per-AC and **already exist in the working tree** in `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` and `dashboard-frontend/src/test/TimeAxis.test.tsx`, written during the interrupted attempt. Listed here as the authoritative "must pass" set for the remaining implementation work, not as new authorship:

- **Test**: "renders a visible time axis independent of any hover state"
  **Category**: integration
  **Verifies**: AC #1 — `screen.getByTestId('gantt-time-axis')` exists with zero hover/pointer interaction dispatched.
  **Location**: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
  **Status**: passing.

- **Test**: "time axis end label updates as nowIso advances"
  **Category**: integration
  **Verifies**: AC #1 (axis reflects the live since/now window, not a frozen snapshot) — uses `vi.useFakeTimers()`, advances 60s, asserts the last tick's label text changed.
  **Location**: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
  **Status**: passing.

- **Test**: "imports toPercent from GanttBar rather than redeclaring it"
  **Category**: architecture guard (anti-drift, raw-source scan)
  **Verifies**: AC #3 — `TimeAxis.tsx`'s source text imports `toPercent` from `@/components/GanttBar` and contains no local `function toPercent` redeclaration.
  **Location**: `dashboard-frontend/src/test/TimeAxis.test.tsx`
  **Status**: passing.

- **Test**: "positions a known tick at exactly the value toPercent returns for that timestamp"
  **Category**: unit
  **Verifies**: AC #3 — a directly-computed `toPercent(...)` call in the test matches the rendered tick's `style.left`, proving axis and bar math cannot silently diverge.
  **Location**: `dashboard-frontend/src/test/TimeAxis.test.tsx`
  **Status**: passing.

- **Test**: "renders the axis root immediately with no hover/interaction required"
  **Category**: integration
  **Verifies**: AC #1.
  **Location**: `dashboard-frontend/src/test/TimeAxis.test.tsx`
  **Status**: passing.

- **Test**: "each rendered bar carries an on-chart run-id label distinct from the tooltip"
  **Category**: integration
  **Verifies**: AC #2 — `screen.getByTestId('gantt-bar-run-label')` exists pre-hover with the fixture's `run_id` as its text content, and that text is not the full tooltip string.
  **Location**: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
  **Status**: **failing today** — `GanttBar.tsx` does not render this element yet. This is the primary remaining implementation gap.

- **Test**: "narrow/clamped bar label is not dropped when the bar hits its minimum width"
  **Category**: integration
  **Verifies**: AC #2 + the ticket's "narrow-bar label crowding" scope bullet — a run with `start_ts === end_ts` (triggering the pre-existing `0.5%` width clamp) still renders a non-empty `gantt-bar-run-label`.
  **Location**: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
  **Status**: **failing today** — same root cause.

- **Test**: "existing hover-tooltip content is unchanged after the on-chart label addition"
  **Category**: architecture guard / regression
  **Verifies**: AC #4 — hover/focus still produces the exact original tooltip string, and the tooltip DOM node is distinct from the `gantt-bar-run-label` node.
  **Location**: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
  **Status**: **failing today** — `screen.getByTestId('gantt-bar-run-label')` throws (element doesn't exist), not a tooltip-content regression per se, but the test cannot pass until the label exists.

**No new test file needs to be created.** The remaining work is exclusively implementation (`GanttBar.tsx`'s two render branches) to make the 3 failing tests pass, plus re-confirming the other 42 stay green.

**One test-vs-plan inconsistency to resolve during implementation** (see investigation.md Risk #4): the "each rendered bar carries an on-chart run-id label" test asserts `label.textContent).toBe('run-completed')` — the *untruncated* 13-character fixture `run_id`. If the implementation follows the interrupted attempt's stale plan.md design ("12 chars + ellipsis" truncation default), this test will fail (`'run-complete…'` ≠ `'run-completed'`). The implementation must satisfy the test as it exists now, not the superseded plan prose — either raise the truncation threshold or otherwise ensure 13-char IDs pass through unmodified.

## Scoped Pytest Commands

This ticket is TypeScript/Vitest-only in its own diff; the one Python command below is the architecture-guard regression check, not new test authorship:

```bash
# Vitest — primary verification surface for this ticket
cd dashboard-frontend && npx vitest run

# Scoped subset (fast iteration while fixing the remaining GanttBar label gap)
cd dashboard-frontend && npx vitest run src/test/RecentActivityGantt.test.tsx src/test/GanttBar.test.tsx src/test/TimeAxis.test.tsx

# Typecheck (must still compile cleanly given the tsconfig.test.json split
# already present in the working tree from the sibling CSS-fix ticket)
cd dashboard-frontend && npx tsc -b --noEmit

# Production build sanity (confirms no build-time regression from the new files)
cd dashboard-frontend && npm run build

# Python architecture guard — scoped to agent_ops_dashboard + frontend surface only.
# Never run the full tests/ suite for this ticket.
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -m "not slow"
```

Never: `pytest tests/`. Also never rely only on the scoped-subset Vitest command before Finalize — run the full `npx vitest run` at least once, since that is what surfaced the sibling CSS-fix ticket's uncommitted changes sharing this suite; a narrower run could miss cross-file regressions in `TicketsView.test.tsx`, `App.test.tsx`, etc.

## Anti-Drift Test Guards

- **`GanttBar.test.tsx`'s raw-source scan (no `Date.now()`/`new Date()` anywhere in `GanttBar.tsx`)** — must still pass after the label-rendering code lands; any `truncateRunId`-style helper must operate purely on the `run.run_id` string prop, never touch `Date`.
- **`RecentActivityGantt.test.tsx`'s "never shares styling between an inferred-active bar and an authoritative-completed bar"** (set-intersection over `el.className`, outer `[data-run-id]` element only) — must still pass after the label span is added; the label's class name must never be pushed into either branch's outer `classNames` array.
- **`TimeAxis.test.tsx`'s "imports toPercent from GanttBar rather than redeclaring it"** — guards against a future silent fork of the axis's percentage math from the bar's; if any future change touches `TimeAxis.tsx`, this guard must still pass unmodified.
- **`RecentActivityGantt.test.tsx`'s "existing hover-tooltip content is unchanged after the on-chart label addition"** — the single most direct guard against the on-chart label accidentally replacing or altering tooltip content instead of being additive to it (this ticket's Scope explicitly forbids replacement).
- **`tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`** — guards that no file touched by this ticket (or the unrelated CSS-LAYER-PADDING-FIX changes sitting in the same tree) accidentally imports `src/api/server.py`, `read_model_cache.py`, `routes/history.py`, or `ws/stream.py`. Pure frontend-only changes should trivially keep this guard green, but it is cheap to re-run and catches an entire class of stale-reference drift.
- **Grep-based scope guard (manual, not an automated test, but should be run before Finalize)**: `git diff --stat -- dashboard-frontend/src/components/GanttBar.tsx dashboard-frontend/src/views/RecentActivityGantt.tsx dashboard-frontend/src/components/TimeAxis.tsx` should show no change to `SINCE_WINDOW_MS`'s value or a second definition of it, and no new time-window-picker UI/state — both explicitly Out of Scope.
- **Commit-hygiene guard (manual, not an automated test)**: before committing, verify this ticket's commit does **not** bundle `dashboard-frontend/src/index.css`, `dashboard-frontend/tsconfig.app.json`, `dashboard-frontend/tsconfig.json`, or `dashboard-frontend/tsconfig.test.json` unless the planner has explicitly decided to fold the already-DONE `TCK-20260717-CSS-LAYER-PADDING-FIX` catch-up commit into the same session (see investigation.md Risk #1). If those files are committed, the commit message must reference `TCK-20260717-CSS-LAYER-PADDING-FIX`, not this ticket, to preserve per-ticket traceability. `dashboard-frontend/src/test/TicketsView.test.tsx`'s new describe block is the CSS-fix ticket's own regression test and belongs to that same commit, not this one.
- **Follow-through guard, informed by prior-ticket history**: `stored_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/` shows the *previous* Gantt ticket shipped without some of its own test_plan.md's Anti-Drift Test Guards actually implemented, triggering a `DOD_BLOCKED` remediation pass at Verify. Before this ticket is marked complete, explicitly re-check that every test named in this document actually exists in the diff and passes, not just described.
