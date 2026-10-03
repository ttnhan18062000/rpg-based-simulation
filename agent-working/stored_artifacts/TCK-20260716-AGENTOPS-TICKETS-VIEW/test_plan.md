---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-TICKETS-VIEW
artifact_type: test_plan
tags: [observability, agent-monitoring]
---

# Test Plan — TCK-20260716-AGENTOPS-TICKETS-VIEW

## Regression Surface

This ticket is frontend-only (TypeScript/React, extending the existing `dashboard-frontend/`
scaffold), unless the plan decides to close the backend filter-test gap noted in
investigation.md Risk #3, in which case exactly one new backend test file may be added
(additive only — no changes to `ingest.py`/`main.py`/`models.py` themselves).

- unit/integration (backend, must stay green, unmodified):
  - `tests/tools/test_agent_ops_dashboard_ingest.py` — including the ticket-run join tests
    (`test_ticket_run_join_returns_all_matches_sorted_desc`,
    `test_ticket_run_join_none_start_ts_sorts_last_not_first`) and the null-body-section test
    (`test_ticket_missing_body_sections_surfaces_null_not_error`) this view's rendering must
    trust, not reimplement.
  - `tests/tools/test_agent_ops_dashboard_api.py`.
  - `tests/tools/test_agent_ops_dashboard_api_boundary.py` — including
    `test_all_five_routes_are_declared` (asserts `/api/tickets` is present) and
    `test_typed_response_models_not_dict`.
  - `tests/tools/test_agent_ops_dashboard_concurrency.py` — including its `get_tickets()`-then-
    `get_runs()` cache-straddle test.
