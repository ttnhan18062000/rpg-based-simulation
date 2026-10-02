# Implementation Sequence — perf-evidence-inventories

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT  (no deps in this batch)
2. TCK-20261003-PERF-HASH-CALLSITE-INVENTORY  (depends on: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT, for shared output conventions)

## Why This Order Matters

Both tickets add a read-only inventory script under `tools/perf/` with the same output and
`--check` conventions. The phase inventory settles those conventions; the hash inventory reuses
them. Parent epic: `TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC`.
