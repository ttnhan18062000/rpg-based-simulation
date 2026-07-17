---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-TICKETS-TAG-SEARCH
artifact_type: plan
tags: [observability, performance]
---

# Implementation Plan — TCK-20260717-TICKETS-TAG-SEARCH

## Summary

Replace the flat `optionsFacets.tags.map(...)` button dump at
`TicketsView.tsx:232-252` with a substring search box plus a count-bounded
(capped) button list, keeping `optionsFacets.tags` (the server-computed,
full-filtered-corpus facets field — confirmed current post-pagination-ticket
source, superseding the ticket's own stale reference to
`distinctTags(optionsSource)`) as the sole tag source. "Collapsed/bounded by
default" is resolved as design (b) from investigation.md Risk #1: an
always-visible list capped at `MAX_VISIBLE_TAGS = 40` buttons, narrowed by a
case-insensitive substring search input when non-empty, never a
click-to-expand/closed dropdown. This keeps the two existing direct-click
tests (`filter-tag-observability`, `filter-tag-infra`, 2-tag fixtures) and
the existing facets-independent-of-page-window test (2-tag fixture) passing
unmodified, since 2 is far under the 40-tag cap, while still bounding the
real ~1,309-tag production case to 40 rendered buttons (a >97% DOM
reduction). All narrowing/capping logic uses a manual `for` loop — never
`Array.prototype.filter` — per the existing `removeTag()` idiom and the
blanket `.filter(` anti-drift guard. No new npm dependency: the requirement
(text input + substring match + count bound) is fully served by existing
primitives (`useState`, a plain `<input>`, a manual loop), so a
combobox/multi-select library would be unjustified scope creep.

## Steps

### Step 1 — Add tag-search state and a manual substring-narrowing helper
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:**
- Add `const [tagSearch, setTagSearch] = useState('')` alongside the other
  `useState` declarations (~L104-111).
- Add a pure helper function next to `removeTag()` (~L67-72), using the same
  manual-loop idiom (no `.filter(`, no cap yet — cap is added in Step 2):
  ```ts
  function narrowTags(tags: string[], query: string): string[] {
    const trimmed = query.trim().toLowerCase()
    const result: string[] = []
    for (const tag of tags) {
      if (trimmed === '' || tag.toLowerCase().includes(trimmed)) {
        result.push(tag)
      }
    }
    return result
  }
  ```
- In the `filter-tags` block (~L232-252), add a text input above the button
  row, inside the existing `data-testid="filter-tags"` wrapper div:
  ```tsx
  <input
    type="text"
    data-testid="filter-tags-search"
    value={tagSearch}
    onChange={(event) => setTagSearch(event.target.value)}
    placeholder="Search tags…"
    className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary text-[11px]"
  />
  ```
  and change the `.map((tag) => ...)` call to iterate over
  `narrowTags(optionsFacets.tags, tagSearch)` instead of raw
  `optionsFacets.tags`. Do not wrap this in `useMemo` yet if it complicates
  the diff — a plain function call in render is fine at this data volume
  (≤1,309 short strings, single pass); `useMemo` may be added in Step 2 if
  desired for clarity, not required for correctness.
- `setTagSearch` must never call `applyFilters`, `fetchTickets`, or touch
  `filters`/`rows`/`totalCount` state — it is purely local UI state.
**Do NOT touch:** `toggleTag()`, `removeTag()`, `applyFilters()`, the
`FilterSelect` component, or any of the Tier/Layer/Status/Priority
`<select>` blocks.
**Verify:** New test "typing a substring into the tag search narrows the
rendered tag options case-insensitively without a new fetchTickets call"
(added in Step 3) exercises this step's code end-to-end — narrowing works
correctly regardless of Step 2's cap because the test fixtures stay well
under 40 tags. `npx tsc -b` must pass (no type errors from the new state/
helper).

### Step 2 — Cap the rendered tag list to a fixed visible bound
**Files:** `dashboard-frontend/src/views/TicketsView.tsx`
**Change:**
- Add `const MAX_VISIBLE_TAGS = 40` as a module-level constant near
  `PAGE_SIZE` (~L28).
