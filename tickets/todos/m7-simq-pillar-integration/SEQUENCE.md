# Implementation Sequence — m7-simq-pillar-integration

Tickets must be implemented in this order. Generated from the M7 epic's own Scope items 1-5, which
form a single dependent pipeline (mapping/inventory/rule-authoring, then calibration/completeness).
`implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES  (epic Scope items 1-3, no deps in this batch)
2. TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS  (epic Scope items 4-5, depends on: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES)

## Why This Order Matters

The calibration run needs a real rule set to exercise, and the completeness cross-check needs the
named-pillar mapping to check against — both only exist once ticket 1 lands. Re-run
`/implement-epic` with the same folder after any gate failure — already-done tickets are skipped
automatically.
