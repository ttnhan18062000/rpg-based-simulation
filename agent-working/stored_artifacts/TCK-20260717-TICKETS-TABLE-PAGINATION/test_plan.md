---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TABLE-PAGINATION
artifact_type: test_plan
tags: [observability, agent-monitoring, performance]
---

# Test Plan — TCK-20260717-TICKETS-TABLE-PAGINATION

## Regression Surface

**Backend (unit/integration), must keep passing (some require the
`.items`-unwrap or envelope-shape read-adjustment named below, not
behavior changes):**

- `tests/tools/test_agent_ops_dashboard_ingest.py`
  - `test_get_tickets_and_across_dimensions_filters_tier_and_layer` —
    must pass unmodified (zero-arg `get_tickets()` call, full-set return).
  - `test_get_tickets_or_within_tag` — must pass unmodified.
  - `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and` —
    must pass unmodified.
  - Any other existing ingest tests not touching `get_tickets` (ticket
    parsing, run join, inferred-active, files_touched) — unaffected, must
    pass unmodified.
- `tests/tools/test_agent_ops_dashboard_api.py`
  - `test_get_tickets_title_is_distinct_from_ticket_id` — **requires a
    read-adjustment** (`resp.json()` → `resp.json()["items"]` or equivalent)
    to keep passing against the new `TicketsPage` envelope; this is an
    envelope-shape accommodation, not a behavior change to the test's
    assertion.
  - `test_run_detail_404_for_unknown_run_id`, `test_run_timeline_404_for_unknown_run_id`,
    `test_run_detail_200_for_known_run_id` — unaffected (`/api/runs` routes),
    must pass unmodified.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py`
  - `test_typed_response_models_not_dict` — must pass unmodified; the new
    `TicketsPage` response_model still satisfies the `BaseModel`-subclass
    assertion via the `else` branch (non-`List[...]` origin).
  - `test_all_five_routes_are_declared` — must pass unmodified (route path
    set unchanged; only `/api/tickets`'s `response_model` and query params
    change).
  - `test_main_mounts_no_static_files`,
    `test_agent_ops_dashboard_module_has_no_write_path`,
    `test_agent_ops_dashboard_does_not_import_workflow_orchestrator` —
    unaffected, must pass unmodified.
- `tests/tools/test_agent_ops_dashboard_concurrency.py`
  - `test_concurrent_requests_never_observe_partial_rebuild` — must pass
    unmodified (`cache.get_tickets()` primer call at L88 discards its
    return value).
  - `test_active_run_completion_flips_atomically_under_concurrent_reads` —
    unaffected (`/api/runs`/`get_run` path), must pass unmodified.
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`
  - `test_dashboard_frontend_never_references_simulation_api_surface` — must
    pass unmodified (glob/source guard, unrelated to shape changes).
- `tests/architecture/test_api_read_model_guard.py`
  - `test_no_api_route_directly_imports_authoritative_state` — must pass
    unmodified (this dashboard app already imports nothing from
    `AuthoritativeState`; adding `TicketsPage`/`TicketFacets` models does
    not change that).

**Frontend (unit, Vitest), must keep passing (several require
`mockFetchReturning`/call-site updates to the new envelope shape, not
behavior changes):**

- `dashboard-frontend/src/test/TicketsView.test.tsx` — every existing
  `describe` block (`'TicketsView — rendering'`, `'TicketsView — filter bar
  delegates to server query params'`, `'TicketsView — linked-runs control'`,
  `'TicketsView — null-safe rendering'`, `'TicketsView — anti-drift source
  guards'`) must keep passing. **All of them use `mockFetchReturning`, which
  must be updated (or wrapped) to resolve the new `{items, total_count,
  facets}` envelope shape instead of a bare array** — this is a required
  test-infrastructure change, not a behavior assertion change; the
  assertions themselves (rows render, filters send correct query params,
  linked-runs render, null-safe rendering, anti-drift guards) must be
  unaffected in intent.
  - `'TicketsView — index.css reset does not zero out padding utilities'`
    (added by the unrelated, already-done `TCK-20260717-CSS-LAYER-PADDING-FIX`)
    also uses `mockFetchReturning` and must keep passing under the same
    helper update — confirm it wasn't accidentally scoped out.