- Extend `narrowTags` from Step 1 to stop collecting once the cap is hit,
  still via the manual loop (no `.slice` needed, but `.slice` would also be
  acceptable and is not `.filter(` — either is fine; a `break` inside the
  existing loop is simplest):
  ```ts
  function narrowTags(tags: string[], query: string): string[] {
    const trimmed = query.trim().toLowerCase()
    const result: string[] = []
    for (const tag of tags) {
      if (trimmed === '' || tag.toLowerCase().includes(trimmed)) {
        result.push(tag)
        if (result.length >= MAX_VISIBLE_TAGS) break
      }
    }
    return result
  }
  ```
  This means: with an empty search box, the first 40 tags (in
  `optionsFacets.tags`'s existing server-sorted order — already
  alphabetically sorted by `_distinct_sorted()` in `ingest.py`, no new sort
  introduced) render; with a non-empty search box, the first 40
  case-insensitive substring matches render. This is "search narrows within
  the same capped-or-matched set" — one function, one bound, applied
  uniformly whether or not a query is present.
- Do not special-case already-selected tags (`filters.tags`) to force them
  into view outside the capped/matched window — no AC requires this, and
  adding it would be untested scope creep. A selected tag that scrolls out
  of the visible 40 due to a search query remains selected in
  `filters.tags` (and still contributes to the active `tag=` query params)
  even though its button is not currently rendered; this matches the
  ticket's explicit semantics-preservation requirement (AC #3 concerns the
  query-param contract, not permanent visibility of selected buttons).
**Do NOT touch:** the sort order of `optionsFacets.tags` itself (it arrives
pre-sorted from the backend — do not re-sort client-side), `ingest.py`, or
any backend facets computation.
**Verify:** New tests "the tag selector does not render all ~1,309
facets.tags option buttons simultaneously on initial load" and "an off-page
facets tag remains reachable through the tag search after narrowing" (both
added in Step 3).

### Step 3 — Confirm existing tests unmodified, add new coverage
**Files:** `dashboard-frontend/src/test/TicketsView.test.tsx`
**Change:**
- Run the existing suite first and confirm, without editing their bodies:
  - `'filter bar narrows rows AND-across-dimensions, OR-within-tag, via
    server query params'` (~L98-122)
  - `'selecting two tags with no dimension filter sends both as repeated
    tag params'` (~L124-144)
  - `'filter dropdown options include values from tickets outside the
    currently-loaded page'` (~L303-323, the offpage-tag test)
  All three use 2-tag fixtures and click `filter-tag-*` directly with no
  "open" step — under the chosen always-visible-capped design these must
  pass with zero changes to their bodies. If any of them fail, that is a
  signal the implementation drifted from the resolved design (e.g.
  accidentally gated buttons behind a click-to-expand toggle) — fix the
  component, do not edit these tests to accommodate a different design.
- Add a new `describe('TicketsView — tag search/collapse', ...)` block
  (place after the existing `'TicketsView — facets independent of page
  window'` block, before `'TicketsView — anti-drift source guards'`) with:
  1. `'typing a substring into the tag search narrows the rendered tag
     options case-insensitively without a new fetchTickets call'` — mock a
     facets.tags list of ~5-10 short strings, type a substring matching a
     subset into `filter-tags-search`, assert only matching `filter-tag-*`
     buttons remain in the DOM, assert `mockFetch.mock.calls.length` is
     unchanged before/after typing, assert `tickets-table` rows are
     unchanged. Verifies AC #1.
  2. `'the tag selector does not render all ~1,309 facets.tags option
     buttons simultaneously on initial load'` — mock `facets.tags` as an
     array of ~1,500 synthetic strings (e.g. `tag-0000` … `tag-1499`),
     render with no search input interaction, assert
     `screen.getAllByTestId(/^filter-tag-/).length` is exactly 40 (matching
     `MAX_VISIBLE_TAGS`) or otherwise `< 50` as a bound. Verifies AC #2.
  3. `'an off-page facets tag remains reachable through the tag search
     after narrowing'` — mock a 1-ticket page plus a `facets.tags` array of
     ~1,500 synthetic tags where a distinctively-named tag (e.g.
     `zzz-offpage-target`) sits past position 40 in the array (so it is not
     in the default capped view), type a substring unique to that tag into
     `filter-tags-search`, assert `filter-tag-zzz-offpage-target` becomes
     visible. This is the guard against silently reintroducing
     `rows`-derived tag lists instead of `optionsFacets.tags` — regresses
     loudly if the implementation swaps to a `rows`-derived source.
  4. `'selecting a tag through the search-narrowed control still sends
     exactly one repeated tag= query param per selection'` — mock a
     facets.tags list larger than the cap (e.g. 50 tags), type a substring
     to narrow to a small visible set, click one of the narrowed buttons,
     assert the resulting fetch URL contains exactly one `tag=<value>`
     param matching the clicked tag, same assertion style as the existing
     ~L98-144 tests. Verifies AC #3 through the search path specifically
     (the two existing small-fixture tests already cover the no-search
     path).
  5. (optional, include if trivial) `'clearing the tag search restores the
     full (bounded) option list'` — after narrowing via (1), clear the
     search input, assert the original capped/default list re-renders.
