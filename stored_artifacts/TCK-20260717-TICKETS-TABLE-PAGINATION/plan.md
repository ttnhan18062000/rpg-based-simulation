---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TABLE-PAGINATION
artifact_type: plan
tags: [observability, agent-monitoring, performance]
---

# Implementation Plan — TCK-20260717-TICKETS-TABLE-PAGINATION

## Summary

Add server-side `limit`/`offset` pagination to `GET /api/tickets`, mirroring
`/api/runs`'s `Query(default=..., ge=1, le=...)` pattern but with a higher
ceiling (`le=500`) sized for the larger tickets corpus. Add a `total_count`
field to the response so the frontend never needs `/api/runs`'s offset-loop
workaround. Add a `facets` field to the same response, computed over the
filtered-but-unpaginated result before the `limit`/`offset` slice, so filter
dropdowns keep reflecting the full corpus regardless of which page is loaded.
Rewire `TicketsView.tsx` to request bounded pages, source `optionsSource`
from the new `facets` field instead of `rows`, and leave `sortRows`/
`toggleColumnSort` code untouched — it will automatically become a
page-scoped sort once `rows` is one page, which satisfies AC #4's
page-scoped branch, but the existing test asserting "no-fetch is acceptable"
must be rewritten to make that page-scoping an explicit, observable,
intentional behavior rather than an implicit side effect. Four resolved
decisions (total_count: yes; sort: page-scoped, zero-code-change branch;
facets: folded into existing response, not a new route; default
`limit=100, ge=1, le=500`/`offset=0, ge=0`) are stated explicitly below so
the implementer does not re-litigate them.

## Resolved Decisions (do not revisit)

1. **`total_count`**: add to the `GET /api/tickets` response envelope —
   the count of the filtered-but-unpaginated result, computed inside
   `get_tickets` before slicing. Closes the gap `/api/runs` has; do not
   port `/api/runs`'s no-total-count workaround.
2. **Column-sort under pagination**: **page-scoped sort branch** of AC #4.
   `sortRows`/`toggleColumnSort`/`columnSort` in `TicketsView.tsx` are left
   as-is — zero code changes to the sort logic itself. Once `rows` is one
   page, the existing `[...rows].sort(...)` naturally becomes a sort over
   the current page only. This is intentional and must be made
   **observable** (a `data-testid`/label indicating page-scoped sort) per
   AC #4's "never silently" wording — see Step 4.
3. **Facets source shape**: fold into the existing `GET /api/tickets`
   response, not a new sibling route. Response envelope becomes:
   ```json
   {
     "items": [...TicketSummary],
     "total_count": <int>,
     "facets": {
       "tiers": [...string],
       "layers": [...string],
       "statuses": [...string],
       "priorities": [...string],
       "tags": [...string]
     }
   }
   ```
   All four `facets` arrays are `sorted(set(...))` over the
   filtered-but-unpaginated result, computed before the `limit`/`offset`
   slice. This avoids adding a 6th route (would trip
   `test_all_five_routes_are_declared` unnecessarily) and is cheap since
   it reuses the same filtered-set computation already in `get_tickets`.