- Any other `dashboard-frontend/src/test/*.test.tsx` file that does not
  reference `TicketsView`/`fetchTickets` (e.g. `RecentActivityGantt.test.tsx`,
  `TimeAxis.test.tsx`) — unaffected, must pass unmodified.

## New Tests Required

Per AC #1 (backend `limit`/`offset` + slicing):

- **`test_get_tickets_slices_to_requested_page`** — unit — verifies
  `DashboardCache.get_tickets(limit=N, offset=M)` returns exactly the
  `[M:M+N]` slice of the filtered+sorted result against a fixture with more
  rows than the page size. Lives in `tests/tools/test_agent_ops_dashboard_ingest.py`.
- **`test_get_tickets_limit_offset_default_preserves_existing_behavior`** —
  unit — verifies `get_tickets()` called with no `limit`/`offset` (or
  explicit `limit=None`) returns the full, unsliced filtered set — the
  guard that the three existing AND/OR-filter tests keep passing without
  modification. Lives in `tests/tools/test_agent_ops_dashboard_ingest.py`.
- **`test_list_tickets_route_rejects_out_of_range_limit`** — integration —
  `GET /api/tickets?limit=0` and `?limit=501` (or whatever `le` bound is
  chosen) return `422`, mirroring `/api/runs`'s existing `ge=1, le=100`
  validation behavior. Lives in `tests/tools/test_agent_ops_dashboard_api.py`.
- **`test_list_tickets_route_passes_limit_offset_through_to_cache`** —
  integration — `GET /api/tickets?limit=1&offset=1` against a multi-row
  fixture returns exactly 1 item, matching the second row in sort order.
  Lives in `tests/tools/test_agent_ops_dashboard_api.py`.

Per AC #2 (frontend bounded fetch + bounded rendered rows):

- **`'renders only page-size ticket rows when the mocked corpus exceeds 1000
  rows'`** — unit (Testing Library) — mock `fetchTickets` to resolve an
  envelope whose `items` array has page-size length (e.g. 100) even though
  `total_count` is claimed as 1109+; assert `screen.getAllByTestId(/^ticket-row-/)`
  length equals the page size, never the claimed total. Lives in
  `dashboard-frontend/src/test/TicketsView.test.tsx`.
- **`'requests a bounded limit/offset (or page) param on initial load'`** —
  unit — assert the first `fetch` call's URL contains `limit=`/`offset=`
  (or the chosen param names) with the expected default values, mirroring
  the existing `'filter bar narrows rows...'` pattern of inspecting
  `mockFetch.mock.calls[...]`. Lives in `dashboard-frontend/src/test/TicketsView.test.tsx`.

Per AC #3 (facets independent of page window):

- **`test_facets_source_reflects_full_filtered_corpus_not_just_current_page`**
  — unit — a fixture with more distinct tier/layer/status/priority/tag
  values than fit on one page; call `get_tickets(limit=1, offset=0, ...)`
  and assert the returned `facets` (or equivalent structure) contains
  values only present in rows outside the returned page. Lives in
  `tests/tools/test_agent_ops_dashboard_ingest.py`.
- **`'filter dropdown options include values from tickets outside the
  currently-loaded page'`** — unit (Testing Library) — mock `fetchTickets`
  to resolve `items` (one page) plus a `facets` object containing a
  tier/layer/tag value absent from `items`; assert that value still appears
  as a `<option>`/tag-pill in the rendered filter bar. This is the specific
  regression guard for the `optionsSource`→`optionsFacets` anti-drift
  hazard flagged in investigation.md. Lives in
  `dashboard-frontend/src/test/TicketsView.test.tsx`.

Per AC #4 (column-sort page-scoped, never a silently-partial full-table
sort) — **page-scoped branch, per plan.md's Resolved Decision #2**:

