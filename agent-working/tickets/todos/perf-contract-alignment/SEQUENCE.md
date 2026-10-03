# Implementation Sequence — perf-contract-alignment

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20261003-PERF-M2-CLAUSE-INVENTORY  (no deps in this batch)
2. TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY  (no deps in this batch; may run before or after 1)
3. TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT  (depends on: TCK-20261003-PERF-M2-CLAUSE-INVENTORY; uses TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY if closed)

## Why This Order Matters

PERF-D4 says its P1 edits follow the clause inventory, so T09's performance-document edits are
driven by that inventory's rows. The wall-clock inventory can add a fourth input to the
determinism contract text in T09, but T09 does not wait for it. The first two are evidence only
(`tools/perf/`, `tests/tools/`, `docs/performance/`); the third edits authority-P1 documents and
needs the owner's approval on the PR. Nothing in this batch touches `src/`. Parent epic:
`TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC`.
