---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-V1-COUNTS-A-HUNGER-DROP-AS-BACKED-ONLY-WHEN-AN-ACCEPTED-TRANSFER-MOVED-SOMETHING
phase: active
date: 2026-10-19
tags: []
---

# TCK-20261019-V1-COUNTS-A-HUNGER-DROP-AS-BACKED-ONLY-WHEN-AN-ACCEPTED-TRANSFER-MOVED-SOMETHING

## Title
V1 counts a hunger drop as backed only when an accepted transfer moved something

## Status
INPROGRESS

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
V1 read 0 on the v1 gate run while the free meal is still in the code: the inn's TOWN_SERVICE charge (building_services.py:71-74, gold_delta -5, gold_cost 0) is accepted at 0 gold (conservation.py:256) and the -5 is clamped to 0 when applied (inventory.py:156); run_ledger `_count_hunger_drop` counted any accepted result as backing the drop. Designer-approved, rpg's module only, no world change. Trace: /mnt/data/scratch-rpg-implementer/v1_gate_fails_A.md.

## Scope
- run_ledger `_count_hunger_drop`: a drop is `with_accepted_transfer` only when an accepted result's intent moved something: items in or out, or the gold APPLIED after the clamp (min of the gold held and the debit). The requested gold_delta is never read as movement.
- A result whose intent is not in the update cannot be judged and stays backed (unchanged behaviour).
- rpg_gate_known.yaml V1 note updated.
- Tests: a broke eater at the inn is `without_transfer`; an eater holding 5 gold who pays is `with_accepted_transfer`.

## Out of Scope
- The free-meal removal (D73); any change to the world, the charge, or the clamp.

## Acceptance Criteria
- Both regression tests pass; the final hash is identical on 3 worlds, seed 42 (observer-only); V1 is non-zero where broke eaters eat at the inn.

## Related Tickets
- TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
- TCK-20261019-RECORD-BASELINE-V1

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/run_ledger.py, src/observability/rpg_gate_metrics.py (V1), tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- IntentResult (src/core/state.py:924-930) carries only transaction_id, accepted, reason, source_kind, source_id: neither the requested nor the applied amount. The requested -5 lives on the intent (ResourceTransferIntent.gold_delta) and on TransactionResult.inventory_update (conservation.py:266, gold_delta - gold_cost = requested); the clamp happens only at apply (inventory.py:156). So the transaction record carries the REQUESTED amount, not the applied one: a durable-state honesty defect, disclosed here, not fixed now.

## Implementation Notes
The applied amount is derived in the observer from the intent and the gold the eater held at the prior tick.

## Test Summary

## Files Changed

## Completion Summary