- architecture guard, must stay green:
  - `tests/architecture/test_api_read_model_guard.py` — no new coupling from
    `src/api/agent_ops_dashboard/` into `src/api/read_model_cache.py`/`src/api/server.py`.
  - `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — directory-wide glob over
    `dashboard-frontend/src/**/*.{ts,tsx}`, automatically covers the new
    `views/TicketsView.tsx` and any new `api.ts` additions without a ticket-specific duplicate.
    Must stay green with zero references to `src/api/server.py`, `src/api/read_model_cache.py`,
    `src/api/routes/history.py`, or `src/api/ws/stream.py`.
- frontend, **must be updated, not merely kept passing as-is**:
  - `dashboard-frontend/src/test/App.test.tsx` — its two current assertions referencing
    `"Tickets view coming soon."` (lines 53-59, 61-77 as read) are **expected to be falsified**
    by a correct implementation of this ticket (see investigation.md Risk #5). This file must be
    edited as part of this ticket's changes — treat the old assertions as intentionally
    superseded. The updated file should assert the real `TicketsView` (or equivalent testid)
    renders when the Tickets tab is active, and that Replay/Recent Activity still render their
    existing (unaffected) content.
  - `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`, `GanttBar.test.tsx`,
    `ReplayTimelineView.test.tsx`, `useRunsPolling.test.ts` — unrelated to this ticket's surface,
    must stay green unmodified (sanity check only).

## New Tests Required

Per this ticket's Acceptance Criteria (`tickets/inprogress/TCK-20260716-AGENTOPS-TICKETS-VIEW.md`)
plus the sort/filter/coverage findings in investigation.md. All new frontend tests are Vitest +
Testing Library, colocated under `dashboard-frontend/src/test/`; the optional backend test is
pytest, colocated under `tests/tools/`.

- **`TicketsView renders rows from fetchTickets covering all three lifecycle states`**
  Category: unit (component)
  Verifies: AC #1 — given a `TicketSummary[]` fixture with `lifecycle_state` values of
  `inprogress`/`done`/`todos`, all three appear as rows with no lifecycle silently dropped or
  merged.
  Location: `dashboard-frontend/src/test/TicketsView.test.tsx`

- **`filter bar narrows rows AND-across-dimensions, OR-within-tag, via server query params`**
  Category: unit (component), mocked `fetchTickets`/`fetch` call-args assertion
  Verifies: AC #2 — selecting a tier + a layer + two tags asserts the resulting `fetchTickets`
  (or underlying `fetch`) call carries `tier=<x>&layer=<y>&tag=<a>&tag=<b>` (repeated `tag`, per
  `main.py`'s `Query(default=None)` list param), proving filtering is delegated to the backend's
  query params, not re-filtered client-side over a full unfiltered fetch. A second case with only
  two tags selected (no tier/layer) asserts both `tag` values are sent and relies on the backend's
  own OR-within-tag semantics — this test does not re-verify OR-within-tag logic itself (that's
  `ingest.py`'s job, see the optional backend test below), only that the client sends the right
  params.
  Location: `dashboard-frontend/src/test/TicketsView.test.tsx`

- **`linked-runs control surfaces every matching_runs entry as a separate link, never collapsed`**
  Category: unit (component) — direct guard against investigation.md's read of AC #3
  Verifies: AC #3 — given a `TicketSummary` fixture whose `matching_runs` has 2+ entries (already
  sorted `start_ts` descending per the fixture, mirroring the real backend contract), the rendered
  row exposes a link/control per entry (not a single link, not a "show more" that never reveals
  the rest), and clicking any one of them navigates using **that** entry's own `run_id` (not
  always the first). A second case with `matching_runs = []` asserts no link/picker control is
  rendered for that row (not an empty link or broken href).
  Location: `dashboard-frontend/src/test/TicketsView.test.tsx`

- **`null tier/priority/type render as null/empty, never a placeholder string`**
  Category: unit (component) — direct guard against AC #4
  Verifies: AC #4 — given a `TicketSummary` fixture with `tier: null, priority: null,
  ticket_type: null`, the rendered row's corresponding cells contain no text content (or an
  explicit empty-cell testid), and specifically assert the cells do **not** contain `"N/A"`,
  `"null"`, `"—"`, `"unknown"`, or any other placeholder string — the negative assertion is the
  point, since a naive `value ?? 'N/A'` fallback would pass a looser "renders without crashing"
  test.
  Location: `dashboard-frontend/src/test/TicketsView.test.tsx`

- **`row-link navigates to that row's Replay timeline via the existing App navigation state`**
  Category: integration (component)
  Verifies: clicking a Tickets row's single link (or one entry of its multi-run picker) switches
  `App`'s active view to Replay and renders `ReplayTimelineView` scoped to that specific
  `matching_runs[i].run_id` — reusing `App.tsx`'s existing `handleSelectRun`/`selectedRunId`
  wiring from `AGENTOPS-REPLAY-TIMELINE`, not a new/parallel navigation mechanism.
  Location: `dashboard-frontend/src/test/App.test.tsx` (owns cross-view navigation assertions per
  existing convention, mirroring the Gantt-row navigation test already there)

- **`App-shell scaffold smoke test: Tickets tab renders the real TicketsView, other tabs unaffected`**
  Category: integration / architecture guard
  Verifies: replaces `App.test.tsx`'s now-stale `"Tickets view coming soon."` assertions
  (see Regression Surface) with: activating the Tickets tab renders real `TicketsView` content
  (not the placeholder string), while Recent Activity and Replay continue to render exactly as
  before — guards against this ticket accidentally touching Gantt/Replay rendering logic.
  Location: `dashboard-frontend/src/test/App.test.tsx`

