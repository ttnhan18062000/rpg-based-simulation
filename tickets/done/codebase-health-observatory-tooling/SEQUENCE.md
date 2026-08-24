# Implementation Sequence — codebase-health-observatory-tooling

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD  (no deps in this batch)
2. TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR  (depends on: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.