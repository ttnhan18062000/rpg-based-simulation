---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS
artifact_type: test_plan
tags: [core]
---

# Test Plan — TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS

`tests/unit/engine/test_interaction_unknown_item_diagnostic.py`: unknown id -> reset preserved, counter == 1,
typed event (tick, actor, reason UNKNOWN_ITEM, target node); capacity failure -> no unknown record; successful
harvest -> no record, harvest intent produced; `enforce` does not mutate the input state and is deterministic
across two calls; `unknown_item_ids` helper. Regression: `tests/unit/core/test_interaction_recovery.py`,
`tests/integrity/test_logic_guards.py`, and the scoped non-slow suite.
