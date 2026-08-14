---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-ACTIVITY-GANTT
phase: done
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Title
Recent Activity view: Gantt-style timeline of runs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a default-landing Gantt-style view: completed runs shown as solid authoritative bars from runs.jsonl, and runs with recent tools.jsonl activity but no runs.jsonl record yet shown as a visually distinct inferred-live estimate. This is the frontend half of the concern; the underlying is_inferred_active computation is shared infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a RecentActivityGantt frontend component as the dashboard's default-landing view
- Poll GET /api/runs?since=<ISO> and render completed runs as solid authoritative bars using start_ts/end_ts
- Render runs with is_inferred_active=true as visually distinct fill/pattern with an explicit estimate label, never sharing style with authoritative bars
- Implement a settle-transition UI so that when a run flips from active to completed between polls, its bar updates to authoritative style/values without a jarring reload

## Out of Scope
- Implementing /api/runs, the is_inferred_active heuristic, or ACTIVE_WINDOW_MINUTES logic (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- Fixing live_tail phase/agent always being null (MONITORING_INSTRUMENTATION_GAP — an independent sibling fix, not in scope here)
- The Replay timeline detail view (AGENTOPS-REPLAY-TIMELINE) and Tickets table view (AGENTOPS-TICKETS-VIEW)
- Retention/rotation policy for agent-monitoring/*.jsonl

## Acceptance Criteria
- [ ] GET /api/runs?since=<ISO> results render completed runs as solid bars using authoritative start_ts/end_ts, with is_inferred_active shown false
- [ ] A run present in tools.jsonl within the active window and absent from runs_by_id renders as an inferred-active bar with inferred_start_ts as its start point
- [ ] When a run transitions from active to completed across polls, the UI updates the bar from inferred style to authoritative style/values with no stale 'still active' state ever shown
- [ ] Inferred-active bars are always rendered with a visually distinct fill/pattern and an explicit estimate label, never sharing styling with authoritative completed bars

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/validate.py
- src/api/read_model_cache.py
- src/api/routes/history.py
- src/observability/reporting/history_query.py
- src/api/server.py
- src/api/ws/stream.py
- docs/agent-monitoring/schema.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md
- expected: frontend/src/views/RecentActivityGantt.tsx

## Assumptions / Open Questions
- ACTIVE_WINDOW_MINUTES=10 default (owned by the backend ticket) is not yet validated against real crashed-run timing data; this view's live/estimate rendering depends on that value being reasonable
- live_tail items will always render phase=null/agent=null until the independent MONITORING_INSTRUMENTATION_GAP fix lands; accepted as a known limitation for this view, not blocking

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/plan.md`'s 8 ordered steps.
No deviations from the plan's scope; two ambiguous plan directives were resolved as documented in
that file's new "Deviations" section (dependency set trimmed vs. mirrored 1:1; dev-proxy target made
env-overridable instead of a literal address).

- **Scaffold** (`dashboard-frontend/`): React 19.2 + Vite 7.2 + TypeScript 5.9 + Tailwind 4.1 (via
  `@tailwindcss/vite`) + Radix UI + Vitest 4, mirroring `frontend/`'s versions. Added an explicit
  `"test": "vitest run"` script (absent from `frontend/package.json` despite having `vitest`
  installed). Dev-server proxy target for `/api` is read from `VITE_DASHBOARD_API_TARGET` with a
  placeholder fallback (`http://127.0.0.1:8471`) rather than the confirmed prod port `8420`, per the
  plan's explicit "do not hardcode 8420" instruction (that's `AGENTOPS-BUILD-SERVE`'s decision to
  make).
- **`src/api.ts`**: typed `RunSummary`/`RunDetail`/`RunTimeline`/`HealthStatus`/`TimelineEntry`/etc.
  interfaces transcribed field-for-field from `src/api/agent_ops_dashboard/models.py` (read directly,
  no duck-typing). `fetchRuns()` is a thin typed fetch wrapper over `GET /api/runs`.
  `useRunsPolling(sinceIso, intervalMs=5000)` polls on an interval and, per poll, loops
  `fetchAllRunsSince()` on `offset += 100` while a page returns exactly 100 rows (the backend's
  `le=100` max), merges pages into a `Map` keyed by `run_id` (de-duplicating), and sorts by
  `start_ts ?? inferred_start_ts` descending. Never computes `is_inferred_active` itself — renders
  only what `RunSummary` already carries.
- **`components/GanttBar.tsx`**: two fully separate render branches (`is_inferred_active` ? inferred
  : authoritative) with **zero shared class tokens** — not even a common positioning/layout class.
  Shared absolute-positioning (top/height/border-radius) is applied via an inline `style` object,
  not a CSS class, specifically so the authoritative branch's classes (`gantt-bar--authoritative`,
  `gantt-bar--status-{done,failed,neutral}`, `bg-accent-*`) and the inferred branch's classes
  (`gantt-bar--inferred`, `gantt-bar--inferred-pattern`) can never overlap under a literal
  intersection test — satisfies AC #4's "never sharing styling" as a hard, structurally-enforced
  guarantee rather than a convention. `classifyFinalStatus()` buckets `final_status` per
  `UI_INTERACTION_SPEC.md` §2 (`DONE`→green, `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`→red, else
  neutral gray) and is exported so `Legend.tsx` reuses the identical bucket→class mapping. The
  inferred branch renders an explicit `<span className="gantt-bar__estimate-label">~est.</span>` DOM
  node present only on that variant. `justSettled` adds `gantt-bar--settling transition-all
  duration-300` (plain Tailwind utilities, no new animation dependency) to the authoritative branch
  only, for the one render cycle after a flip.
- **`components/Legend.tsx`**: stateless, renders once per mount (not per row), reuses
  `STATUS_BUCKET_CLASS`/bucket labels from `GanttBar.tsx` plus a fourth swatch for the
  inferred/estimate style — intentionally shares tokens with `GanttBar` (by design, so legend and
  bars can't visually diverge), which does not conflict with AC #4 (that guard is about
  authoritative vs. inferred bars never sharing styling with *each other*, not about the legend).
- **`views/RecentActivityGantt.tsx`**: composes `useRunsPolling` + `GanttBar` + `Legend`. Fixed
  "last 24h" `since` window computed once at mount (`useState` initializer, not recomputed on every
  `nowIso` tick, so the polling `since` argument stays stable and doesn't churn the hook's `useEffect`
  every second). A separate 1s-interval `nowIso` tick drives inferred bars' right-edge and
  duration-so-far. Settle-transition tracking keeps a `previousActiveByRunIdRef` (`run_id` →
  `is_inferred_active`) across poll results; any `run_id` that flips `true`→`false` gets `justSettled`
  for one 300ms window (cleared via `setTimeout`), then the row falls back to plain authoritative
  rendering — the authoritative `start_ts`/`end_ts` render immediately on the same poll that flips the
  flag, so there is no stale "still active" render frame. Hover tooltip
  (`@radix-ui/react-tooltip`) shows `run_id`/`tier`/`workflow`/duration/`agent_count`. Click handler is
  an explicit stub (`console.debug(...)`) noting `AGENTOPS-REPLAY-TIMELINE` builds the real target.
- **`App.tsx`**: plain `useState<PageView>` shell (`'activity' | 'tickets' | 'replay'`, default
  `'activity'`), no router dependency added. `'tickets'`/`'replay'` render explicit "coming soon"
  placeholder text only.
- **Tests** (Vitest + Testing Library, `dashboard-frontend/src/test/`): `useRunsPolling.test.ts`
  exercises the real hook against a mocked `fetch` (pagination-loop + no-wasted-request cases).
  `RecentActivityGantt.test.tsx` and `App.test.tsx` mock the `useRunsPolling` hook itself (via
  `vi.mock('../api', ...)`) to deterministically control poll results across renders/`rerender()`
  calls, rather than driving real timers — this exercises the exact scenario test_plan.md's AC #3
  test describes ("render with an inferred-active fixture, then re-render with a poll result where
  the same run_id is now completed") without jsdom fake-timer fragility. 8/8 tests pass; `tsc -b` and
  `vite build` (production bundle) both succeed cleanly.
- Backend regression sanity check (Step 8): all 30 tests across
  `test_agent_ops_dashboard_{ingest,api,concurrency,api_boundary}.py` +
  `test_api_read_model_guard.py` pass unchanged — confirms no code under
  `src/api/agent_ops_dashboard/` or `src/api/server.py`/`read_model_cache.py` was touched.

### Follow-up fix pass (DOD_BLOCKED remediation)

The first Implement pass closed all 4 Acceptance Criteria but omitted two tests that
`staging_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/test_plan.md`'s "Anti-Drift Test Guards"
section explicitly required. The done-checker caught the gap at Verify and set the ticket to
`DOD_BLOCKED`. This pass adds exactly those two guards; nothing from the first pass was modified.

- **API-surface guard** — `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` (new Python
  test). Scans `dashboard-frontend/src/**/*.{ts,tsx}` for any of the four stale backend path strings
  the ticket's own boilerplate Related Code Areas listed (`src/api/server.py`,
  `src/api/read_model_cache.py`, `src/api/routes/history.py`, `src/api/ws/stream.py`) — none of which
  are the dashboard's real backend (`src/api/agent_ops_dashboard/{main,ingest,models}.py`). Follows the
  same forbidden-literal-string-scan convention as
  `tests/architecture/test_no_old_structural_content_paths.py`. Chosen as a Python test rather than a
  Vitest test because it is checking source text/static analysis, matching this repo's existing
  `tests/architecture/` guard-test convention, not exercising frontend runtime behavior.
- **No client-side `is_inferred_active` duplication guard** —
  `dashboard-frontend/src/test/GanttBar.test.tsx` (new Vitest test file; `GanttBar.tsx` previously had
  no dedicated unit test). Asserts (a) `GanttBar.tsx`'s source never calls `Date.now()` or constructs
  `new Date(...)` (verified via Vite's `?raw` import, already typed through the existing `vite/client`
  types entry — no new dependency added), (b) the branch selection is a direct
  `if (run.is_inferred_active)` check, (c) a fixture with `is_inferred_active: false` but a
  suspiciously "still running"-looking `start_ts`/`end_ts: null` still renders the authoritative
  branch, and (d) a fixture with `is_inferred_active: true` but an `inferred_start_ts` three hours old
  (well past the backend's `ACTIVE_WINDOW_MINUTES=10`) still renders the inferred branch — proving the
  component always trusts the backend-computed flag rather than re-deriving activity from timestamps.

Both tests are documented in `staging_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/plan.md`'s
"Deviations (follow-up fix pass — DOD_BLOCKED remediation)" section.

## Test Summary

- `cd dashboard-frontend && npm test` → 4 test files, 12 tests, all passing
  (`useRunsPolling.test.ts` ×2, `RecentActivityGantt.test.tsx` ×4, `App.test.tsx` ×2,
  `GanttBar.test.tsx` ×4 [new]).
- `cd dashboard-frontend && npx tsc -b` → clean, no type errors.
- `cd dashboard-frontend && npm run build` → production Vite bundle builds successfully.
- `pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"` → 31 passed (the prior 30 plus the new API-surface guard test).
- All 4 Acceptance Criteria mapped 1:1 to `RecentActivityGantt.test.tsx` cases per the plan's
  Acceptance Criteria Map.
- Both `test_plan.md` Anti-Drift Test Guards ("API-surface guard", "No `is_inferred_active`
  computation duplicated client-side") now have dedicated tests, closing the gap that caused
  `DOD_BLOCKED`.

## Files Changed

- `dashboard-frontend/package.json`
- `dashboard-frontend/vite.config.ts`
- `dashboard-frontend/tsconfig.json`
- `dashboard-frontend/tsconfig.app.json`
- `dashboard-frontend/tsconfig.node.json`
- `dashboard-frontend/index.html`
- `dashboard-frontend/.gitignore`
- `dashboard-frontend/src/main.tsx`
- `dashboard-frontend/src/index.css`
- `dashboard-frontend/src/App.tsx`
- `dashboard-frontend/src/api.ts`
- `dashboard-frontend/src/components/GanttBar.tsx`
- `dashboard-frontend/src/components/Legend.tsx`
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`
- `dashboard-frontend/src/test/setup.ts`
- `dashboard-frontend/src/test/useRunsPolling.test.ts`
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
- `dashboard-frontend/src/test/App.test.tsx`
- `dashboard-frontend/src/test/GanttBar.test.tsx` (new — follow-up fix pass)
- `dashboard-frontend/package-lock.json` (generated by `npm install`)
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` (new — follow-up fix pass)

No files under `src/api/agent_ops_dashboard/`, `frontend/`, or `docs/` were modified — this ticket is
additive-only: a new top-level `dashboard-frontend/` directory, plus one new architecture-guard test
under `tests/tools/`.

## Completion Summary

Built the `dashboard-frontend/` scaffold (React 19 + Vite 7 + TypeScript + Tailwind 4 + Radix UI +
Vitest, mirroring `frontend/`'s conventions) as a new, wholly separate SPA, and implemented the
`RecentActivityGantt` default-landing view on top of it: a typed `api.ts` client with an
offset-looping polling hook (guards against `GET /api/runs`'s pagination truncation on busy windows),
a `GanttBar` component whose authoritative-completed and inferred-active render paths share zero CSS
class tokens (structurally enforcing AC #4), a `Legend` reusing the same bucket→class mapping, and an
`App.tsx` shell landing on Recent Activity by default with stub-only Tickets/Replay placeholders. All
4 Acceptance Criteria are covered by passing Vitest tests.

A follow-up fix pass closed a `DOD_BLOCKED` gap: `test_plan.md`'s two Anti-Drift Test Guards (an
API-surface guard against stale backend path references, and a guard against client-side
re-derivation of `is_inferred_active`) were specified but not implemented in the first pass. Both are
now covered — a new Python architecture-guard test
(`tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`) and a new Vitest component test
(`dashboard-frontend/src/test/GanttBar.test.tsx`). The full suite is green: 4 frontend test files (12
tests), clean `tsc -b`/`vite build`, and the extended backend regression command (31 tests, the prior
30 plus the new guard). No backend, `frontend/`, Makefile, or CI changes were made — strictly
additive, presentation-layer and test-only code over the already-parity-tracked read-only `/api/runs`
surface.
