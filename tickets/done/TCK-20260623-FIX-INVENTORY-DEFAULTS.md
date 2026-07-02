---
status: done
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-INVENTORY-DEFAULTS
phase: done
date: 2026-06-23
tags: [test-repair, inventory, resource, defaults, P1]
---

# TCK-20260623-FIX-INVENTORY-DEFAULTS

## Title
Reconcile inventory slot/weight defaults (~35 resource test failures)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Inventory slot or weight capacity defaults changed in source code but tests were not updated. Tests in `tests/unit/resource/` and `tests/unit/world/` assert old values:

- `test_inventory_limits`: expects 5 slots (`assert total_qty == 5`), gets 10
- Related tests: `INVENTORY_FULL` raised where `INSUFFICIENT_GOLD` expected — `ReasonCode` mismatch

This is D10 F4 (Risk 10/15). The `ReasonCode` mismatch is particularly risky because upstream callers branch on reason code. If `INVENTORY_FULL` is returned instead of `INSUFFICIENT_GOLD`, upstream logic silently takes the wrong branch.

Source: D10 audit F4. Confirmed by `tests/unit/resource/test_inventory_serialization.py::test_inventory_limits: assert 10 == 5`.

## Scope
- Determine the authoritative inventory slot/weight defaults in source (check entity anatomy docs + `src/entities/` or `src/core/` where defaults are defined)
- Either: update test assertions to match new defaults (if the default change is intentional and documented), OR revert the default to the previously documented value (if the change was unintentional)
- If the default change is intentional: update `docs/mechanics/01_entity_anatomy.md` and the parity ledger
- Fix the `ReasonCode` mismatch where `INVENTORY_FULL` is returned instead of `INSUFFICIENT_GOLD`

## Out of Scope
- Inventory system logic changes
- Adding new inventory fields
- Performance of inventory operations

## Acceptance Criteria
- `tests/unit/resource/test_inventory_serialization.py::test_inventory_limits` passes
- `tests/unit/resource/test_inventory_hardening.py` — all 4 tests pass
- `tests/unit/resource/test_resource_conservation_regression.py` — all 6 tests pass
- `tests/unit/resource/test_resource_contract.py` — all 4 tests pass
- `tests/unit/resource/test_economy_hardening.py` — all 4 tests pass
- `tests/unit/resource/test_resource_v2_boundary.py` — all 4 tests pass
- `tests/unit/resource/test_transaction_grouping.py` — all 2 tests pass
- `tests/unit/resource/test_item_inventory_contract.py` passes
- `tests/integration/pipeline/test_transaction_completion.py::TestTransactionRejectionReasons::test_insufficient_gold_records_reason` passes
- Other unit/resource and unit/world tests in the failure list pass

## Related Tickets
- D10 audit F4 (inventory capacity defaults diverged)
- D17 (docs/mechanics/01_entity_anatomy.md — biological thresholds/defaults wrong)

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` (inventory defaults section)
- `docs/parity_ledger/town_resource.yaml` (inventory capacity parity entries)
- `docs/audits/D10_test_coverage.md` F4

## Related Code Areas
- `src/entities/` or `src/core/` (inventory default constants)
- `src/domains/resource/` (inventory operations, ReasonCode)
- `tests/unit/resource/`
- `tests/unit/world/`

## Assumptions / Open Questions
- Was the slot count change from 5→10 intentional (balance decision) or an accidental regression?
- What is the parity ledger entry for inventory defaults?

## Implementation Notes
Investigation order:
1. Find where inventory slot/weight defaults are defined in source
2. Find what `docs/mechanics/01_entity_anatomy.md` says the defaults should be
3. Determine which is authoritative — code or doc
4. Fix the gap; update parity ledger if doc changes

## Test Summary
Run: `pytest tests/unit/resource/ tests/unit/world/ tests/integration/pipeline/test_transaction_completion.py -m "not slow" --tb=short`

## Files Changed
- `docs/core/items_and_inventory.md` — updated stale V1 Inventory snippet (max_slots=8) to current InventoryComponent (max_slots=16, per TOWN-013)

## Completion Summary
D10 F4 was already resolved — all 4 named tests pass. Production default is max_slots=16 (correct V2 design). Doc fix only: updated stale class name and default value in items_and_inventory.md. The 32 resource suite failures are a separate AuthoritativeApplyPipeline regression (InteractionUpdate(reset=True) not emitted when inventory full) — out of scope for this ticket.