4. **Default limit/offset**: route-level
   `limit: int = Query(default=100, ge=1, le=500)`,
   `offset: int = Query(default=0, ge=0)` on `main.py::list_tickets`.
   At the `ingest.py::get_tickets` cache-layer function, keep
   `limit: Optional[int] = None, offset: int = 0` (unlike `get_runs`'s
   hardcoded `limit: int = 50`) — when `limit is None`, return the full
   filtered+sorted set unsliced. This preserves the three existing
   `get_tickets(...)`-direct-call tests
   (`test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
   `test_get_tickets_or_within_tag`,
   `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`)
   with zero modification, since they call `get_tickets` without
   `limit`/`offset` today and expect the full 4-5 row fixture back.

## Steps

### Step 1 — Backend: `models.py` response envelope

**Files:** `src/api/agent_ops_dashboard/models.py`

**Change:** Add a new Pydantic model `TicketFacets` with fields
`tiers: List[str]`, `layers: List[str]`, `statuses: List[str]`,
`priorities: List[str]`, `tags: List[str]`. Add a new Pydantic model
`TicketsPage` with fields `items: List[TicketSummary]`,
`total_count: int`, `facets: TicketFacets`. Do not modify `TicketSummary`
itself — it is reused unchanged as the `items` element type.

**Do NOT touch:** `RunSummary` or any `/api/runs`-related model. Do not
add a `total_count`/`facets` field to any run-related model — Out of
Scope explicitly excludes touching `/api/runs`'s own gap.

**Verify:** `test_typed_response_models_not_dict`
(`tests/tools/test_agent_ops_dashboard_api_boundary.py`) — confirms the
new models are real Pydantic `BaseModel` subclasses, never raw `dict`.

---

### Step 2 — Backend: `ingest.py::get_tickets` slicing + total_count + facets

**Files:** `src/api/agent_ops_dashboard/ingest.py` (`DashboardCache.get_tickets`, `~L450-487`)

**Change:**
- Add parameters `limit: Optional[int] = None, offset: int = 0` to
  `get_tickets`'s signature (after existing `tier`/`layer`/`status`/
  `priority`/`tag`/`lifecycle`/`q`/`sort` params).
- After the existing filter + sort logic produces `filtered` (the
  filtered+sorted list, currently returned directly), compute:
  - `total_count = len(filtered)`
  - `facets` dict: `sorted({r["tier"] for r in filtered if r.get("tier")})`,
    same pattern for `layer`→layers, `status`(workflow_status)→statuses,
    `priority`→priorities, and the union of all tags across `filtered`→tags
    (reuse whatever tag-extraction helper the existing OR-within-tag filter
    logic already uses, to stay consistent with how tags are read off each
    ticket record).
  - Both `total_count` and `facets` are computed over `filtered` **before**
    slicing — this is what keeps facets independent of the page window.
- Then apply the slice: `if limit is not None: paged = filtered[offset:offset+limit] else: paged = filtered`.
- Change the return type/shape: instead of returning
  `[_ticket_record_to_summary(r) for r in filtered]`, return a structure
  carrying `items=[_ticket_record_to_summary(r) for r in paged]`,
  `total_count`, and `facets` — the exact shape the route (Step 3) will
  wrap into `TicketsPage`. (Implementer's choice whether `get_tickets`
  itself returns a `TicketsPage`-shaped dict/namedtuple or the route
  assembles `TicketsPage` from three separate return values — pick
  whichever keeps `get_tickets`'s existing direct-call test callsites
  working with minimal signature disruption; do not change what
  `_ticket_record_to_summary` does.)

**Do NOT touch:** `get_runs`, `_build_run_summary`, or any `/api/runs`
code path in this file. Do not change the filter logic itself (tier/
layer/status/priority AND, tag OR-within-tag) — only add slicing +
total_count + facets computation around the existing `filtered` list.
Do not change `_ticket_record_to_summary`.

**Verify:**
- `test_get_tickets_slices_to_requested_page`
- `test_get_tickets_limit_offset_default_preserves_existing_behavior`
- `test_get_tickets_and_across_dimensions_filters_tier_and_layer`,
  `test_get_tickets_or_within_tag`,
  `test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`
  (must pass unmodified — proves the `limit=None` default preserves
  existing full-set-return behavior)
- `test_facets_source_reflects_full_filtered_corpus_not_just_current_page`

---

### Step 3 — Backend: `main.py::list_tickets` route params + response_model

**Files:** `src/api/agent_ops_dashboard/main.py` (`list_tickets`, `~L29-49`)

**Change:**
- Add `limit: int = Query(default=100, ge=1, le=500)`,
  `offset: int = Query(default=0, ge=0)` to `list_tickets`'s signature,
  positioned consistently with how `/api/runs`'s `list_runs` declares its
  equivalents.
- Change the route's `response_model` from `List[TicketSummary]` to
  `TicketsPage` (imported from `models.py`, Step 1).
- Pass `limit=limit, offset=offset` through to `_cache.get_tickets(...)`.
- Assemble the `TicketsPage` return value from whatever shape Step 2's
  `get_tickets` returns (`items`, `total_count`, `facets`).

**Do NOT touch:** `list_runs` or any of its `Query(...)` declarations —
copy the *pattern* (ge/le-bounded `Query`), never edit the sibling route
itself. Do not change any of the other four existing routes.

**Verify:**
- `test_list_tickets_route_rejects_out_of_range_limit`
- `test_list_tickets_route_passes_limit_offset_through_to_cache`
- `test_all_five_routes_are_declared` (must still pass unmodified — no
  route count change, only a response_model + query-param change on an
  existing route)
- `test_get_tickets_title_is_distinct_from_ticket_id` (existing test —
  the required `.items` read-adjustment is made explicit in Step 5b
  below; do not consider Step 3 complete until Step 5b's edit has also
  landed, since this test will otherwise fail against the new envelope)

---

### Step 4 — Frontend: `api.ts` — `FetchTicketsParams`, `fetchTickets`, response typing

**Files:** `dashboard-frontend/src/api.ts`

**Change:**
- Add `limit?: number` and `offset?: number` to `FetchTicketsParams`
  (`~L96-105`).
- In `fetchTickets()` (`~L107-123`), append `limit`/`offset` to the
  `URLSearchParams` when provided, mirroring how `fetchRuns` builds its
  own bounded params.
- Add response types matching the new backend envelope: a `TicketsFacets`
  type (`tiers`, `layers`, `statuses`, `priorities`, `tags`: `string[]`)
  and update `fetchTickets`'s return type from
  `Promise<TicketSummary[]>` to a `TicketsPage`-shaped
  `Promise<{ items: TicketSummary[]; totalCount: number; facets: TicketsFacets }>`
  (or equivalent naming already used elsewhere in the file — match
  existing camelCase/snake_case conventions in `api.ts`, converting the
  wire `total_count`/backend field names to whatever this file's
  established convention is).

**Do NOT touch:** `FetchRunsParams`, `fetchRuns()`, `fetchAllRunsSince()`
— these implement `/api/runs`'s own gap-workaround and are explicitly
Out of Scope.

**Verify:** `test_dashboard_frontend_never_references_simulation_api_surface`
(existing glob guard, automatic); `npx tsc -b` (type-check the new
return-type shape doesn't break other `api.ts` consumers — confirmed
Step-4-only consumer is `TicketsView.tsx`, Step 5).

---

### Step 5 — Frontend: `TicketsView.tsx` — bounded fetch, facets-sourced options, observable page-scoped sort

**Files:** `dashboard-frontend/src/views/TicketsView.tsx`

**Change:**
- `loadInitial()` (`~L128-150`): change `fetchTickets({})` to
  `fetchTickets({ limit: PAGE_SIZE, offset: 0 })` where `PAGE_SIZE` is a
  new module-level constant (e.g. `100`, matching the backend default).
  Store the response's `items` into `rows` (not the raw array) and store
  `facets` into a **new**, separate state variable (e.g. `optionsFacets`)
  — do NOT continue assigning `optionsSource = result` from the paginated
  fetch.
- `applyFilters()` (`~L152-161`) and `toggleDateSort()` (`~L163-173`):
  thread `limit`/`offset` (reset `offset` to `0` on filter/sort change,
  since these replace the current view rather than paginate it) through
  `buildFetchParams(...)` the same way. Each of these already re-fetches
  on every change; the fetched response's `facets` field must also
  update `optionsFacets` each time (facets are always full-corpus-for-the-
  current-filters, not full-unfiltered-corpus — this matches AC #3's
  "reflect the full corpus" as measured against the current filter set,
  not an unfiltered global set, consistent with how `get_tickets`
  computes facets over `filtered` post-filter, pre-slice in Step 2).
- `distinctValues`/`distinctTags` (`~L28-43`): re-point their input from
  `optionsSource` to the new `optionsFacets` state (already-distinct
  arrays from the backend, so these functions may simplify to direct
  reads rather than re-deriving distinctness client-side — implementer's
  call whether to simplify or keep the functions as a passthrough, but
  the **input source** must change from `rows`/`optionsSource`-as-rows to
  `optionsFacets`).
- `toggleColumnSort()`/`sortRows()`/`columnSort` (`~L21-24`, `L57-67`,
  `L175-182`) and `displayedRows` (`~L189-192`): **leave the sort logic
  itself unchanged.** It will now naturally operate over `rows` (one
  page) instead of the full corpus — this is the chosen AC #4 branch.
  Add one small, explicit, observable signal that sort is page-scoped:
  a `data-testid="column-sort-page-scoped-note"` element (or a visually
  subtle label near the table, e.g. "Sorting current page only") rendered
  whenever `columnSort` is active and `total_count > rows.length` (i.e.
  there is more than one page). This is the only new UI element this
  step adds — do not build pagination controls (next/prev page buttons)
  unless the ticket's AC requires them (it does not; AC #2 only requires
  bounded fetch + bounded rendered rows, not a page-navigation UI).
- **`dashboard-frontend/src/test/TicketsView.test.tsx`'s shared
  `mockFetchReturning` helper (`L29-33`) must be updated in this same
  step, as part of the same commit as the `api.ts`/`TicketsView.tsx`
  changes above — not deferred as follow-up cleanup.** Today it mocks
  `fetch` to resolve a bare `TicketSummary[]`:
  ```ts
  function mockFetchReturning(response: TicketSummary[]) {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => response })
    globalThis.fetch = mockFetch as unknown as typeof fetch
    return mockFetch
  }
  ```
  Once `fetchTickets`'s return type becomes the `TicketsPage` envelope
  (Step 4), every existing call site of the form
  `mockFetchReturning([makeTicket(...), ...])` resolves the wrong wire
  shape and every one of the ~9 existing `it(...)` blocks across all
  five pre-existing `describe` blocks in this file (`'TicketsView —
  rendering'`, `'TicketsView — filter bar delegates to server query
  params'`, `'TicketsView — linked-runs control'`, `'TicketsView —
  null-safe rendering'`, `'TicketsView — anti-drift source guards'`,
  plus the already-done sibling's `'TicketsView — index.css reset does
  not zero out padding utilities'` block) breaks simultaneously — not
  just the column-sort test this plan already calls out for rewriting.
  Fix by changing `mockFetchReturning`'s signature to accept (or wrap)
  the envelope shape, e.g.:
  ```ts
  function mockFetchReturning(
    items: TicketSummary[],
    envelopeOverrides: Partial<{ total_count: number; facets: TicketsFacets }> = {},
  ) {
    const body = {
      items,
      total_count: envelopeOverrides.total_count ?? items.length,
      facets: envelopeOverrides.facets ?? emptyFacets(),
    }
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => body })
    globalThis.fetch = mockFetch as unknown as typeof fetch
    return mockFetch
  }
  ```
  (exact parameter shape/defaults are the implementer's call — the
  binding requirement is that every existing call site
  `mockFetchReturning([...])` keeps compiling and passing with its
  existing single-array argument, defaulting `total_count`/`facets` to
  sane single-page values, so none of the ~9 pre-existing tests need
  their own call sites edited beyond what the helper itself absorbs).
  Only the tests that specifically need non-default `total_count`/
  `facets` values (the new facets-independence test and the rewritten
  column-sort test) pass the optional second argument.

