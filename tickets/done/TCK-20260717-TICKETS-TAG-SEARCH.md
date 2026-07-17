---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-TICKETS-TAG-SEARCH
phase: done
date: 2026-07-17
tags: []
---

# TCK-20260717-TICKETS-TAG-SEARCH

## Title
Replace the flat all-tags button dump in the Tickets view with a searchable, collapsed multi-select

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The tag filter on the Tickets view renders every distinct tag present across the fetched ticket corpus (~1,309 values, sourced from distinctTags(optionsSource), not the 48-entry tag_registry.jsonl as originally suspected) as individual flat pill buttons in one unbroken wrapped block, with no search box, grouping, or collapse. This pushes the actual ticket table far below the fold and bloats the page to a >1.2MB DOM on initial load. By contrast, the Tier/Layer/Status/Priority filters are proper dropdowns and work fine. Needs a searchable/collapsible multi-select in place of the flat button dump.

## Scope
- Replace the flat distinctTags(optionsSource) button dump in TicketsView.tsx with a searchable, collapsed-by-default multi-select control.
- Preserve existing filter semantics exactly: selecting a tag still calls toggleTag()/applyFilters() -> fetchTickets() with one repeated tag= query param per selection (OR-within-tag), no client-side re-filtering.
- Keep optionsSource (fetched ticket data) as the tag source — do not switch to tag_registry.jsonl.

## Out of Scope
- Backend changes to GET /api/tickets's tag query-param handling.
- Any change to the tier/layer/status/priority dropdown filters (already working <select> elements).

## Acceptance Criteria
- [ ] Typing a substring into a new tag-search input narrows the rendered tag-option list to tags containing that substring (case-insensitive) without changing the ticket table contents and without triggering a new fetchTickets call.
- [ ] The tag selector is collapsed/bounded by default so initial page load does not render all ~1,309 distinct tag buttons simultaneously.
- [ ] Selecting a tag through the new control still results in one repeated tag= query param per selection (OR semantics), matching existing test coverage.
- [ ] TicketsView.test.tsx's anti-drift guard (source must not match /\.filter\(/) continues to pass — no Array.prototype.filter call is introduced.

## Related Tickets
- TCK-20260716-AGENTOPS-TICKETS-VIEW
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/test/TicketsView.test.tsx
- dashboard-frontend/src/api.ts
- dashboard-frontend/package.json

## Assumptions / Open Questions
- The tag list source is distinctTags(optionsSource) over the fetched ticket corpus, not docs/guidelines/tag_registry.jsonl as the original bug report assumed — corrected during investigation.
- No combobox/multi-select library is currently a dependency in dashboard-frontend/package.json — implementation may need a new minimal dependency or a hand-rolled search/collapse using existing primitives; justify the choice during implementation.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260717-TICKETS-TAG-SEARCH/plan.md`, Steps 1-4:

- `dashboard-frontend/src/views/TicketsView.tsx`: added `MAX_VISIBLE_TAGS = 40` module constant next to `PAGE_SIZE`; added `narrowTags(tags, query)` helper next to `removeTag()` using a manual `for` loop (case-insensitive substring match, `break` once `MAX_VISIBLE_TAGS` is reached — no `.filter(` anywhere, satisfying the blanket anti-drift regex); added `tagSearch` local UI state (`useState('')`) alongside the other view state; added a `data-testid="filter-tags-search"` text input inside the existing `data-testid="filter-tags"` wrapper; changed the tag-button `.map(...)` call to iterate `narrowTags(optionsFacets.tags, tagSearch)` instead of raw `optionsFacets.tags`. `optionsFacets.tags` (server-computed, full-filtered-corpus facets field) remains the sole source — never re-derived from `rows`, never switched to `tag_registry.jsonl`. `toggleTag()`, `removeTag()`, `applyFilters()`, `FilterSelect`, and the Tier/Layer/Status/Priority `<select>` blocks were not touched.
- `dashboard-frontend/src/test/TicketsView.test.tsx`: confirmed the 3 pre-existing tag/facets tests (~L98-122, ~L124-144, ~L303-323) pass unmodified — their 2-tag fixtures are well under the 40-tag cap. Added a new `describe('TicketsView — tag search/collapse', ...)` block with 5 tests (matching the plan's suggested set, including the optional 5th): search narrows rendered options without a new `fetchTickets` call or table change; the tag selector renders exactly 40 buttons (not all ~1,500) on initial load with a large synthetic facets.tags array; an off-page tag past position 40 becomes reachable by typing a unique substring; selecting a tag through the search-narrowed control still sends exactly one `tag=` query param; clearing the search restores the full bounded list.

No deviations from the plan.

## Test Summary
- `cd dashboard-frontend && npm test -- --run` — 7 test files, 54 tests, all passed (49 pre-existing + 5 new).
- `cd dashboard-frontend && npx tsc -b --noEmit` — no output, no errors.
- `cd dashboard-frontend && npm run build` — succeeded (`tsc -b && vite build`), no type errors, bundle built.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py -m "not slow"` — 38 passed. Confirms the `facets.tags` backend contract this ticket's UI depends on is unchanged.

## Files Changed
- `dashboard-frontend/src/views/TicketsView.tsx`
- `dashboard-frontend/src/test/TicketsView.test.tsx`
- `docs/observability/agent_ops_dashboard_contract.md`
- `docs/guides/agent_ops_dashboard.md`

## Completion Summary
Replaced the flat, unbounded `optionsFacets.tags.map(...)` tag-button dump in the Tickets view filter bar with a search-narrowed, count-bounded control: a `filter-tags-search` text input plus a manual-loop `narrowTags()` helper that case-insensitively substring-matches and caps the rendered list at `MAX_VISIBLE_TAGS = 40`. The tag source remains `optionsFacets.tags` (server-computed, full-filtered-corpus facets, unchanged from the prior pagination ticket); selection still goes through the existing `toggleTag()` → `applyFilters()` → `fetchTickets()` path with one repeated `tag=` query param per selection, and no `Array.prototype.filter(` was introduced anywhere in the file, keeping the existing anti-drift guard test green. All four acceptance criteria are met and verified by new/existing tests; full frontend regression (vitest, tsc, vite build) and the backend facets-contract sanity tests all pass. No backend, wire-contract, or parity ledger change was needed — this was a frontend-only presentational fix (parity-updater explicitly confirmed INFRA-275's scope excludes pure frontend rendering logic). `docs/observability/agent_ops_dashboard_contract.md`'s frontend SPA structure section and `docs/guides/agent_ops_dashboard.md`'s Tickets view section were both updated to describe the search-narrowed, capped tag control (and, incidentally, the pagination behavior the prior sibling ticket introduced but the user guide had not yet documented).
