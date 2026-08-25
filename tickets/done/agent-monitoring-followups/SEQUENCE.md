# Implementation Sequence — agent-monitoring-followups

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION  (no deps in this batch)
2. TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY  (depends on: TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION)
3. TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX  (no deps in this batch)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
