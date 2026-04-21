# TCK-20260421-TOWN-RESOLUTION-SCOPE

## Title
Town Resource Resolution Scope and Oracle Capture

## Status
DONE

## Request Summary
Define the narrow scope for town resource resolution in Phase 5 and capture the original `src` behavior as an oracle for parity testing.

## Scope
- Define supported town actions: selling materials, blacksmith material handling, inventory-to-progression conversion.
- Create `tests_v2/parity/town_oracle/capture_src_town.py` to capture V1 outcomes.
- Capture scenarios: Selling WOOD, upgrading with material blockers, and automatic town-entry resolution.

## Out of Scope
- Full equipment economy.
- Dynamic pricing.
- Complex crafting trees.

## Acceptance Criteria
- Scope is documented in `docs/engine/phase5_town_resolution_scope.md`.
- Oracle results are captured in `tests_v2/parity/town_oracle/results.json`.
- Characterization of V1 behavior covers success and failure cases.

## Related Tickets
- Milestone 1 (Completed)

## Related Docs
- resource_phase5_implementation_milestone_2.md

## Related Code Areas
- src/ai/states/town.py (V1)
- src/systems/economy.py (V1)

## Implementation Notes
- Use the same oracle capture pattern as Milestone 1.
- Ensure narrow scope to avoid economy bloat.

## Test Summary
- 100% Pass in `tests_v2/parity/test_town_resolution_parity.py`.
- 100% Pass in `tests_v2/contract/test_town_contract.py`.

## Files Changed
- `src_v2/engine/blacksmith.py`
- `src_v2/engine/shop.py`
- `src_v2/engine/town_resolution.py`
- `docs/engine/phase5_town_resolution_scope.md`

## Completion Summary
- Defined and captured the town resolution oracle for Phase 5.
- Implemented `BlacksmithSystem` and `ShopSystem` with full legacy parity for 14 recipes.
- Verified bit-identical automated town resolution outcomes.
