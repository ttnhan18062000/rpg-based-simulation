# Implementation Sequence — agent-monitoring-derived-index

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260713-MONITORING-SQLITE-INDEX  (no deps in this batch)
2. TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX)
3. TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX)
4. TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE  (depends on: TCK-20260713-MONITORING-SQLITE-INDEX)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
