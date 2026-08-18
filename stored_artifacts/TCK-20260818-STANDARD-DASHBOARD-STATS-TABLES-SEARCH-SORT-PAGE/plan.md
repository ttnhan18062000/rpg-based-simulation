---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE
tags: [dashboard, observability]
---

# Plan — TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE

## Approach
1. Build `SearchableTable<T>` (`dashboard-frontend/src/components/SearchableTable.tsx`): generic
   columns config (`key`, `header: ReactNode`, `accessor`, optional `render`/`numeric`/`sortable`),
   `rows`, `rowKey`, optional `rowTestId` override, `defaultSortKey`/`defaultSortDir`,
   `pageSizeOptions`. Internal `useState` for query/sortKey/sortDir/page/pageSize; `useMemo` for
   filter → sort → paginate pipeline.
2. Remove `TOP_AGENTS_LIMIT` cap from `topAgentRows()`.
3. Add `statusBreakdownColumns<T>()` helper generating the shared 6-column set for Top
   Agents/Phase Status (name + total/ok/failed/blocked/skipped, glossary-tooltipped headers).
4. Replace the 4 named sections' raw `<table>` JSX with `<SearchableTable>`, each passing
   `rowTestId` matching the exact pre-existing testid convention.
5. Add "Avg agents per run" `StatTile` and a `done_count (X%)` computed display to the top
   summary row.
6. Verify: `tsc -b`, `vitest run` (scoped then full), `npm run build`, then a live check against
   the actually-running dashboard server (not just trusting the local build).

## Scope guards
- No backend/API changes.
- No changes to any other dashboard view/table not named in the request.
- Zero test file modifications — `rowTestId` override preserves every existing assertion.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| Top agents: all rows, searchable, sort-by-total default, paged | `SearchableTable` + no cap |
| Phase status: same treatment | `SearchableTable` |
| Slow runs / Duration outliers: same treatment | `SearchableTable` |
| Avg agents per run + DONE % shown | New StatTile + computed display |
| tsc clean | `npx tsc -b` |
| Existing tests pass unmodified | `npx vitest run src/test/StatsView.test.tsx` |
| Build succeeds, live-served | `npm run build` + `curl`/`grep` against the real server |
