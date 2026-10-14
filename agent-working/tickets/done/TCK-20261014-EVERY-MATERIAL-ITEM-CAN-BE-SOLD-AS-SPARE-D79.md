---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79

## Title
Every item in the MATERIAL category can be sold as spare; the code's name list goes (D79 step 1).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`src/engine/shop_sale.py` `SELLABLE_MATERIALS` listed eight names, only four in items.yaml, so most materials could never be sold (the only SELL path, H1). Owner ruling D79.

## Scope
- `spare_quantity` reads the registry kind: MATERIAL sells whole, spare WEAPON and ARMOR beyond the last, food keeps its surplus rule. `SELLABLE_MATERIALS` removed.
- An item with no category is a compile error.
- Measure alone under audit_mode (paired, base-vs-base self-check).

## Out of Scope
- The other D79 steps; the dead rules disclosed for after v1 (D78).

## Acceptance Criteria
- No item-name literal in shop_sale.py.
- A missing category fails compile (test).
- A material not on the old list (stone) is sold as spare (test).
- Divergence entry with the paired measurement.

## Related Tickets
- TCK-20261014-NAME-LITERALS-IN-SRC-SCAN

## Related Docs
- docs/guidelines/intentional_divergences.md 2.130; docs/parity_ledger/town_resource.yaml TOWN-202

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79/

## Related Code Areas
- src/engine/shop_sale.py; src/core/items.py

## Assumptions / Open Questions
- Spare weapons and armor of every kind sell (planner option B, default unless told otherwise).

## Implementation Notes
See plan.md. The measurement is dormant: no SELL or WAGE in either arm.

## Test Summary
tests/unit/world/test_every_material_item_sells_as_spare.py (5) plus the sell, economy, resource and registry-bridge suites (297 passed, 1 skipped).

## Files Changed
src/engine/shop_sale.py; src/core/items.py; the new test; divergence 2.130; TOWN-202.

## Completion Summary
SELLABLE_MATERIALS is gone; every MATERIAL item sells as spare, spare weapons and armor sell beyond the last, a categoryless item fails bootstrap. Measured: 30 paired audit_mode runs show zero SELL and zero WAGE in both arms, all counts identical; the base-vs-base repeat was identical. The sell path is dormant in the gate worlds, so the change is proved by unit tests only.