**Do NOT touch:** Any `.filter(` client-side row filtering (already
guarded by an existing test) — do not introduce a `.slice(pageStart,
pageEnd)` client-side windowing pattern; the bounding must come from the
server via `limit`/`offset` in the fetch, not client-side slicing of an
unbounded fetch. Do not rewrite the ~9 pre-existing tests' own bodies to
work around a still-bare-array `mockFetchReturning` — fix the helper
once, not each call site individually.

**Verify:**
- `'renders only page-size ticket rows when the mocked corpus exceeds
  1000 rows'`
- `'requests a bounded limit/offset (or page) param on initial load'`
- `'filter dropdown options include values from tickets outside the
  currently-loaded page'`
- Rewritten version of `'TicketsView — client-side column sort'`
  (`~L188-217`): must now assert (a) no new `fetchTickets` call on a
  column-header click (unchanged from today), AND (b) the new
  page-scoped-sort observable signal is present when there is more than
  one page — this is the deliberate rewrite anti-drift hazard flagged in
  investigation.md; the old assertion of "no-fetch is fine" must not
  survive unexamined, it must be paired with the new observability
  assertion.
- `'TicketsView — anti-drift source guards'` (`~L220-237`): existing
  `.filter(` guard and `matching_runs`-sort guard must keep passing
  unmodified. `'never constructs a sort value other than date_asc/
  date_desc for a fetchTickets call'` (`L230-236`) must also keep passing
  unmodified, since this plan's chosen branch (page-scoped sort) adds no
  new `sort` query values — this guard needs **no** update under this
  plan (only the server-side-sort branch would have required updating
  it; confirm this explicitly during Step 5 verification since
  test_plan.md flagged it as conditionally needing a rewrite).
