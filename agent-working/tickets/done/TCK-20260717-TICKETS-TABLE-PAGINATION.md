---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-TICKETS-TABLE-PAGINATION
phase: done
date: 2026-07-17
tags: [performance]
---

# TCK-20260717-TICKETS-TABLE-PAGINATION

## Title
Add pagination to the Tickets view and its backend endpoint

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The Tickets view fetches and renders the full ticket corpus (1,109 rows observed) as one unvirtualized table with no pagination. This works today but is a scalability risk as the corpus keeps growing. Explicitly lower priority than the dashboard's other UI issues and should be tracked/implemented independently rather than blocking them.

## Scope
- Add limit and offset query params to GET /api/tickets (main.py + ingest.py get_tickets), mirroring the existing /api/runs pattern (Query(default=50, ge=1, le=100)/offset=0).
- Update TicketsView.tsx to request bounded pages through fetchTickets instead of a single unbounded fetchTickets({}) call.
- Provide a dedicated facets/options source for filter-dropdown values (tier/layer/status/priority/tags) so they continue reflecting the full corpus even when only one page of rows is loaded, rather than silently narrowing to page-1 values.
- Decide and implement the fate of client-side column-sort (toggleColumnSort/sortRows) under pagination — either server-side sort only, or explicitly scope it to sort only the current page.

