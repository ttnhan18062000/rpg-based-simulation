---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE
phase: done
date: 2026-08-18
tags: [dashboard, observability]
---

# TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE

## Title
Make 4 Agent Ops Dashboard Stats tables searchable/sortable/paginated and fill 2 missing fields
in the Agent Monitoring summary

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Direct user request: "update the Top agents by call volume and Phase status distribution,
display a search-able table that I can view all the existing, ordered by total, with
select-able paging. Also update the Slow runs and Duration outliers (by tier) too" — followed by
"also, the top summarized statistical is missing too many fields (Agent Monitoring), update it
too".

Investigated the second request directly: `RunSummaryStats` (`src/api/agent_ops_dashboard/
models.py`) has 6 fields (`total`, `done_count`, `gate_fail_count`, `avg_duration_min`,
`avg_agents`, `total_agent_calls`) but the dashboard's top summary tile row only rendered 5 —
`avg_agents` ("Avg agents per run", already shown in the CLI retro report's own Run Summary
table) was missing entirely, and `done_count` was shown as a bare number with no percentage-of-
total the way the retro report renders it (`37 (94%)`).

For the 4 tables: "Top agents by call volume" was hard-capped to the top 15 by a
`TOP_AGENTS_LIMIT` constant with no way to see the rest; "Phase status distribution" showed every
row but with no sort, search, or pagination; "Slow runs" and "Duration outliers (by tier)" were
plain unpaginated tables (bounded by backend list size, but still no search/sort).

## Scope
- New reusable `dashboard-frontend/src/components/SearchableTable.tsx` — generic client-side
  search (substring match across all column accessor values) + click-to-sort column headers
  (default sort configurable per table) + pagination with a selectable page-size dropdown. Built
  as a shared component specifically because the same treatment was requested for 4 different
  tables, rather than writing bespoke pagination logic 4 times.
- Removed `topAgentRows()`'s `TOP_AGENTS_LIMIT = 15` cap — the searchable/paginated table makes
  truncation unnecessary; all agents are now reachable.
- Wired `SearchableTable` into all 4 named sections in `StatsView.tsx`, each defaulting to
  sort-by-total/ratio descending (matching "ordered by total" for the first two, and the most
  natural default — highest outlier first — for the latter two) while remaining click-to-resort.
- A `rowTestId` override prop was added to `SearchableTable` (in addition to the standard
  `${testId}-row-${rowKey}` auto-generated one) specifically to preserve the exact pre-existing
  `data-testid` values (`top-agent-row-*`, `phase-status-row-*`, `slow-run-row-*`,
  `duration-outlier-row-*`) the existing `StatsView.test.tsx` suite already asserts against — zero
  test file changes were needed as a result.
- Added the missing "Avg agents per run" `StatTile` and a `done_count (X%)` display to the top
  Agent Monitoring summary row.

## Out of Scope
- Server-side pagination (unlike `TCK-20260717-TICKETS-TABLE-PAGINATION`'s approach for the much
  larger ticket corpus) — these datasets (agents, phases, slow runs, outliers) are already fully
  fetched client-side in one `GET /api/stats/agent-monitoring` call with no existing
  limit/offset API, and are small enough that client-side search/sort/page is the right fit; no
  backend endpoint changes were needed or made.
- Applying `SearchableTable` to any other dashboard table not named in the request (e.g. the
  KGMCP per-ticket/per-agent tables added by the sibling ticket earlier today, or the Tickets
  view) — out of this ticket's explicit scope, though the component is reusable for exactly that
  kind of future follow-up.
- Any change to the underlying `/api/stats/agent-monitoring` response shape — this is a pure
  frontend rendering change; `RunSummaryStats` already had both fields, they just weren't
  rendered.

## Acceptance Criteria
- [x] "Top agents by call volume" shows every agent (no 15-item cap), searchable, sorted by total
      descending by default, with selectable page size.
- [x] "Phase status distribution" gets the same treatment.
- [x] "Slow runs" and "Duration outliers (by tier)" get the same treatment.
- [x] Top Agent Monitoring summary shows "Avg agents per run" and a DONE percentage.
- [x] `npx tsc -b` clean.
- [x] Full frontend test suite passes unchanged (`npx vitest run`) — no test file modifications
      required, confirming the `rowTestId` backward-compatibility approach worked.
- [x] `npm run build` succeeds; the built bundle was confirmed live-served by the running
      dashboard server (`curl` against `http://127.0.0.1:8420/` and grep for new UI strings in
      the served JS bundle) rather than just trusting a local build.

## Related Tickets
- `TCK-20260718-STATS-TAB-FRONTEND`, `TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE` (the original
  sections this ticket enhances)
- `TCK-20260717-TICKETS-TABLE-PAGINATION` (the only prior pagination precedent in this codebase —
  server-side, deliberately not followed here given the different data-scale/API-shape situation)
- `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` (landed immediately
  before this ticket, added the Skill Usage/KGMCP sections to the same view)

## Related Docs
- `docs/guides/agent_ops_dashboard.md`

## Related Stored Artifacts
`stored_artifacts/TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE/`

## Related Code Areas
- `dashboard-frontend/src/components/SearchableTable.tsx` (new)
- `dashboard-frontend/src/views/StatsView.tsx`

## Assumptions / Open Questions
None.

## Implementation Notes
`SearchableTable<T>` is a generic component: callers pass `columns` (each with an `accessor` used
for both sort and search, an optional custom `render`, and a `numeric` flag for right-alignment),
`rows`, a `rowKey` function, and an optional `rowTestId` override. A new `statusBreakdownColumns()`
helper in `StatsView.tsx` generates the shared 6-column set ("name" + total/ok/failed/blocked/
skipped, each status column keeping its original `GlossaryTooltip`-wrapped header) for both the
Top Agents and Phase Status tables, avoiding duplicating that column definition twice. Search
matches substrings across every column's accessor value (case-insensitive); sort defaults per
table via `defaultSortKey`/`defaultSortDir` and is click-to-toggle on any sortable header
thereafter.

## Test Summary
- `npx tsc -b`: clean, no errors.
- `npx vitest run src/test/StatsView.test.tsx`: 21 passed (unchanged from before this ticket).
- `npx vitest run` (full suite): 145 passed, 15 test files.
- `npm run build`: succeeded (701 modules transformed).
- Live verification: restarted-server-not-needed confirmed (`StaticFiles` serves `dist/` directly
  from disk), `curl http://127.0.0.1:8420/` returned the freshly-built asset hash, and `grep`
  against the served JS bundle confirmed new UI strings ("Rows per page", "Avg agents per run")
  are present in what's actually being served, not just in the local build output.

## Files Changed
- `dashboard-frontend/src/components/SearchableTable.tsx` (new)
- `dashboard-frontend/src/views/StatsView.tsx`

## Completion Summary
Implemented both explicit user requests: a reusable searchable/sortable/paginated table component
applied to all 4 named Stats-tab tables (removing the artificial 15-agent cap in the process),
and filled the 2 fields (`avg_agents`, DONE percentage) missing from the Agent Monitoring summary
tile row relative to what the backend model and CLI retro report already provide. Zero backend
changes were needed. Verified against the actually-running dashboard server, not just a local
build.