- All five pre-existing `describe` blocks in `TicketsView.test.tsx`
  (`'TicketsView — rendering'`, `'TicketsView — filter bar delegates to
  server query params'`, `'TicketsView — linked-runs control'`,
  `'TicketsView — null-safe rendering'`, `'TicketsView — anti-drift
  source guards'`) plus the CSS-layer-padding-fix sibling's `'TicketsView
  — index.css reset does not zero out padding utilities'` block must all
  keep passing after the `mockFetchReturning` update — this is the
  direct proof that the helper fix didn't just move the breakage from
  "everything fails" to "everything silently returns wrong data and
  still passes for the wrong reason."

---

### Step 5b — Backend test: `test_agent_ops_dashboard_api.py`'s one direct-list-index test needs the `.items` unwrap

**Files:** `tests/tools/test_agent_ops_dashboard_api.py` (`test_get_tickets_title_is_distinct_from_ticket_id`, `L77-98`)

**Change:** This test currently does:
```python
resp = client.get("/api/tickets")
assert resp.status_code == 200
tickets = resp.json()
ticket = next(t for t in tickets if t["ticket_id"] == "TCK-20260101-TITLED")
```
`tickets = resp.json()` indexes the top-level response as a list directly.
Under the new `TicketsPage` envelope (Step 3), the top level is now a dict
with `items`/`total_count`/`facets` keys, so this line must become:
```python
tickets = resp.json()["items"]
```
This is a one-line read-adjustment to accommodate the new envelope shape —
no change to the test's assertions (`ticket["title"] == "..."`,
`ticket["title"] != ticket["ticket_id"]`) or its intent. This is already
listed in Step 3's verify bullets as a test to confirm still passes; this
step makes the required edit explicit so it is not skipped as "someone
else's test."

