---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-REPLAY-TIMELINE
phase: done
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-REPLAY-TIMELINE

## Title
Run Detail / Replay timeline view: scrubbable playback of a run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a detail view for a single completed (or live) run: scrubbable phase-by-phase plus tool-call playback, plus a static files-touched panel. This is the frontend half of the concern; the underlying timeline join and files-touched derivation are shared infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a Replay timeline frontend view: scrubbable phase-by-phase and tool-call playback for a single run, driven by GET /api/runs/{run_id}/timeline
- Build a static files-touched panel from the timeline payload's deduplicated files_touched list
- Implement a scrub/playback control that replays only the already-fetched RunTimeline payload client-side, without triggering new fetches
- Render honest '(phase unknown — run still in progress)' captions for live_tail entries where phase/agent are null

## Out of Scope
- Implementing GET /api/runs/{run_id}/timeline, its seq-ordered join logic, or files_touched derivation from tool_calls[].input_summary (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- Fixing the live phase/agent null-labeling gap (independent sibling ticket, not this scope)
- The Recent Activity Gantt view (AGENTOPS-ACTIVITY-GANTT) and Tickets table view (AGENTOPS-TICKETS-VIEW)
- Concurrency/RLock implementation in the backend cache (owned by AGENTOPS-DASHBOARD-BACKEND)

## Acceptance Criteria
- [x] Timeline view renders entries in the order returned by GET /api/runs/{run_id}/timeline (seq ascending), each showing its joined tools.jsonl rows
- [x] Files-touched panel shows a deduplicated-by-path list restricted to Read/Edit/Write/MultiEdit tool calls, retaining first-seen ts+tool per file
- [x] When is_live=true, every live_tail item displays phase=null and agent=null explicitly with an '(phase unknown — run still in progress)' caption, never a guessed value
- [x] Scrubbing the playback control replays the already-fetched timeline payload client-side and triggers no new network fetch

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- src/api/server.py
- src/api/routes/history.py
- src/observability/reporting/history_query.py
- src/api/read_model_cache.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- docs/agent-monitoring/schema.md
- .claude/workflows/implement-ticket.js
- expected: frontend/src/views/ReplayTimelineView.tsx

## Assumptions / Open Questions
- Frontend currently has zero CI coverage; this view inherits that gap rather than fixing it
- The live phase/agent labeling sibling fix is independent, and this view must render honestly without depending on or blocking it

## Implementation Notes

Followed `staging_artifacts/TCK-20260716-AGENTOPS-REPLAY-TIMELINE/plan.md`'s 12 steps in order.

- **Step 1** (`dashboard-frontend/src/api.ts`): added `fetchRunTimeline(runId)` — a one-shot
  `fetch('/api/runs/{runId}/timeline')` mirroring `fetchRuns`'s error-message convention, returning
  the already-declared `RunTimeline` type. No polling hook added.
- **Step 2** (`dashboard-frontend/src/components/PlaybackScrubber.tsx`, new): controlled
  `{ maxIndex, index, onIndexChange }` component built on `@radix-ui/react-slider`, with internal
  `playing`/`speed` (1/5/20x) state and a `setInterval`-driven auto-advance effect. Imports nothing
  from `api.ts` — no knowledge of `RunTimeline`/`TimelineEntry`/`RawToolCall`, so "scrub never
  fetches" is structural.
- **Steps 3-7** (`dashboard-frontend/src/views/ReplayTimelineView.tsx`, new): fetch-once-per-`runId`
  effect (async/await + `cancelled` flag, matching `useRunsPolling`'s shape minus the
  `setInterval`); phase-timeline segments mapped directly from `entries` array order (no `.sort(`)
  with a local `ENTRY_STATUS_CLASS` map scoped to the real `TimelineEntry.status` value set
  (`ok`/`failed`/`blocked`/`skipped`, per `docs/agent-monitoring/schema.md`), kept separate from
  `GanttBar.tsx`'s `classifyFinalStatus`; detail area gated by `scrubIndex` via
  `entries.slice(0, scrubIndex + 1)`; files-touched panel renders `timeline.files_touched`
  unconditionally (not scrub-gated), grouped only by `.tool` via a single `Map`; live_tail section
  renders a fixed `PHASE_UNKNOWN_CAPTION` constant per item, unconditionally, only when
  `is_live && live_tail.length > 0`.
- **Step 8** (`dashboard-frontend/src/test/ReplayTimelineView.test.tsx`, new): rendering tests for
  AC #1/#2/#3/#4 plus three `?raw` source-text anti-drift guards (no second dedup/filter, no
  `.phase`/`.agent`/`tool ===` inference on live_tail, no `.sort(`), landed in the same pass as the
  feature code.
