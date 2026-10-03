# Implementation Sequence — perf-evidence-inventories

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT  (no deps in this batch; done)
2. TCK-20261003-PERF-HASH-CALLSITE-INVENTORY  (depends on: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT, for shared output conventions)
3. TCK-20261003-PERF-PROFILING-TOOLKIT  (depends on: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY, for the settled `tools/perf` conventions and a clean tree)

## Why This Order Matters

All three tickets add read-only tooling under `tools/perf/`. The phase inventory settles the
output and `--check` conventions; the hash inventory reuses them; the profiling toolkit comes last
because it also touches `pyproject.toml` and the test-scope map. Parent epic:
`TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC`.