**Do NOT touch:** Any other test in this file — the other three tests
(`test_run_detail_404_for_unknown_run_id`,
`test_run_timeline_404_for_unknown_run_id`,
`test_run_detail_200_for_known_run_id`) exercise `/api/runs` routes,
untouched by this ticket, and must pass unmodified.

**Verify:** `test_get_tickets_title_is_distinct_from_ticket_id` passes
against the new envelope shape.

---

### Step 6 — Full regression pass + parity ledger update

**Files:** `docs/parity_ledger/infrastructure.yaml` (INFRA-275 entry, `~L4478-4544`)

**Change:**
- Run the full scoped backend command from `test_plan.md`:
  ```
  python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
    tests/tools/test_agent_ops_dashboard_api.py \
    tests/tools/test_agent_ops_dashboard_api_boundary.py \
    tests/tools/test_agent_ops_dashboard_concurrency.py \
    tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
    tests/architecture/test_api_read_model_guard.py \
    -m "not slow"
  ```
- Run frontend: `cd dashboard-frontend && npm test` and
  `cd dashboard-frontend && npx tsc -b`.
- Update INFRA-275's `v2_evidence` by **appending** a third
  paragraph (after the original backend-shape paragraph and the
  title-fix paragraph already appended by
  `TCK-20260717-TICKET-TITLE-PARSE-FIX`) describing: `GET /api/tickets`
  now accepts `limit`/`offset`, returns a `TicketsPage` envelope
  (`items`/`total_count`/`facets`) instead of a bare list, and
  `get_tickets` slices to the requested page while facets/total_count are
  computed over the full filtered-but-unpaginated result. Append the new
  pagination test names to `test_path` (do not replace the existing
  list). Do not touch any other field on the entry (`status` stays
  `verified`, `priority` stays `P2`).