- **Steps 9-10** (`App.tsx`, `RecentActivityGantt.tsx`): added `selectedRunId` state and
  `onSelectRun` callback to `App.tsx`, replacing the Replay placeholder with a real
  `<ReplayTimelineView runId={selectedRunId} />` (or a "select a run" placeholder when null);
  `RecentActivityGantt` now takes a required `onSelectRun` prop and each row's `onClick` calls
  `onSelectRun(run.run_id)`, replacing the stub `console.debug`.
- **Step 11** (`App.test.tsx`): removed the stale "Replay timeline coming soon." assertions, added
  an App-shell smoke test and a Gantt-row-click-navigates-to-Replay integration test (mocking
  `fetchRunTimeline`), kept the Tickets-stub guard.
- **Step 12**: confirmed empty `git diff --stat -- src/api/agent_ops_dashboard/`; ran both the
  scoped backend pytest command (31 passed) and `npm test` (24 passed) green.

Deviations from plan.md (recorded there too):
1. Added a `ResizeObserver` stub to `dashboard-frontend/src/test/setup.ts` — jsdom has no
   `ResizeObserver`, which `@radix-ui/react-slider`'s internal `useSize` hook requires; every test
   that renders `PlaybackScrubber` (i.e. every `ReplayTimelineView` test) crashed without it. Not
   called out in plan.md since the plan predates hitting this jsdom gap.
2. `PlaybackScrubber` only renders the actual `Slider.Root` when `maxIndex > 0`; for a 0-or-1-entry
   timeline (`maxIndex === 0`) it renders an inert placeholder track instead. Radix's slider divides
   by `(max - min)`, and `min === max === 0` produced `calc(NaN% + 0px)`, which jsdom's style setter
   throws a `SyntaxError` on, unmounting the whole React tree. Discovered via the App.tsx navigation
   test (`run-nav-target` fixture has zero `entries`). Not in the original plan text.
3. Updated `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (not listed under plan.md
   Step 11, which named only `App.test.tsx`) — a necessary consequence of Step 10 making
   `onSelectRun` a required prop; all pre-existing `render(<RecentActivityGantt />)` call sites
   needed a mock prop to keep compiling. Also added one new test asserting the click handler passes
   the clicked row's own `run_id`. This was anticipated by test_plan.md's Regression Surface section
   even though plan.md's Step 11 didn't enumerate it.

## Test Summary

`cd dashboard-frontend && npm test` — 5 files, 24 tests, all passing (includes the 3 pre-existing
suites `GanttBar.test.tsx`, `useRunsPolling.test.ts`, and the updated `RecentActivityGantt.test.tsx`/
`App.test.tsx`, plus the new `ReplayTimelineView.test.tsx`).

`npx tsc -b --noEmit` — clean, no type errors.

`pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"` — 31 passed.

`git diff --stat -- src/api/agent_ops_dashboard/` — empty, confirming no backend files touched.

## Files Changed

- `dashboard-frontend/src/api.ts` (added `fetchRunTimeline`)
- `dashboard-frontend/src/components/PlaybackScrubber.tsx` (new)
- `dashboard-frontend/src/views/ReplayTimelineView.tsx` (new)
- `dashboard-frontend/src/App.tsx`
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`
- `dashboard-frontend/src/test/ReplayTimelineView.test.tsx` (new)
- `dashboard-frontend/src/test/App.test.tsx`
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
- `dashboard-frontend/src/test/setup.ts`

## Completion Summary

Built the Replay timeline frontend view end to end: a one-shot `fetchRunTimeline` fetch, a
data-agnostic `PlaybackScrubber` (Radix slider + play/pause + 1x/5x/20x speed), and
`ReplayTimelineView` rendering seq-ordered phase segments with per-entry tool-call detail gated by
scrub position, a static files-touched panel grouped by tool, and an honest unconditional
"(phase unknown — run still in progress)" caption for live_tail items. Wired Gantt-row click-through
navigation end to end (`RecentActivityGantt` → `App` → `ReplayTimelineView`). All four acceptance
criteria are covered by passing tests, including anti-drift `?raw` source guards against re-sorting,
re-deduping, or inferring phase/agent client-side. No backend files were touched; the scoped backend
regression suite and the full frontend suite are both green.