- **(Optional, per investigation.md Risk #3 — include only if the plan confirms it's in scope)
  `get_tickets AND-across-dimensions/OR-within-tag filter semantics`**
  Category: unit (backend), additive-only (asserts existing `ingest.py` behavior, changes no
  source)
  Verifies: AC #2's actual server-side guarantee — a fixture with several tickets spanning
  distinct `tier`/`layer`/`workflow_status`/`priority`/`tags` combinations, asserting: (a)
  combining `tier` + `layer` returns only rows matching both (AND), (b) passing two `tags` values
  returns rows matching either (OR), (c) combining a dimension filter with a tag filter is AND
  between the two groups.
  Location: `tests/tools/test_agent_ops_dashboard_ingest.py` (new test function(s), no edits to
  existing ones)

## Scoped Pytest Commands

```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

Never: `pytest tests/`.

Frontend test command (existing convention, unchanged):

```
cd dashboard-frontend && npm test
```

## Anti-Drift Test Guards

Given `AGENTOPS-ACTIVITY-GANTT`'s `DOD_BLOCKED` history — anti-drift guards specified in its
test_plan.md but skipped in the first Implement pass, requiring a dedicated follow-up fix pass —
**every guard below must be implemented in the same pass as the feature code**, not deferred.

1. **API-surface guard — already covered, no new test needed.**
   `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` globs recursively over
   `dashboard-frontend/src/**/*.{ts,tsx}`, so it automatically picks up `views/TicketsView.tsx`
   and any new `api.ts` additions without modification. The obligation is procedural: **run this
   test as part of Verify and confirm it passes**, the same class of guard silently skipped in
   the Gantt ticket's first pass.

2. **No client-side re-implementation of the tier/layer/status/priority AND filter or the
   OR-within-tag semantics.** A `?raw` source-text guard (mirroring `GanttBar.test.tsx`'s
   pattern: `import TICKETS_VIEW_SOURCE from '../views/TicketsView.tsx?raw'`) asserting the
   component contains no client-side `.filter(` call applied to a fetched `TicketSummary[]` array
   keyed on `tier`/`layer`/`status`/`priority`/`tags` — filtering must be expressed only as query
   params passed to `fetchTickets`, never as a second filter pass over an already-fetched full
   list. Paired with the call-args test above.

3. **No client-side re-sort/re-derivation of `matching_runs`.** Source-text guard: assert the
   component contains no `.sort(` call applied to a `matching_runs` array — the backend already
   returns it `start_ts`-descending (`ingest.py:178-199`); this view must trust that order.

4. **Non-date column sort, if implemented per investigation.md Risk #2's resolution, must be
   client-side only and must never mutate the params sent to `fetchTickets` for the `sort` query
   param beyond `date_asc`/`date_desc`.** A test asserting that toggling a tier/layer/status/
   priority/tag column header re-orders the already-rendered rows without triggering a new
   `fetchTickets` call (or, if it does trigger one, that the `sort` param sent is unchanged from
   `date_asc`/`date_desc` — never `tier_asc`/`layer_desc`/etc., which the backend does not
   support and would silently no-op server-side per `ingest.py`'s date-only sort key).
   Location: `dashboard-frontend/src/test/TicketsView.test.tsx`. If the plan instead defers
   non-date sorting entirely (Scope bullet 3 not implemented this pass), this guard is replaced
   by a single explicit note in Implementation Notes recording that deferral — not silently
   dropped.

5. **Null-vs-placeholder guard** (already listed under New Tests Required as the negative
   assertion against `"N/A"`/`"null"`/`"—"`/etc.) — restated here because it is the guard most
   likely to be silently satisfied by a superficially-passing "renders without crashing" test
   that a looser assertion (`toBeInTheDocument()` on the row) would not catch.

6. **Out-of-scope-view guard** (the updated `App.test.tsx` test above) — asserts Recent Activity
   and Replay continue to render unaffected after this ticket lands, catching accidental
   incidental changes to sibling views' rendering logic while wiring row-link navigation.

7. **Backend-untouched guard** (unless investigation.md Risk #3's optional backend test is
   accepted, in which case this becomes "backend source-untouched, tests-only-added guard") — the
   Scoped Pytest Command above, run as part of Verify, proves this ticket did not modify
   `src/api/agent_ops_dashboard/{main,ingest,models}.py`'s filter/sort/join logic instead of
   consuming it. A green diff on that command combined with `git diff --stat` showing no changes
   under `src/api/agent_ops_dashboard/` (or only a new test function, never a change to existing
   function bodies) is the actual verification, not just "tests still pass."