## Out of Scope
- Adding a total-count field to GET /api/runs (the sibling endpoint's existing gap) — that endpoint itself is not touched by this ticket.
- Any UI redesign beyond pagination/windowing controls.

## Acceptance Criteria
- [ ] GET /api/tickets accepts limit and offset query params (mirroring /api/runs's pattern) and ingest.py's get_tickets() slices the filtered+sorted result to the requested page instead of returning the entire corpus.
- [ ] TicketsView.tsx requests bounded pages through fetchTickets instead of one unbounded call, and the number of rendered ticket-row DOM nodes stays bounded to page size regardless of total ticket count (verified via a test mocking >1000 rows).
- [ ] Filter-dropdown option population continues to reflect the full corpus's tiers/layers/statuses/priorities/tags even when only one page of rows is loaded, via a dedicated facets source, not silently truncated to page-1 values.
- [ ] Client-side column-sort is either disabled/replaced by server-side sort under pagination, or explicitly scoped to sort only the current page — never silently a partial-corpus sort presented as a full-table sort.

## Related Tickets
- TCK-20260716-AGENTOPS-TICKETS-VIEW
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260716-AGENTOPS-BUILD-SERVE

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/models.py
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/test/TicketsView.test.tsx
- tests/tools/test_agent_ops_dashboard_api_boundary.py

## Assumptions / Open Questions
- This is explicitly lower priority than the other five dashboard UI tickets per the proposal author — should not block or be blocked by them.
- /api/runs's existing pagination has no total-count field and works around it via looping (fetchAllRunsSince) — /api/tickets should decide upfront whether to add a total_count field rather than repeat that gap.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260717-TICKETS-TABLE-PAGINATION/plan.md`'s
7 steps, in order.

- **Step 1 (`models.py`)**: added `TicketFacets` (`tiers`/`layers`/`statuses`/
  `priorities`/`tags`: `List[str]`) and `TicketsPage` (`items`/`total_count`/
  `facets`) Pydantic models. `TicketSummary` untouched.
- **Step 2 (`ingest.py::get_tickets`)**: added `limit: Optional[int] = None,
  offset: int = 0` params. Introduced `TicketsQueryResult(list)` — a `list`
  subclass carrying `.total_count`/`.facets` alongside the paged
  `TicketSummary` items. This was the one design decision plan.md left to the
  implementer ("dict/namedtuple, or route assembles from three return
  values"): a list subclass was chosen specifically because it is the only
  shape under which the three pre-existing direct-call tests
  (`for r in results: r.ticket_id`) keep passing with the literal zero
  modification plan.md's Resolved Decision #4 requires — a namedtuple/dict
  return would have broken their iteration semantics. `total_count`/`facets`
  are computed over `filtered` (post-filter, pre-slice) via a new
  `_distinct_sorted()` helper, matching Resolved Decision #3's exact
  `sorted({r["tier"] for r in filtered if r.get("tier")})` pattern.
- **Step 3 (`main.py::list_tickets`)**: added `limit`/`offset` `Query(...)`
  params (`ge=1, le=500` / `ge=0`), changed `response_model` to `TicketsPage`,
  and the route now assembles `TicketsPage(items=list(result),
  total_count=result.total_count, facets=TicketFacets(**result.facets))`.
- **Step 4 (`api.ts`)**: added `TicketsFacets`/`TicketsPage` interfaces
  (field names kept snake_case, matching this file's existing "mirrors
  models.py exactly" convention rather than converting to camelCase), added
  `limit`/`offset` to `FetchTicketsParams`, `fetchTickets()` now returns
  `Promise<TicketsPage>`.
- **Step 5 (`TicketsView.tsx`)**: added `PAGE_SIZE = 100` constant;
  `loadInitial`/`applyFilters`/`toggleDateSort` now call `fetchTickets` with
  `limit`/`offset` (via `buildFetchParams`, which now also emits
  `limit: PAGE_SIZE, offset: 0`) and split the response into `rows` (from
  `.items`), a new `optionsFacets` state (from `.facets`), and a new
  `totalCount` state (from `.total_count`). Removed `distinctValues`/
  `distinctTags` (no longer needed — facets arrive pre-sorted/pre-deduped
  from the backend) and the `optionsSource` state entirely; the four
  `FilterSelect`s and the tag-pill list now read directly from
  `optionsFacets.*`. Added `isPageScopedSort = columnSort !== null &&
  totalCount > rows.length` and a `data-testid="column-sort-page-scoped-note"`
  element rendered under that condition — the observable signal AC #4
  requires. `sortRows`/`toggleColumnSort`/`columnSort` themselves are
  byte-for-byte unchanged, per the plan's chosen page-scoped branch.
  `TicketsView.test.tsx`'s `mockFetchReturning` was updated to accept an
  optional `envelopeOverrides` second argument and wrap the passed items in
  the `{items, total_count, facets}` envelope, defaulting `facets` to a
  `computeFacetsFromItems()` derivation (mirrors the old client-side
  `distinctValues`/`distinctTags` logic) so all ~9 pre-existing call sites
  keep compiling and passing unmodified. Rewrote the `'TicketsView —
  client-side column sort'` describe block into two tests: one asserting
  no new fetch + the page-scoped note appears when `total_count >
  items.length`, one asserting the note is absent on a single page. Added
  new `'TicketsView — pagination'` (bounded row count on a >1000-row mock,
  bounded `limit=100&offset=0` on initial load) and `'TicketsView — facets
  independent of page window'` (facets values absent from the loaded page
  still populate the dropdown/tag-pill list) describe blocks.
- **Step 5b (`test_agent_ops_dashboard_api.py`)**: changed
  `tickets = resp.json()` to `tickets = resp.json()["items"]` in
  `test_get_tickets_title_is_distinct_from_ticket_id`. No other test in the
  file touched.
- **Step 6**: full backend + frontend regression run (below), then appended
  a third, clearly-delimited paragraph to `INFRA-275`'s `v2_evidence` and a
  third segment to its `test_path` in
  `docs/parity_ledger/infrastructure.yaml`, verified via `git diff` that
  only additions landed (the two pre-existing appended paragraphs/segments
  from `TCK-20260716-AGENTOPS-TICKETS-VIEW`/`TCK-20260717-TICKET-TITLE-PARSE-FIX`
  are untouched). Also verified via `git diff` that zero lines changed in
  `list_runs`/`get_runs`/`_build_run_summary`/`FetchRunsParams`/`fetchRuns`/
  `fetchAllRunsSince`.

### Deviation from plan.md (not scoped by any of the 7 steps)

`dashboard-frontend/src/test/App.test.tsx` has its own `mockTicketsFetch`
helper (independent of `TicketsView.test.tsx`'s `mockFetchReturning`) that
also mocked `fetch` to resolve a bare `TicketSummary[]`. Neither plan.md nor
investigation.md named this file — investigation.md's "TicketsView.tsx is
the only frontend consumer" claim covered production code correctly but did
not audit `App.test.tsx`'s own independent fetch mock. Running the frontend
suite after Steps 4-5 surfaced 2 failing tests in `App.test.tsx`
(`TypeError: Cannot read properties of undefined (reading 'tiers')`, since
`optionsFacets` came back `undefined` under the old bare-array response
shape). Fixed by updating `mockTicketsFetch` to wrap its `items` argument in
the same `{items, total_count, facets}` envelope, mirroring the
`mockFetchReturning` fix. This is a one-line-helper fix with no assertion
changes, in the same spirit as the plan's Step 5 `mockFetchReturning` fix —
recorded here and in `plan.md`'s Deviations section per CLAUDE.md's
"never silently deviate" rule.

## Test Summary

Backend (`python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_api.py
tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
tests/architecture/test_api_read_model_guard.py -m "not slow"`): 42 passed.
Includes 5 new tests (`test_get_tickets_slices_to_requested_page`,
`test_get_tickets_limit_offset_default_preserves_existing_behavior`,
`test_facets_source_reflects_full_filtered_corpus_not_just_current_page`,
`test_list_tickets_route_rejects_out_of_range_limit`,
`test_list_tickets_route_passes_limit_offset_through_to_cache`) and all
pre-existing tests unmodified/passing, including the three direct-call
AND/OR-filter tests confirmed to require zero changes.

Frontend (`cd dashboard-frontend && npm test -- --run`): 49 passed (7 test
files, including the 3 new `TicketsView.test.tsx` tests, 2 rewritten
column-sort tests, and `App.test.tsx`'s deviation fix).
`npx tsc -b` and `npm run build` both clean.

## Files Changed

- `src/api/agent_ops_dashboard/models.py`
- `src/api/agent_ops_dashboard/ingest.py`
- `src/api/agent_ops_dashboard/main.py`
- `dashboard-frontend/src/api.ts`
- `dashboard-frontend/src/views/TicketsView.tsx`
- `dashboard-frontend/src/test/TicketsView.test.tsx`
- `dashboard-frontend/src/test/App.test.tsx` (deviation — see above)
- `tests/tools/test_agent_ops_dashboard_ingest.py`
- `tests/tools/test_agent_ops_dashboard_api.py`
- `docs/parity_ledger/infrastructure.yaml`
- `docs/observability/agent_ops_dashboard_contract.md`

## Completion Summary

All 4 acceptance criteria met: `GET /api/tickets` accepts `limit`/`offset`
(`Query(default=100, ge=1, le=500)` / `Query(default=0, ge=0)`) and
`get_tickets()` slices the filtered+sorted result to the requested page,
returning a `TicketsPage` envelope (`items`/`total_count`/`facets`) instead
of a bare list; `TicketsView.tsx` requests bounded pages
(`limit=100&offset=0`) and rendered row count stays bounded regardless of
total ticket count; filter-dropdown options are sourced from a dedicated
`facets` field computed over the full filtered-but-unpaginated corpus, so
they never silently narrow to page-1 values; client-side column-sort is
explicitly scoped to the current page via a new observable
`column-sort-page-scoped-note` signal, with zero changes to the underlying
sort logic itself (the chosen, plan-approved AC #4 branch). Backend and
frontend regression suites pass in full, `tsc -b`/`npm run build` are clean,
and `INFRA-275`'s parity ledger entry was updated append-only. One deviation
from plan.md — `App.test.tsx`'s independent fetch mock helper, not named in
plan.md/investigation.md, required the same envelope-wrapping fix as
`TicketsView.test.tsx`'s `mockFetchReturning` — is documented above and in
`plan.md`'s Deviations section.

`docs/observability/agent_ops_dashboard_contract.md`'s route table and
Ingest/cache section (both flagged as stale by the investigator, since they
still described `GET /api/tickets` as unpaginated returning a bare list)
were updated in this Verify-fix round to describe the `limit`/`offset`
params, the `TicketsPage`/`TicketFacets` models, and the pre-slice
facets/total_count computation.
