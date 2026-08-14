---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-ACTIVITY-GANTT
artifact_type: test_plan
tags: [observability, agent-monitoring]
---

# Test Plan — TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Regression Surface

This ticket is frontend-only (TypeScript/React, new `dashboard-frontend/` scaffold — see
investigation.md Risk #2 for the location decision the plan must confirm). No Python source under
`src/api/agent_ops_dashboard/` should be modified, so the backend's own regression suite is a
**sanity check that nothing was inadvertently touched**, not a suite this ticket's changes should
affect:

- unit/integration (backend, must stay green, unmodified):
  - `tests/tools/test_agent_ops_dashboard_ingest.py` (18 tests — ticket parsing, ticket-run join,
    inferred-active window/boundary/exclusion, files_touched dedup, legacy schema tolerance)
  - `tests/tools/test_agent_ops_dashboard_api.py` (5 tests — 404s, malformed-JSONL surfaced in
    `/api/health`)
  - `tests/tools/test_agent_ops_dashboard_concurrency.py` (2 tests — RLock rebuild atomicity, active→
    completed flip atomicity)
  - `tests/tools/test_agent_ops_dashboard_api_boundary.py` (5 tests — typed `response_model`s only, no
    `StaticFiles` mount yet, no write path)
- architecture guard: `tests/architecture/test_api_read_model_guard.py` — must stay green; this ticket
  must not introduce any new coupling from `src/api/agent_ops_dashboard/` back into
  `src/api/read_model_cache.py` or `src/api/server.py` (that coupling does not exist today and should
  not be created — see investigation.md Anti-Drift Hazards).
- there is **no existing frontend test suite for a dashboard** to regress against (none existed before
  this ticket). `frontend/src/test/useSimulation.test.tsx` (the existing game-UI frontend's Vitest
  suite) is unrelated to this new scaffold and out of this ticket's regression surface entirely — it
  lives in a different, unrelated project (`frontend/`, not the new dashboard scaffold).

## New Tests Required

Per this ticket's Acceptance Criteria (`tickets/inprogress/TCK-20260716-AGENTOPS-ACTIVITY-GANTT.md`),
plus the ownership/pagination questions raised in investigation.md. All new tests are Vitest +
Testing Library, colocated under the new scaffold's `src/test/` (mirroring
`frontend/src/test/`'s convention) — run locally, not CI-gated (see investigation.md: frontend has
zero CI coverage repo-wide today, and `AGENTOPS-BUILD-SERVE`'s Out of Scope explicitly excludes adding
frontend CI).

- **`completed run renders as a solid authoritative bar with is_inferred_active=false`**
  Category: unit (component)
  Verifies: AC #1 — given a `RunSummary` fixture with `is_inferred_active: false`, `start_ts`/`end_ts`
  set, the rendered bar uses the authoritative-style CSS class/token and its extents derive from
  `start_ts`/`end_ts`, not from `inferred_start_ts` (which should be `null`/absent on this fixture).
  Location: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

- **`run present only in the inferred-active set renders as an inferred bar anchored at inferred_start_ts`**
  Category: unit (component)
  Verifies: AC #2 — given a `RunSummary` fixture with `is_inferred_active: true`, `start_ts: null`,
  `end_ts: null`, `inferred_start_ts` set, the bar's left edge derives from `inferred_start_ts` and its
  right edge is pinned to "now" (not a fixed/absent value).
  Location: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

- **`inferred-active bar and authoritative-completed bar never share styling`**
  Category: unit (component) — direct guard against Anti-Drift Hazard (styling drift)
  Verifies: AC #4 — asserts the rendered class/style token sets for an inferred-active fixture and a
  completed fixture are disjoint (not just "the inferred one additionally has an estimate label"); also
  asserts an explicit estimate-label element/text is present only on the inferred-active bar.
  Location: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

- **`active-to-completed transition across polls updates the bar without a stale 'still active' state`**
  Category: unit (component), simulated poll cycle
  Verifies: AC #3 — render with an inferred-active fixture for `run_id=X`, then re-render/update props
  with a poll result where the same `run_id=X` is now present in `runs_by_id` (i.e.
  `is_inferred_active: false`, authoritative `start_ts`/`end_ts` now populated) and assert: (a) the bar
  for `run_id=X` never shows `is_inferred_active: true` styling/label after the second render, and
  (b) the authoritative `start_ts`/`end_ts` are what's rendered post-transition, not the earlier
  `inferred_start_ts`. A ≤300ms CSS transition per the UI spec is a visual nicety, not itself asserted
  numerically here (jsdom has no real paint timing) — the assertion is on final DOM state correctness,
  not animation duration.
  Location: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