- Do not modify, remove, or weaken the existing `.filter(` anti-drift test
  (~L327-329) — it requires no change; only confirm it still passes after
  Steps 1-2 land. Do not add a second `.filter(`-permitting exception.
**Do NOT touch:** `App.test.tsx` test bodies (re-run only, see Step 4), the
CSS-layer-padding tests (~L408-460), the column-sort tests, the pagination
tests, the rendering/null-safe/linked-runs tests.
**Verify:** `cd dashboard-frontend && npm test -- --run` — all tests in
`TicketsView.test.tsx` pass, including the 5 new tests and all pre-existing
ones unmodified.

### Step 4 — Full regression pass
**Files:** none changed; verification only.
**Change:** none — this step runs the full verification surface from
`test_plan.md` to confirm no incidental breakage.
**Do NOT touch:** anything — this is a read-only verification step. If any
command below fails, return to the relevant step above and fix the
component/test, do not patch symptoms in unrelated files.
**Verify:** run, in order:
1. `cd dashboard-frontend && npm test -- --run` (full frontend suite,
   including `App.test.tsx`'s `mockTicketsFetch`-based mount of the real
   `TicketsView`).
2. `cd dashboard-frontend && npx tsc -b`
3. `cd dashboard-frontend && npm run build`
4. `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py -m "not slow"`
   (backend sanity check only — no backend code changes expected; this
   confirms the `facets.tags` contract this ticket's UI depends on is
   still exactly what Steps 1-3 assumed).

## Scope Guards

- Do not touch `src/api/agent_ops_dashboard/ingest.py`'s `get_tickets` or
  `_distinct_sorted()` — the facets computation (server-side, full-filtered
  corpus, alphabetically sorted) is a fixed contract from
  `TCK-20260717-TICKETS-TABLE-PAGINATION` and this ticket's own Out of
  Scope.
- Do not add a new backend route or query param (e.g. a dedicated
  tag-search endpoint) — explicit ticket Out of Scope; all narrowing is
  client-side over the already-fetched `optionsFacets.tags` array, per
  AC #1's "without triggering a new fetchTickets call."
- Do not introduce any `Array.prototype.filter(` call anywhere in
  `TicketsView.tsx` — use the manual-loop `narrowTags()` helper (Steps 1-2)
  exclusively. This is mechanically enforced by the existing test at
  `TicketsView.test.tsx:327-329`.
- Do not re-derive the tag list from `rows` or any client-side
  recomputation of the fetched ticket page — `optionsFacets.tags` (server-
  computed, full-filtered-corpus) is the only source, per this ticket's own
  corrected Scope and investigation.md's Anti-Drift Hazards.
- Do not switch the tag source to `docs/guidelines/tag_registry.jsonl` (48
  entries) — explicitly ruled out in the ticket's Assumptions.
- Do not touch `FilterSelect`, or the Tier/Layer/Status/Priority `<select>`
  blocks (~L204-231) — explicit ticket Out of Scope, unrelated to the
  tag-volume problem.
- Do not change `toggleTag()`, `removeTag()`, `applyFilters()`, or
  `api.ts`'s `tag=`-per-selection query-param construction (`api.ts:129`) —
  must stay byte-for-byte compatible per AC #3.
- Do not add a new npm dependency (combobox/multi-select/autocomplete
  library) — the ACs require only a text input, substring match, and a
  count bound, all servable by existing primitives (`useState`, a plain
  `<input>`, a manual loop). Introducing a dependency here would be
  unjustified for the actual requirement.
