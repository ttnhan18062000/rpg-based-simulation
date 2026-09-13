# Implementation Sequence — perf-m0-architecture-governance

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260913-PERF-M0-SOURCE-AUDIT  (no deps in this batch)
2. TCK-20260913-PERF-M0-OWNER-TRIAGE  (depends on: TCK-20260913-PERF-M0-SOURCE-AUDIT)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
