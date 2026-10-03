---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-TICKETS-VIEW
phase: done
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-TICKETS-VIEW

## Title
Tickets view: filterable/sortable table over ticket lifecycle

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a table view over all tickets (spanning tickets/inprogress, tickets/done, and tickets/todos) that can be filtered and sorted by tier, layer, status, priority, and tag, with each row linking to the matching run's Replay timeline. This is the frontend half of the concern; the backend endpoint it consumes is a separate, shared piece of infrastructure owned by the backend ticket in this same batch.

## Scope
- Build a TicketsView frontend component that renders a table of tickets sourced from GET /api/tickets
- Implement a filter bar for tier/layer/status/priority/tag with AND-across-dimensions, OR-within-tag semantics
- Implement column sorting by tier/layer/status/priority/tag
- Each row links to the Replay timeline view for its matching run(s)
- Render null tier/priority/type as null/empty (not an error or placeholder) when a ticket's body lacks those sections

## Out of Scope
- Implementing the /api/tickets endpoint itself, ticket frontmatter+body parsing, or ticket-to-run join logic (owned by AGENTOPS-DASHBOARD-BACKEND's ingest.py)
- The Replay timeline detail view content itself (owned by AGENTOPS-REPLAY-TIMELINE)
- The Recent Activity Gantt view (owned by AGENTOPS-ACTIVITY-GANTT)
- Backend caching or concurrency handling (owned by AGENTOPS-DASHBOARD-BACKEND)

## Acceptance Criteria
- [ ] Table renders rows from GET /api/tickets covering tickets/inprogress/, tickets/done/, and tickets/todos/
- [ ] Filtering by tier/layer/status/priority/tag narrows rows correctly (AND across dimensions, OR within tag)
- [ ] Each row's linked-runs control surfaces every matching_runs entry (sorted start_ts descending) as links to that run's Replay timeline, not collapsed to one
- [ ] A ticket with null tier/priority/type (missing body section) renders as null/empty in the table, not an error or placeholder

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260529-OBS-PHASE27-API-DASHBOARD
- TCK-20260614-RESOURCE-DASHBOARD
- TCK-20260607-MON-DASHBOARD

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/main.py (REAL endpoint — GET /api/tickets, see note below; src/api/server.py below is STALE, do not use)
- src/api/agent_ops_dashboard/models.py (REAL TicketSummary/RunMatchSummary shapes, see note below)
- dashboard-frontend/src/api.ts (existing typed fetch client + useRunsPolling pattern to extend, NOT create fresh — scaffold already exists)
- dashboard-frontend/src/App.tsx (has a stubbed 'tickets' nav placeholder left for this ticket, same pattern AGENTOPS-REPLAY-TIMELINE's stub was)
- dashboard-frontend/src/views/RecentActivityGantt.tsx, dashboard-frontend/src/components/GanttBar.tsx (sibling view/component conventions to match: Vitest + Testing Library, disjoint CSS class tokens per state, ?raw source-text anti-drift tests)
- tools/validate_frontmatter.py
- tools/generate_registry.py
- docs/REGISTRY.yaml
- tickets/working_log.csv
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md
- experiments/agent_ops_dashboard/TEST_PLAN.md
- docs/guides/ticket_reporting.md
- STALE, do not use as a starting point: src/api/server.py, src/api/routes/history.py, src/observability/reporting/history_query.py — these were the backend ticket's own reuse-source references before it was built; the real backend is src/api/agent_ops_dashboard/
- STALE, do not use: "expected: frontend/src/views/TicketsView.tsx" — build at dashboard-frontend/src/views/TicketsView.tsx instead (separate SPA, confirmed architecture decision in docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md); frontend/ is the unrelated game-UI app

## Assumptions / Open Questions
- docs/REGISTRY.yaml is not a viable data source for this view since it only covers tickets/done/ and omits status/layer/priority; the view depends entirely on the backend ticket's /api/tickets endpoint reflecting full lifecycle coverage
- Ticket-run join collisions (43/618 confirmed) mean the UI must show multiple linked runs per ticket, not assume a 1:1 relationship

## Handoff Notes — confirmed 2026-07-17 by the session that built the other 3 tickets in this batch (all now DONE)

**Do not re-derive these from scratch during Investigate — they are confirmed, not guesses. Still run
the real Investigate/Plan phases; this just gives them a warm start, the same as the prior two
tickets in this batch each received.**

1. **GET /api/tickets already exists and already does server-side filtering/sorting — do not
   reimplement client-side.** Confirmed by direct read of `src/api/agent_ops_dashboard/main.py`
   (`list_tickets`, ~line 29): it accepts `tier`, `layer`, `status`, `priority`, `tag` (repeatable),
   `lifecycle`, `q`, and `sort` as query params and returns `List[TicketSummary]`. The AND-across-
   dimensions/OR-within-tag filtering this ticket's AC #2 asks for should be implemented by passing
   these query params to the backend, not by fetching everything and filtering in the browser.

2. **`TicketSummary` (`models.py`) already has every field this view needs**, including
   `matching_runs: List[RunMatchSummary]` (already sorted `start_ts` descending server-side, per
   AC #3 — do not re-sort client-side) and nullable `tier`/`ticket_type`/`priority` (already `None`
   when a ticket's body lacks the section, satisfying AC #4 — do not add a placeholder/default value
   for `null`).

3. **`dashboard-frontend/` already exists** (built by the sibling `AGENTOPS-ACTIVITY-GANTT` ticket) —
   do not scaffold a new project. Extend the existing `api.ts` (add a `fetchTickets(params)`
   function, following `fetchRuns`'s existing typed-fetch convention), and `App.tsx` has a `'tickets'`
   nav slot with a placeholder string ("Tickets view coming soon.", same shape as the `'replay'` stub
   `AGENTOPS-REPLAY-TIMELINE` replaced) — real Investigate should confirm the exact current text
   before writing a test that removes it.

4. **Anti-drift guards are not optional or an afterthought** — `AGENTOPS-ACTIVITY-GANTT`'s first
   Implement pass skipped its planned anti-drift guards and got `DOD_BLOCKED` at Verify, requiring a
   full follow-up fix pass. `AGENTOPS-REPLAY-TIMELINE` avoided this by planning its guards as an
   explicit, first-class plan step (not a prose mention) landing in the same Implement pass as the
   feature code. Do the same here: plan test_plan.md's anti-drift guards as their own numbered plan
   step with a concrete file path, and implement them in the same pass.
   `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` already globs
   `dashboard-frontend/src/**` recursively — it will automatically cover this ticket's new files with
   no ticket-specific duplicate needed for that specific guard.

5. **Plan-phase gate is a literal heading check, not a content check.** If `plan.md` has zero
   genuinely unresolved questions, do not write an `## Unresolved Questions` heading at all (not even
   with "None" underneath) — `tools/gate_checks/plan_gate_static.py::plan_has_unresolved_questions_heading`
   matches on heading presence alone and will trip `NEEDS_HUMAN_INPUT` regardless of the content
   beneath it. This bit `AGENTOPS-REPLAY-TIMELINE`'s first planner pass; fixed by removing the
   heading entirely.

6. **Nothing was committed incrementally during this batch's original implementation** — the first
   3 tickets' work sat uncommitted in the working tree until a user-requested checkpoint stopped the
   batch and committed everything in 4 commits (`bb869b3d`, `1ff5b556`, `c066880a`, `1c90e045`). If
   this ticket is implemented in the same session as `AGENTOPS-BUILD-SERVE` (the last ticket in
   `SEQUENCE.md`), consider committing after each ticket's Finalize rather than batching, to keep
   `git diff --stat` checks meaningful (a coverage gap this batch's own Test phase flagged: an empty
   diff against an untracked directory is weak evidence of "untouched," not strong evidence).

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260716-AGENTOPS-TICKETS-VIEW/plan.md`'s 11 steps.

- **Step 1** (`dashboard-frontend/src/api.ts`): added `RunMatchSummary`/`TicketSummary`/
  `FetchTicketsParams` interfaces mirroring `models.py` field-for-field, and `fetchTickets(params)`
  following `fetchRuns`'s existing `URLSearchParams` convention, with repeated `tag=` params built
  via `query.append('tag', t)` per tag.
- **Steps 2-6** (`dashboard-frontend/src/views/TicketsView.tsx`, new): one-shot fetch-on-mount
  table (`useState`/`useEffect` with a `cancelled` flag, matching `ReplayTimelineView.tsx`'s
  convention, not `useRunsPolling`'s interval pattern). Filter bar: single-select `<select>` for
  tier/layer/status(workflow_status)/priority, multi-select toggle pills for tag; every filter
  change calls `fetchTickets` with the new params and replaces `rows` with the server response
  (never re-filtered client-side). Linked-runs cell renders one button per `matching_runs` entry in
  array order (never `.sort()`ed), each calling `onSelectRun(entry.run_id)` with its own id; empty
  array renders no control. `tier`/`priority`/`ticket_type` cells render the raw nullable value
  (`{ticket.tier}` etc.) so React emits no text node for `null` — no placeholder fallback string.
  Client-side column sort added for tier/layer/status/priority/tag via one `[...rows].sort(...)`
  call over the already-fetched array (`sortRows`); the date column's sort stays server-side
  (`toggleDateSort` only ever sends `'date_asc'`/`'date_desc'` as `FetchTicketsParams.sort`).
- **Step 7** (`dashboard-frontend/src/App.tsx`): replaced the `"Tickets view coming soon."` stub
  with `<TicketsView onSelectRun={handleSelectRun} />`, reusing the existing navigation wiring
  verbatim.
- **Step 8** (`dashboard-frontend/src/test/App.test.tsx`): edited the two stub-referencing
  assertions (now checking for/against `data-testid="tickets-view"` instead of the removed stub
  string), added a real-TicketsView smoke test and a Tickets-row-to-Replay-timeline navigation
  test. Both new tests stub `globalThis.fetch` directly since `fetchTickets` (unlike
  `useRunsPolling`/`fetchRunTimeline`) is not mocked at the `../api` module level in this file.
- **Step 9** (`dashboard-frontend/src/test/TicketsView.test.tsx`): three `?raw` source-text guards
  landed in the same pass as the feature code (per the `AGENTOPS-ACTIVITY-GANTT` `DOD_BLOCKED`
  lesson) — no `.filter(` anywhere in `TicketsView.tsx` at all (matches
  `ReplayTimelineView.test.tsx`'s existing blanket-guard precedent, stricter than but consistent
  with the plan's "keyed on tier/layer/status/priority/tags" wording), no `.sort(` applied to
  `matching_runs`, and no `sort:` literal other than `'date_asc'`/`'date_desc'` anywhere in the
  file. One guard assertion (the `.sort()` call-count check) was rewritten mid-implementation after
  first failing: `distinctValues`/`distinctTags` also each call `.sort()` on their own local
  `Array.from(...)` option lists (unrelated to `rows`/`matching_runs`), so a strict "exactly one
  `.sort(` in the file" assertion over-fired; replaced with a targeted regex that only checks
  `matching_runs` is never the sort target.
- **Step 10** (`tests/tools/test_agent_ops_dashboard_ingest.py`): three new, additive-only test
  functions (`test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
  `test_get_tickets_or_within_tag`, `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`)
  against a 4-ticket fixture, closing investigation.md Risk #3's coverage gap. No existing test
  function or any of `main.py`/`ingest.py`/`models.py` was touched.
- **Step 11**: both scoped test commands pass (backend: 34 passed; frontend: 35 passed, 6 files).
  `git diff --stat` confirms zero changes under `src/api/agent_ops_dashboard/{main,ingest,models}.py`;
  all changed/new files are confined to `dashboard-frontend/src/**` and
  `tests/tools/test_agent_ops_dashboard_ingest.py` (plus the auto-updated `agent-monitoring/tools.jsonl`
  and this ticket's own artifacts).

**Deviation from plan.md** (documented in that file's new Deviations section): added a `Type`
column (`ticket_type`, `data-testid="type-cell-{id}"`) to the table, which Step 2's literal column
list omitted. AC #4 explicitly requires `tier`/`priority`/`ticket_type` null-safe rendering, which
is untestable without a rendered `ticket_type` cell — the omission in Step 2's column list was an
oversight relative to the ticket's own AC #4, not an intentional scope exclusion.

`dashboard-frontend/node_modules` did not exist at the start of this session (only
`package-lock.json` was present); ran `npm ci` to install before `npm test` could execute. Not a
plan deviation — no step assumed a pre-installed `node_modules`, and `npm ci` is a pure,
lockfile-driven install with no source changes.

## Test Summary

- `pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"` — 34 passed.
- `cd dashboard-frontend && npm test` (vitest) — 6 files, 35 tests passed, including the new
  `TicketsView.test.tsx` (10 tests: rendering, filter-bar server-param delegation, linked-runs,
  null-safe cells, client-side column sort, 3 anti-drift `?raw` guards) and the updated
  `App.test.tsx` (7 tests, including the new Tickets-tab smoke test and row-link-to-Replay
  navigation test).
- `npx tsc -b` — clean, no type errors.

## Files Changed

- `dashboard-frontend/src/api.ts` — added `RunMatchSummary`, `TicketSummary`,
  `FetchTicketsParams`, `fetchTickets()`.
- `dashboard-frontend/src/views/TicketsView.tsx` — new.
- `dashboard-frontend/src/App.tsx` — replaced the Tickets stub with `<TicketsView>`.
- `dashboard-frontend/src/test/TicketsView.test.tsx` — new.
- `dashboard-frontend/src/test/App.test.tsx` — updated stub assertions, added 2 new tests.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — 3 new additive test functions plus one
  shared fixture helper.
- `staging_artifacts/TCK-20260716-AGENTOPS-TICKETS-VIEW/plan.md` — added Deviations section.

## Completion Summary

Built `TicketsView.tsx`, a read-only filterable/sortable table over `GET /api/tickets`, and wired
it into `App.tsx` in place of the Tickets stub. All four acceptance criteria are met: rows span all
three lifecycle states; the tier/layer/status/priority/tag filter bar delegates AND-across-
dimensions/OR-within-tag filtering entirely to backend query params (never re-filtered
client-side, guarded by a source-text test); every `matching_runs` entry renders as its own link in
the backend's `start_ts`-descending order (never re-sorted) and navigates via the existing
`App.tsx` `handleSelectRun`/`selectedRunId` wiring; null `tier`/`priority`/`ticket_type` render as
empty cells, never a placeholder string. Column sorting for tier/layer/status/priority/tag (Scope
bullet 3) is implemented as a client-side re-order of the already-fetched array, with the date
column's sort remaining server-side and never sending a non-date `sort` value. Closed a
pre-existing backend test-coverage gap in `get_tickets`'s filter semantics with 3 new additive
tests. Both scoped test commands (backend pytest, frontend vitest) pass, `tsc -b` is clean, and
`git diff --stat` confirms no source-file changes under `src/api/agent_ops_dashboard/`.
