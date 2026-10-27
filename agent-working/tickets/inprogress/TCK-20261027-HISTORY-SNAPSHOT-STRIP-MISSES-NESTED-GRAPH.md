---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261027-HISTORY-SNAPSHOT-STRIP-MISSES-NESTED-GRAPH
phase: open
date: 2026-10-27
tags: [bug]
---

# TCK-20261027-HISTORY-SNAPSHOT-STRIP-MISSES-NESTED-GRAPH

## Title
The history API's summary mode returns the whole cognition graph and reports zero node/edge counts

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
lead-planner found this (2026-10-27, while reviewing an unrelated proposal). rpg-planner-ubuntu
re-checked it on origin/main 2afdba653.

`HistoryQueryService.get_entity_snapshots(full_graph=False)`
(`src/observability/reporting/history_query.py:56-62`) is meant to drop the graph and return
counts. It pops top-level `nodes`/`edges` and counts them. The real writer, `build_snapshot_record`
(`src/observability/cognition/schema.py:115-137`), nests them under `graph: {nodes, edges}` and
already writes `node_count`/`edge_count` itself. So on real data:
- nothing is stripped, and the full graph is returned;
- the added `nodes_count`/`edges_count` are always 0.

This reaches the API at `/api/v1/observability/history` (`src/api/routes/history.py:93-119`).

The unit fixture in `tests/unit/observability/cognition/test_cognition_query_service.py:39-93`
puts `nodes`/`edges` at top level, which hides the bug.

Two side issues:
- The query collects every match before slicing the page (L47-71).
- Three docs name the file `cognition_snapshots.jsonl`, but the real file is
  `cognition_graph_snapshots.jsonl` (history_query.py:42).

## Scope
1. In summary mode, drop the `graph` key and return the writer's own `node_count`/`edge_count`.
   Stop emitting the invented `nodes_count`/`edges_count` keys. First check, with `git grep` over
   `src/`, `frontend/` and `tests/`, whether anything reads `nodes_count`/`edges_count`. If a reader
   exists, keep the old key names as aliases computed from the nested graph, and say so in the
   ticket.
2. Make the unit fixture use the real record shape: build it with `build_snapshot_record`, not by
   hand. Assert that summary mode has no `graph` key and has correct counts, and that `full_graph=True`
   returns the nested graph.
3. Pagination: count `total` while streaming, but keep only the page slice in memory. The response
   shape stays the same.
4. Fix the file name in `docs/guides/simulation.md:104-114`, `docs/guides/observability.md:116` and
   `docs/observability/how_to_run_simulation.md:170`. The route tool shows no domain owns the two
   docs/guides files; the third is rpg's.

## Out of Scope
- Snapshot writer schema (`build_snapshot_record`) and `SCHEMA_VERSION`.
- Other history endpoints (diffs, manifests).
- Any simulation behaviour. This is a read path, so the world hash is unaffected.

## Acceptance Criteria
1. Summary mode on a real-shaped record returns no `graph` and the correct `node_count`/`edge_count`.
2. `full_graph=True` is unchanged.
3. `total`, `page` and `page_size` values are unchanged on the existing tests, and only one page is
   held in memory.
4. `pytest tests/unit/observability tests/integration -k "history or cognition" -m "not slow"` and
   the history route's API tests pass.
5. The 3 docs name `cognition_graph_snapshots.jsonl`.

## Related Tickets
- None on origin/main mention `full_graph` or `nodes_count` (lead-planner checked).

## Related Docs
- docs/observability/how_to_run_simulation.md, docs/guides/simulation.md, docs/guides/observability.md
- docs/audits/D15_entity_decision_inspection.md (cognition snapshots)

## Related Stored Artifacts

## Related Code Areas
- src/observability/reporting/history_query.py
- src/observability/cognition/schema.py (read only)
- src/api/routes/history.py (read only unless the response schema names the counts)
- tests/unit/observability/cognition/test_cognition_query_service.py

## Assumptions / Open Questions
- I assume the frontend does not read `nodes_count`/`edges_count`. Scope 1 says how to check this.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
