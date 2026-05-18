# Test Plan: Component-Level Patch Model

## Objectives
Verify that the `ComponentPatch` model correctly implements no-op detection, patch merging, and exact state application parity compared to the old `EntityUpdate` monolithic logic.

## Unit Tests
`tests/unit/optimization/test_component_patches.py`:
1. `test_patch_noop_detection`: Verify that each patch type correctly returns `True` for `is_noop()` when empty, and `False` when populated.
2. `test_patch_merging`: Verify that two patches of the same type merge their deltas correctly.
3. `test_order_sensitivity`: Verify that stat-impacting patches trigger derived stat recalculation in the correct sequence.

## Integration Parity Tests
`tests/integration/optimization/test_component_patch_apply_parity.py`:
1. `test_patch_apply_parity`: Create an `AuthoritativeState` and a rich `StateUpdate` with complex entity updates across all domains (navigation, combat, inventory, strategic, identity, social). Apply updates using the patch model vs the legacy model and verify 100% identical resulting states.

## Verification Commands
```bash
pytest tests/unit/optimization/test_component_patches.py
pytest tests/integration/optimization/test_component_patch_apply_parity.py
pytest tests/perf/test_optimization_proof_report.py
pytest tests/api/test_rest_parity.py
```