- **`time-window polling paginates when a since-window's match count reaches the page limit`**
  Category: unit (data-fetching hook) — direct guard against investigation.md Risk #3
  Verifies: given a mocked `/api/runs?since=...` that returns exactly `limit` (e.g. 50) results on the
  first call and fewer than `limit` on a second call with `offset` advanced, the polling logic issues
  the second (and would issue a third if needed) request and the merged result set includes rows from
  both pages — i.e. the fetch layer does not silently treat a full first page as "the complete window."
  Also assert a single sub-`limit` page does **not** trigger a second request (no wasted calls in the
  common case).
  Location: `dashboard-frontend/src/test/useRunsPolling.test.ts` (or colocated with whichever
  data-fetching hook/module is introduced — module name TBD by the plan)

- **`scaffold smoke test: dashboard-frontend builds and the default landing view is RecentActivityGantt`**
  Category: integration / architecture guard
  Verifies: the new `dashboard-frontend/` project's `App`-level shell renders `RecentActivityGantt` as
  the default view (no other view selected) on initial mount — guards against the "default-landing
  view" requirement in Scope bullet 1 silently regressing if a later ticket (`AGENTOPS-TICKETS-VIEW`,
  `AGENTOPS-REPLAY-TIMELINE`) changes the shell's default state.
  Location: `dashboard-frontend/src/test/App.test.tsx`

## Scoped Pytest Commands

This ticket adds no Python source, so no new pytest target is introduced. The only pytest obligation
is the regression sanity check confirming the untouched backend + its architecture guard are still
green after this ticket's frontend-only changes land:

```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

Never: `pytest tests/`.

Frontend test command (once the scaffold's `package.json` exists, per the convention in
`frontend/package.json`'s own `vitest` wiring):

```
cd dashboard-frontend && npm test
```

(Exact script name — `test`/`vitest run`/`vitest` — is a plan-time decision; `frontend/package.json`
today has no `test` script at all despite having `vitest` as a devDependency, so this scaffold should
add one explicitly rather than assuming one is inherited.)

## Anti-Drift Test Guards

- **API-surface guard**: no test file, mock, or fetch client in this ticket's new code should reference
  `src/api/server.py`, `src/api/ws/stream.py`, `src/api/routes/history.py`, or
  `src/api/read_model_cache.py` — a grep-based or import-based guard test (Python side, e.g. extending
  `tests/architecture/test_api_read_model_guard.py`'s pattern, or a lightweight new check) catches
  accidental coupling back into the simulation engine's own API surface.
- **No `is_inferred_active` computation duplicated client-side**: a test asserting the frontend never
  independently computes "is this run still active" from raw `tools.jsonl`/timestamps — it must always
  render strictly from the `is_inferred_active`/`inferred_start_ts` fields the backend already computed.
  Prevents the frontend from silently reimplementing `ACTIVE_WINDOW_MINUTES` logic that is explicitly
  out of scope.
- **Styling mutual-exclusivity guard** (the AC #4 test above) doubles as an anti-drift guard: if a future
  change to the Gantt bar component collapses inferred/authoritative rendering onto a shared base style
  with only a boolean modifier, this test fails loudly rather than the drift being caught visually (or
  not at all).
- **Scope-creep guard for sibling views**: `dashboard-frontend`'s App-shell test (`App.test.tsx`) should
  assert that only `RecentActivityGantt` renders real content; any Tickets/Replay navigation targets
  present in the shell render as an explicit placeholder/stub, not functional views — catches this
  ticket accidentally implementing `AGENTOPS-TICKETS-VIEW` or `AGENTOPS-REPLAY-TIMELINE` ahead of
  schedule.
- **Pagination guard** (the `useRunsPolling` test above) is itself the anti-drift guard for
  investigation.md Risk #3 — without it, a naive single-request implementation would pass every other
  test today (current data volume is low) and silently regress in correctness as
  `agent-monitoring/*.jsonl` grows, with no test ever catching it.