- Confirm via `git diff` that zero lines changed in
  `main.py::list_runs`/`ingest.py::get_runs`/`_build_run_summary` (the
  Out-of-Scope guard for `/api/runs`).

**Do NOT touch:** INFRA-276 (serve.py/Makefile — unaffected, confirmed in
investigation.md). Do not overwrite or delete either of INFRA-275's two
existing appended paragraphs/test_path segments.

**Verify:** All commands above pass; `git diff docs/parity_ledger/infrastructure.yaml` shows only an append (no removed lines within the INFRA-275 entry other than possibly a trailing-newline adjustment).

## Scope Guards

- Do not add a `total_count` field to `GET /api/runs` or otherwise modify
  `/api/runs`'s pagination/gap — Out of Scope, explicit in the ticket.
- Do not edit `main.py::list_runs`, `ingest.py::get_runs`,
  `ingest.py::_build_run_summary`, or `api.ts`'s `FetchRunsParams`/
  `fetchRuns`/`fetchAllRunsSince` in any step of this plan.
- Do not add a new route (e.g. `GET /api/tickets/facets`) — facets are
  folded into the existing `GET /api/tickets` response per Resolved
  Decision 3. Adding a 6th route would gratuitously trip
  `test_all_five_routes_are_declared` and is explicitly not the chosen
  design.
- Do not build pagination navigation UI (next/prev buttons, page number
  controls) — not required by any AC; AC #2 only requires bounded fetch
  + bounded rendered row count.
- Do not modify `_ticket_record_to_summary`, the tier/layer/status/
  priority AND-filter logic, or the tag OR-within-tag filter logic in
  `ingest.py::get_tickets` — only add slicing/total_count/facets around
  the existing `filtered` list.
- Do not overwrite or delete either of INFRA-275's two existing appended
  `v2_evidence`/`test_path` segments — append only.
- Do not touch `parse_ticket_file`/`parse_body_section` (title-parsing
  logic from the sibling hotfix ticket) — confirmed no functional overlap
  with this ticket's changes.
- Do not introduce client-side `.slice(pageStart, pageEnd)` windowing of
  an unbounded fetch as a substitute for real server-side `limit`/
  `offset` — the existing `.filter(` guard would not catch this, but it
  violates this ticket's intent.

## Dependency Map

