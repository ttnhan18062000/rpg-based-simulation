---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TAG-SEARCH
artifact_type: test_plan
tags: [observability, performance]
---

# Test Plan — TCK-20260717-TICKETS-TAG-SEARCH

## Regression Surface

All frontend — this ticket touches no backend/Python code (Out of Scope).

**`dashboard-frontend/src/test/TicketsView.test.tsx`** (unit/component,
current post-pagination state — 49 total assertions across these describe
blocks per the pagination ticket's Test Summary):

- `'TicketsView — rendering'` — 1 test, renders rows across lifecycle
  states. Unaffected by tag-control changes; must keep passing unmodified.
- `'TicketsView — filter bar delegates to server query params'` — 2 tests
  (`L98-122`, `L124-144`). **These directly call
  `screen.getByTestId('filter-tag-observability')` /
  `'filter-tag-infra'` with no prior "open the control" step.** This is the
  single highest-risk regression point — see Anti-Drift Test Guards below.
  Must keep passing, possibly requiring an in-scope update to add an
  "open the tag control" interaction step first, depending on which
  collapsed-by-default design is chosen (see investigation.md Risk #1).
- `'TicketsView — linked-runs control'` — 2 tests. Unaffected, must pass
  unmodified.
- `'TicketsView — null-safe rendering'` — 1 test. Unaffected, must pass
  unmodified.
- `'TicketsView — client-side column sort'` — 2 tests. Unaffected (tag
  control does not touch `columnSort`/`sortRows`), must pass unmodified.
- `'TicketsView — pagination'` — 2 tests. Unaffected, must pass unmodified.
- `'TicketsView — facets independent of page window'` — 1 test
  (`L303-323`), asserts `screen.getByTestId('filter-tag-offpage-tag')` is
  present after mocking a facets payload with a tag absent from the loaded
  page. **This test's assumption (the tag button is directly queryable
  without opening any control) has the same fork-dependency as the two
  filter-bar tests above** — must keep passing under whichever
  collapsed-by-default design is chosen, updated in-scope if needed.
- `'TicketsView — anti-drift source guards'` — 3 tests (`L327-343`),
  including the load-bearing `.filter(` guard
  (`expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.filter\(/)`, `L327-329`)
  that this ticket's AC #4 explicitly requires to keep passing. Must pass
  unmodified — the new tag-search-narrowing logic must not introduce any
  `Array.prototype.filter(` call anywhere in `TicketsView.tsx`.
- `'TicketsView — index.css reset does not zero out padding utilities'` —
  2 tests (CSS-layer-padding-fix sibling's block). Unaffected, must pass
  unmodified.

**`dashboard-frontend/src/test/App.test.tsx`** — mounts the real
`TicketsView` via its own independent `mockTicketsFetch` helper (the
pagination ticket's documented deviation). Not named in this ticket's
Related Code Areas but is a real consumer of `TicketsView` — must be
re-run to confirm no incidental breakage from the tag-control change
(e.g. if `mockTicketsFetch`'s fixture happens to render/select a tag).

**Backend** (no changes expected, run as a sanity check only since
`facets.tags` is the data contract this ticket's UI consumes):
- `tests/tools/test_agent_ops_dashboard_ingest.py::test_facets_source_reflects_full_filtered_corpus_not_just_current_page`
- `tests/tools/test_agent_ops_dashboard_ingest.py::test_get_tickets_or_within_tag`
- `tests/tools/test_agent_ops_dashboard_ingest.py::test_get_tickets_dimension_filter_and_tag_filter_combine_with_and`

**Type/build gates:**
- `cd dashboard-frontend && npx tsc -b`
- `cd dashboard-frontend && npm run build`

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260717-TICKETS-TAG-SEARCH.md`):

1. **Test name:** `typing a substring into the tag search narrows the rendered tag options case-insensitively without a new fetchTickets call`
   - **Category:** unit/component
   - **Verifies:** AC #1 — narrows `optionsFacets.tags` rendering to
     case-insensitive substring matches; `mockFetch.mock.calls.length`
     unchanged before/after typing; ticket table rows (`rows`/`displayedRows`)
     unchanged.
   - **Location:** `dashboard-frontend/src/test/TicketsView.test.tsx`, new
     `describe('TicketsView — tag search/collapse')` block.

2. **Test name:** `the tag selector does not render all ~1,309 facets.tags option buttons simultaneously on initial load`
   - **Category:** unit/component (anti-drift / performance guard)
   - **Verifies:** AC #2 — mock a large `facets.tags` array (e.g. 1500
     synthetic tag strings) and assert the number of rendered
     `[data-testid^="filter-tag-"]` elements stays under a small bound
     (e.g. < 50) on initial render, before any search/expand interaction.
     This is the direct regression guard for the reported >1.2MB-DOM /
     below-the-fold bug.
   - **Location:** same file, same new describe block.

3. **Test name:** `selecting a tag through the new control still sends exactly one repeated tag= query param per selection`
   - **Category:** unit/component
   - **Verifies:** AC #3 — the OR-within-tag / one-param-per-selection
     contract survives whatever new interaction is required to reach a tag
     button (open control, optionally search, then click). Reuses the same
     assertion style as the existing `L98-122`/`L124-144` tests but through
     the new control's interaction path.
   - **Location:** same file — either a new test, or an in-place update to
     the two existing filter-bar tests (`L98-122`, `L124-144`) if the
     chosen design requires opening the control first (see Risk #1 in
     investigation.md — resolve before writing this test).

4. **Test name:** `TICKETS_VIEW_SOURCE never contains an Array.prototype.filter( call` (already exists — confirm, do not duplicate)
   - **Category:** architecture guard (anti-drift)
   - **Verifies:** AC #4. This test already exists
     (`TicketsView.test.tsx:327-329`) and requires no new test — only
     confirmation that the implementation doesn't violate it. Listed here
     as a required-passing gate, not a new test to write.

5. **Test name:** `an off-page facets tag remains reachable through the tag search after narrowing`
   - **Category:** unit/component (anti-drift for the facets-source finding)
   - **Verifies:** that the new search/collapse UI reads from
     `optionsFacets.tags` (server-computed, full-filtered-corpus) and not a
     client-side re-derivation from `rows`/the current page. Mock a page of
     1 ticket plus a `facets.tags` array containing a tag absent from that
     ticket, type a substring matching only that off-page tag into the
     search box, and assert its `filter-tag-*` button becomes reachable.
     This directly guards against the highest-severity Anti-Drift Hazard
     identified in investigation.md (resurrecting client-side tag
     derivation from `rows`).
   - **Location:** same file, same new describe block.

6. **Test name:** `clearing the tag search restores the full (bounded) option list` (optional but recommended)
   - **Category:** unit/component
   - **Verifies:** search-box state is client-local and reversible — not
     required by any AC verbatim but a natural corollary of AC #1's
     "narrows... without changing the ticket table contents"; include if
     the chosen design has an explicit clear affordance.
   - **Location:** same file, same new describe block.

## Scoped Pytest Commands

This ticket is frontend-only; no new/changed Python behavior. Run as a
regression sanity check only (confirms the facets contract this UI depends
on is unchanged):

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  -m "not slow"
```

Never: `pytest tests/`.

Frontend (primary verification surface for this ticket):

```
cd dashboard-frontend && npm test -- --run
cd dashboard-frontend && npx tsc -b
cd dashboard-frontend && npm run build
```

## Anti-Drift Test Guards

- **`.filter(` source guard** (`TicketsView.test.tsx:327-329`) — must pass
  unmodified. This is the mechanical enforcement of AC #4 and the single
  most likely accidental violation, since the natural implementation of
  "narrow options by substring" is `array.filter(predicate)`. Any
  implementation must use `.reduce()`, a manual loop, or an equivalent
  non-`.filter()` idiom (matching the existing `removeTag()` pattern at
  `TicketsView.tsx:67-72`).
- **Facets-source guard (new test #5 above)** — catches silent
  reintroduction of client-side tag derivation from `rows` instead of
  `optionsFacets.tags`. Without this test, a regression here would not be
  caught by any existing test (all pre-existing fixtures use page-size ==
  corpus-size, where `rows`-derived and `facets`-derived tag lists are
  indistinguishable).
- **Bounded-render guard (new test #2 above)** — catches silent
  reintroduction of the original bug (all facets.tags rendered
  simultaneously) even if a search box is added but the "collapsed"
  requirement is dropped or forgotten.
- **No-new-fetch guard (new test #1 above)** — catches an implementation
  that mistakenly re-fetches from the server on every keystroke in the
  search box (AC #1 explicitly forbids this — the narrowing must be
  client-side over the already-fetched `optionsFacets.tags` array).
- **Query-param contract guard (new/updated test #3 above)** — catches any
  accidental change to the `tag=`-per-selection OR-semantics contract when
  the selection UI is reworked; this is the same contract
  `TICKETS-TABLE-PAGINATION` and `TICKETS-VIEW` both depend on being
  stable, and downstream backend filter tests
  (`test_get_tickets_or_within_tag`) assume the frontend always sends
  distinct repeated `tag=` params, never a single comma-joined value or
  AND-combined tag filter.
- **Tier/Layer/Status/Priority `<select>` non-regression** — no dedicated
  new test needed; the existing `'TicketsView — filter bar delegates to
  server query params'` tests already assert on `tier=`/`layer=` params
  alongside tag params and must keep passing, proving the other four
  dropdowns are untouched by this ticket's changes.
