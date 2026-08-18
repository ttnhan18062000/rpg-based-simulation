---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE
tags: [dashboard, observability]
---

# Investigation — TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE

## Current state found
- `topAgentRows()` (`StatsView.tsx`) hard-slices to `TOP_AGENTS_LIMIT = 15` after sorting by
  total descending — no way to view the rest.
- `phaseStatusRows()` returns every phase, unsorted, no search/pagination.
- `agentStats.slow_runs` and `agentStats.outliers.duration_s` rendered as plain unpaginated
  tables — backend already bounds their size (`generate_retro.py`'s own slow-run/outlier
  thresholds), but no search/sort existed.
- `RunSummaryStats` (backend model) has `avg_agents` — never rendered. `done_count` rendered as a
  bare integer; the CLI retro's own Markdown table renders it as `37 (94%)`.
- No existing reusable client-side search/sort/pagination component in
  `dashboard-frontend/src/components/`. The only prior pagination precedent,
  `TCK-20260717-TICKETS-TABLE-PAGINATION`, is server-side (`limit`/`offset` query params) — built
  for the ticket corpus (1,109+ rows, no client-side full-fetch), a different situation from these
  stats tables (already fully fetched in one `GET /api/stats/agent-monitoring` call, no existing
  limit/offset API for them).

## Design decision
Client-side `SearchableTable<T>` generic component, not a backend pagination API — the datasets
here are small (dozens to low hundreds of rows at most) and already fully in the browser after
one fetch; adding a new paginated backend endpoint would be real, unnecessary backend work for no
benefit at this scale.

## Backward-compatibility check
`StatsView.test.tsx` asserts against specific `data-testid` values (`top-agent-row-implementer`,
`phase-status-row-Investigate`, `slow-run-row-TCK-slow-1`, `duration-outlier-row-TCK-dur-outlier`)
that don't follow a single consistent naming scheme relative to each other (singular
"top-agent-row" vs. table-name "phase-status-row" vs. "slow-run-row" vs.
"duration-outlier-row") — a naive `${testId}-row-${rowKey}` auto-generation in the new shared
component would not reproduce any of them exactly. Added a `rowTestId` override prop specifically
so each call site can supply its own exact legacy prefix, avoiding any test file changes.

## Verification performed
- `npx tsc -b`: clean.
- `npx vitest run src/test/StatsView.test.tsx`: 21/21 passed, unmodified.
- `npx vitest run` (full suite): 145/145 passed.
- `npm run build`: succeeded.
- Live check against the actually-running dashboard server (not just local build output):
  `curl http://127.0.0.1:8420/` returned the freshly built asset hash matching
  `dashboard-frontend/dist/assets/`, and `grep` against that served JS bundle found the new UI
  strings ("Rows per page", "Avg agents per run") — confirms `StaticFiles` serves `dist/` live
  from disk with no server restart needed for frontend-only changes (only backend Python code
  changes require a process restart, per earlier work this session).