- Step 1 (models.py) has no dependencies — pure additive schema step.
- Step 2 (ingest.py) depends on Step 1 only if `get_tickets` is typed to
  return `TicketsPage`/`TicketFacets` directly; if it returns a plain
  dict/tuple instead (implementer's choice per Step 2), Step 2 can be
  implemented and tested independently of Step 1.
- Step 3 (main.py) depends on both Step 1 (imports `TicketsPage`) and
  Step 2 (calls the new `get_tickets` signature).
- Step 4 (api.ts) depends on Step 3 being complete (mirrors the actual
  wire shape) but can be developed in parallel against a mocked response
  shape and verified against the real backend afterward.
- Step 5 (TicketsView.tsx, including the `mockFetchReturning` helper
  update) depends on Step 4 (`fetchTickets`'s new return shape and
  params).
- Step 5b (`test_agent_ops_dashboard_api.py`'s `.items` unwrap) depends
  on Step 3 only (it exercises the real backend envelope shape via
  `client.get("/api/tickets")`, not `fetchTickets`) — it has no
  dependency on Steps 4/5 and can land any time after Step 3.
- Step 6 (regression + parity) depends on all of Steps 1-5, 5b being
  complete; it is the final verification and documentation step.
- Steps 1→2→3 are backend-sequential. Step 4→5 are frontend-sequential.
  Backend (1-3) and frontend (4-5) have no code dependency on each
  other's internals beyond the wire contract, so they may be implemented
  in either order, but frontend Step 4/5 tests that assert on real
  response shapes should run after Step 3 lands. Step 5b is a small,
  independent backend-test fix that can land alongside Step 3 or any
  time before Step 6's full regression pass.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `GET /api/tickets` accepts `limit`/`offset`; `get_tickets()` slices the filtered+sorted result | Steps 2, 3, 5b (envelope-shape test accommodation) | `test_get_tickets_slices_to_requested_page`, `test_get_tickets_limit_offset_default_preserves_existing_behavior`, `test_list_tickets_route_rejects_out_of_range_limit`, `test_list_tickets_route_passes_limit_offset_through_to_cache`, `test_get_tickets_title_is_distinct_from_ticket_id` |
| AC #2 — `TicketsView.tsx` requests bounded pages; rendered row count stays bounded regardless of total ticket count | Steps 4, 5 (incl. `mockFetchReturning` envelope update) | `'renders only page-size ticket rows when the mocked corpus exceeds 1000 rows'`, `'requests a bounded limit/offset (or page) param on initial load'` |
| AC #3 — filter-dropdown options continue reflecting the full corpus (via a dedicated facets source), not silently truncated to page-1 values | Steps 2, 3, 4, 5 | `test_facets_source_reflects_full_filtered_corpus_not_just_current_page`, `'filter dropdown options include values from tickets outside the currently-loaded page'` |
| AC #4 — client-side column-sort is either server-side or explicitly scoped to the current page, never a silent partial-corpus sort | Step 5 (page-scoped branch chosen; zero change to sort logic itself, only the observable-signal addition) | Rewritten `'TicketsView — client-side column sort'` test asserting no-new-fetch AND the page-scoped observable signal; `'never constructs a sort value other than date_asc/date_desc for a fetchTickets call'` (unmodified — no new sort param added under this branch) |

## Anti-Drift Notes

- **`optionsSource`/`optionsFacets` separation is the single highest-risk
  point in this plan.** It is a one-line mistake to leave
  `setOptionsFacets` unused and keep deriving `distinctValues`/
  `distinctTags` from `rows`/the paginated fetch result — this is the
  exact silent-narrowing failure AC #3 forbids. The new frontend test
  mocking facets values absent from the mocked first page is the only
  guard that catches this; it must pass, not just exist.
- **The page-scoped sort branch was chosen specifically because it
  requires zero changes to `sortRows`/`toggleColumnSort`/`columnSort`.**
  Do not be tempted to also add server-side sort support "while in
  there" — that would be scope creep beyond this ticket's chosen branch
  and would require backend `sort` param changes not covered by this
  plan. The only frontend change tied to AC #4 is the new observable
  page-scoped-sort signal.
- **`get_tickets`'s `limit: Optional[int] = None` default at the cache
  layer is deliberate and different from `get_runs`'s hardcoded
  `limit: int = 50`.** Do not "align" `get_tickets` to match `get_runs`'s
  hardcoded default — doing so would break the three existing
  AND/OR-filter tests that call `get_tickets(...)` directly with no
  `limit`/`offset` and expect the full fixture set back.
- **Facets are computed over the filtered set, not the unfiltered global
  set.** When a tier/layer/status/priority/tag filter is already active,
  `facets` reflects what's available *given the current filters* (matches
  how `get_tickets` computes `total_count`/`facets` from `filtered`, after
  the AND/OR filter logic but before the `limit`/`offset` slice). This is
  the correct interpretation of AC #3 — "reflect the full corpus" means
  "not narrowed further by pagination," not "ignore active filters."
- **INFRA-275 already carries two appended paragraphs.** The Step 6 parity
  update must append a third, distinguishable paragraph — read the full
  existing entry before editing to confirm exact insertion point and
  avoid any accidental line deletion.
- **Response envelope shape change (`List[TicketSummary]` →
  `TicketsPage`) is a breaking change to `GET /api/tickets`'s wire
  contract.** Confirmed in investigation.md that `TicketsView.tsx` is the
  only frontend consumer and `main.py::list_tickets` is the only backend
  caller of `get_tickets` — so this break is fully contained to Steps
  3-5, 5b of this plan and requires no additional consumer updates
  elsewhere in the repo. Still, grep for any other `fetchTickets`/
  `/api/tickets` reference before considering Step 5 complete, as a final
  sanity check beyond what investigation.md already confirmed.
- **`mockFetchReturning` (`TicketsView.test.tsx:29-33`) is a single
  point of breakage for ~9 pre-existing tests, not a detail scoped to
  the column-sort rewrite.** It mocks `fetch` to resolve a bare
  `TicketSummary[]` today. The moment `fetchTickets`'s return type
  becomes the `TicketsPage` envelope (Step 4), every existing call site
  `mockFetchReturning([...])` across all five pre-existing `describe`
  blocks (plus the CSS-layer-padding-fix sibling's block) breaks
  simultaneously unless the helper itself is updated in Step 5, in the
  same commit as the `api.ts`/`TicketsView.tsx` changes. Do not treat
  this as a mechanical "fix each failing test individually" cleanup
  pass — fix the shared helper once so the ~9 pre-existing call sites
  need no changes of their own.
- **`tests/tools/test_agent_ops_dashboard_api.py::test_get_tickets_title_is_distinct_from_ticket_id`
  (Step 5b) does `tickets = resp.json()` and iterates it as a list
  directly today.** Under the new envelope this must become
  `tickets = resp.json()["items"]`. This is a distinct fix from the
  frontend `mockFetchReturning` fix above — different language, different
  file, different test runner — do not assume fixing one covers the
  other.

## Deviations

- **`dashboard-frontend/src/test/App.test.tsx`'s `mockTicketsFetch` helper**
  was not named anywhere in this plan or in `investigation.md`.
  Investigation's claim that "`TicketsView.tsx` is the only frontend
  consumer... so this break is fully contained to Steps 3-5, 5b" was correct
  about *production* code but did not audit test-only fetch mocks outside
  `TicketsView.test.tsx`. `App.test.tsx` mounts the real `TicketsView` and
  mocks `globalThis.fetch` itself (independent of `mockFetchReturning`) with
  the same bare-`TicketSummary[]` assumption. Running the frontend suite
  after Steps 4-5 landed surfaced 2 failing tests in `App.test.tsx` with
  `TypeError: Cannot read properties of undefined (reading 'tiers')` —
  `optionsFacets` was `undefined` because the mock's `json()` resolved a
  bare array instead of the `{items, total_count, facets}` envelope. Fixed
  by updating `mockTicketsFetch` (in `App.test.tsx`) to wrap its `items`
  argument in the same envelope shape, mirroring the `mockFetchReturning`
  fix this plan already specified for `TicketsView.test.tsx`. No assertion
  in `App.test.tsx` changed — only the fetch-mock's wire shape, matching
  the fix's own no-behavior-change intent for `mockFetchReturning`.