- **Rewritten `'TicketsView — client-side column sort'`** (currently
  `'a tier column-header click re-orders rendered rows without triggering a
  new fetchTickets call'`, `TicketsView.test.tsx:188-217`) — must keep
  asserting no new `fetchTickets` call on a column-header click (unchanged
  intent) **and** additionally assert the new page-scoped-sort observable
  signal (e.g. `data-testid="column-sort-page-scoped-note"`) is present when
  `total_count > items.length` (more than one page) and absent otherwise.
  This rewrite is the deliberate anti-drift correction flagged in
  investigation.md — do not leave the old "no-fetch is fine, nothing else
  asserted" version in place unexamined. Lives in
  `dashboard-frontend/src/test/TicketsView.test.tsx`.
- **Optional but recommended**: an explicit new test asserting the
  page-scoped-sort note is absent when the mocked `total_count` equals
  `items.length` (single page — sort is trivially "full table" and no
  page-scoped caveat should render). Lives alongside the rewritten test
  above.

Architecture guard (per plan.md's Anti-Drift Notes — no route-count
regression):

- Confirm existing `test_all_five_routes_are_declared` is exercised as part
  of this ticket's regression run (no new test needed — it already guards
  against a 6th route being added for facets).

## Scoped Pytest Commands

Backend — do not run the full suite; scope to the dashboard's own test
files plus the one cross-cutting architecture guard:

```
python3 -m pytest \
  tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/architecture/test_api_read_model_guard.py \
  -m "not slow"
```

Frontend — scope to the dashboard SPA package, not a repo-wide test run:

```
cd dashboard-frontend && npm test
cd dashboard-frontend && npx tsc -b
```

## Anti-Drift Test Guards

- `test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
  `test_get_tickets_or_within_tag`,
  `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`
  passing **unmodified** is itself the anti-drift guard proving the
  cache-layer `limit: Optional[int] = None` default was not "aligned" to
  `get_runs`'s hardcoded default (a change that would silently truncate
  these tests' small fixtures to `get_runs`'s `50`-row default and mask
  itself as a coincidental pass on tiny fixtures — must be checked as an
  explicit `limit is None` behavior test, not inferred from fixture size).
- `'never re-implements a client-side .filter( pass over fetched ticket
  rows'` (`TicketsView.test.tsx:221-223`) must keep passing unmodified —
  guards against introducing a client-side `.slice(pageStart, pageEnd)`
  windowing pattern as a substitute for real server-side `limit`/`offset`
  (the exact substitution investigation.md's Anti-Drift Hazards section
  warns against). Note this specific guard only checks for `.filter(`, not
  `.slice(` — if the implementer is tempted to add client-side slicing, this
  existing regex will not catch it; treat `'requests a bounded limit/offset
  ... param on initial load'` (new test above) as the guard that actually
  proves the bound comes from the server, not client-side windowing of an
  unbounded fetch.
- `'never constructs a sort value other than date_asc/date_desc for a
  fetchTickets call'` (`TicketsView.test.tsx:230-236`) must keep passing
  **unmodified** — proves the chosen AC #4 branch (page-scoped, zero
  backend `sort` changes) was actually followed; a failure here would mean
  server-side sort support was added instead, which is explicit scope creep
  per plan.md's Anti-Drift Notes.
- A `git diff` check (not a pytest test, but a required verification step
  per plan.md's Step 6) confirming zero lines changed in
  `main.py::list_runs`, `ingest.py::get_runs`, `ingest.py::_build_run_summary`,
  `api.ts`'s `FetchRunsParams`/`fetchRuns`/`fetchAllRunsSince` — the
  Out-of-Scope guard for `/api/runs`.
- `docs/parity_ledger/infrastructure.yaml` diff check: `INFRA-275`'s two
  existing appended segments (in `v2_evidence` and `test_path`) must remain
  present verbatim after this ticket's parity update; only a new, third
  appended segment should appear as an addition.
