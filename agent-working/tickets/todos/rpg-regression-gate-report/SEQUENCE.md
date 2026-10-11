# Implementation Sequence — rpg-regression-gate-report

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-09 by testing-planner.

`TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC` is scope-only and is not in the order. The rpg-side tickets (the metric computation module, the
SimQ needs/livelihood pillar) are rpg-planner's and live elsewhere. Child 3's real wiring waits for the metric module.

## Order

1. TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE  (no deps)
2. TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS  (no deps; uses child 3's harness hash once it exists, and a placeholder until then)
3. TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS  (a stub metric module until rpg's lands)
4. TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN  (depends on: 1, 2, 3)
5. TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW  (depends on: 4)