- Do not add keyboard navigation, click-outside-to-close, Escape-to-close,
  or any open/close interaction model — the resolved design (b) is
  always-visible-and-capped, not a closeable dropdown; none of the ACs
  require open/close semantics.
- Do not force already-selected tags to remain visible outside the
  capped/matched window (see Step 2) — not required by any AC, would add
  untested complexity.
- Do not edit the two existing direct-click tests (~L98-122, ~L124-144) or
  the offpage-tag test (~L303-323) to add an "open the control" step — the
  resolved design requires no such step; if the implementation makes these
  tests fail, that is a signal to fix the component, not the tests.

## Dependency Map

- Step 2 depends on Step 1 (extends the `narrowTags` helper Step 1
  introduces; cannot cap a function that does not yet exist).
- Step 3 depends on Steps 1 and 2 (all new tests exercise the finished
  search+cap behavior together; the "off-page reachable via search" test
  specifically needs both the search narrowing from Step 1 and the cap
  from Step 2 to be meaningful).
- Step 4 depends on Step 3 (full regression pass only makes sense once new
  tests are written and passing locally).
- Steps 1 and 2 are both confined to `TicketsView.tsx` and can be reviewed
  as a single combined diff if convenient, but should land as described
  (narrowing first, cap second) so each is independently comprehensible.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — substring search narrows tag options case-insensitively, no table change, no new fetchTickets call | Step 1 (narrowTags helper + search input), Step 2 (final capped output still respects search) | "typing a substring into the tag search narrows the rendered tag options case-insensitively without a new fetchTickets call" (Step 3) |
| AC #2 — tag selector collapsed/bounded by default, does not render all ~1,309 buttons on load | Step 2 (MAX_VISIBLE_TAGS cap) | "the tag selector does not render all ~1,309 facets.tags option buttons simultaneously on initial load" (Step 3) |
| AC #3 — selecting a tag still sends one repeated tag= param per selection (OR semantics) | Steps 1-2 (toggleTag/onClick handler unchanged, only the source array iterated over changes) | Existing tests ~L98-122, ~L124-144 (unmodified, Step 3 confirms) + new "selecting a tag through the search-narrowed control still sends exactly one repeated tag= query param per selection" (Step 3) |
| AC #4 — `.filter(` anti-drift guard continues to pass | Steps 1-2 (manual-loop `narrowTags`, never `Array.prototype.filter`) | Existing test `TicketsView.test.tsx:327-329` (unmodified, Step 3/4 confirm) |

## Anti-Drift Notes

- `optionsFacets.tags` arrives already sorted and already scoped to the
  current filter set (tier/layer/status/priority/other selected tags) —
  this is existing, intentional behavior from
  `TCK-20260717-TICKETS-TABLE-PAGINATION`, not something this ticket
  introduces or should "fix." The capped/searched list must re-derive from
  `optionsFacets` on every render (plain function call or `useMemo` keyed
  on `[optionsFacets.tags, tagSearch]`), never a one-time captured snapshot
  — otherwise a filter change that shrinks/grows the facets tag list would
  leave a stale search-narrowed view.
- The `.filter(` guard (`TicketsView.test.tsx:327-329`) is a blanket regex
  over the entire file's source text, not scoped to the old
  client-row-filtering pattern it was originally written to catch. Any
  substring-narrowing logic — even though its purpose (bounding a small
  in-memory string array) is unrelated to the guard's original intent —
  must avoid the literal text `.filter(` anywhere in `TicketsView.tsx`.
- `INFRA-275` in `docs/parity_ledger/infrastructure.yaml` is the sole
  parity entry covering this subsystem and already carries three appended
  `v2_evidence`/`test_path` segments. This ticket makes no backend/wire
  contract change (frontend-only UI work over an already-existing facets
  field), so a fourth appended segment is **not a hard requirement** — it
  is at most an optional append at Finalize's discretion if the
  client-contract behavior shift (search-narrow-then-click vs.
  click-any-of-N) is judged worth recording. If appended, it must be
  strictly additive — do not overwrite the three existing segments.
- No Mechanics Bible chapter or engine contract governs this subsystem
  (read-only observability frontend, confirmed in investigation.md) — no
  divergence entry or mechanics citation is needed for this ticket.
