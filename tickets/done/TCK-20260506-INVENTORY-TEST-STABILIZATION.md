# TCK-20260506-INVENTORY-TEST-STABILIZATION

## Title

Migrate inventory test suites to V2EntityBuilder

## Status

INPROGRESS

## Request Summary

Resolve remaining test suite failures in `tests/inventory/` by systematically refactoring legacy `EntityState` instantiations to the `V2EntityBuilder` fluent API.

## Scope

- Identify legacy `EntityState` instantiations in `tests/inventory/`
- Migrate `test_equipment_chests_storage.py` to `V2EntityBuilder`
- Migrate `test_equipment_ranking.py` to `V2EntityBuilder`
- Migrate `test_harvest_channeling.py` to `V2EntityBuilder`
- Migrate `test_inventory_hardening.py` to `V2EntityBuilder`
- Migrate `test_item_inventory_contract.py` to `V2EntityBuilder`
- Migrate `test_loot_channeling.py` to `V2EntityBuilder`
- Final verification of all tests in `tests/inventory/`

## Out of Scope

- Changes to inventory systems or engine logic unless necessary for parity.

## Acceptance Criteria

- All tests in `tests/inventory/` pass.
- No direct `EntityState` instantiations in the affected test files.

## Related Tickets

- TCK-20260504-CORE-TEST-STABILIZATION

## Related Docs

- logic_checklist_exhaustive.md

## Related Stored Artifacts

- None

## Related Code Areas

- tests/inventory/

## Assumptions / Open Questions

- None

## Implementation Notes

- Use `V2EntityBuilder` for all entity creation in tests.
- Update property access if needed (e.g., `inventory.gold`).

## Test Summary

- Initial run: 15 failed, 1 passed.
- Final run: 16 passed, 0 failed.

## Files Changed

- `src/core/builder.py`
- `tests/inventory/test_equipment_chests_storage.py`
- `tests/inventory/test_equipment_ranking.py`
- `tests/inventory/test_harvest_channeling.py`
- `tests/inventory/test_inventory_hardening.py`
- `tests/inventory/test_item_inventory_contract.py`
- `tests/inventory/test_loot_channeling.py`

## Completion Summary

Successfully migrated all 16 tests in `tests/inventory/` to the `V2EntityBuilder` fluent API. 
Key fixes included:
- Replaced direct `EntityState` instantiations with `V2EntityBuilder`.
- Enhanced `V2EntityBuilder.with_inventory()` to support `max_weight` parameter for hardening tests.
- Updated `test_inventory_capacity_limits` to align with the V2 engine's partial inventory addition logic.
- All tests now strictly adhere to the component-based initialization contract.
