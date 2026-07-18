# Implementation Sequence — agentops-stats-board

Tickets must be implemented in this order. Generated from intra-batch
dependency analysis. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260718-RETRO-STATS-REFACTOR  (no deps in this batch)
2. TCK-20260718-AGENTOPS-STATS-API  (depends on: TCK-20260718-RETRO-STATS-REFACTOR)
3. TCK-20260718-TICKET-CORPUS-REPORT  (no deps in this batch)
4. TCK-20260718-STATS-TAB-FRONTEND  (depends on: TCK-20260718-AGENTOPS-STATS-API, TCK-20260718-TICKET-CORPUS-REPORT)
5. TCK-20260718-STATS-DOCS-UPDATE  (depends on: TCK-20260718-AGENTOPS-STATS-API, TCK-20260718-TICKET-CORPUS-REPORT, TCK-20260718-STATS-TAB-FRONTEND)

## Why This Order Matters

RETRO-STATS-REFACTOR must land first — it extracts the computation
AGENTOPS-STATS-API's new endpoint calls; that endpoint would have no real
data source without it. TICKET-CORPUS-REPORT is independent of both (a
separate new report tool + endpoint over ticket-corpus data, not
agent-monitoring data) and could in principle run in parallel, but runs
third here for a stable, simple order. STATS-TAB-FRONTEND needs both
backend endpoints to exist before it has anything real to fetch and render.
STATS-DOCS-UPDATE runs last since it documents the final, landed state of
everything else.

Re-run `/implement-epic` with the same epic_id after any gate failure —
already-done tickets are skipped automatically.
