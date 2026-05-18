# Test Plan: StateUpdateCompactor

## Objectives
Validate that `StateUpdateCompactor`:
1. Correctly identifies and prunes no-op subcomponents across all simulation update models.
2. Accurately identifies matching properties on existing entities and strips redundant property updates.
3. Completely drops empty `EntityUpdate` objects from `entity_updates`.
4. Emits accurate reduction metrics (`raw_entity_updates`, `compacted_entity_updates`, `dropped_noop_updates`, etc.).
5. Preserves 100% semantic parity when applied via `ApplyPath.apply_generation()`.

## Test Cases
- `test_compactor_drops_empty_entity_update`: Verify pure empty `EntityUpdate` is stripped.
- `test_compactor_drops_zero_delta_combat_update`: Verify `CombatUpdate(hp_delta=0)` is pruned and entity dropped.
- `test_compactor_preserves_nonzero_combat_update`: Verify `CombatUpdate(hp_delta=-10)` is kept intact.
- `test_compactor_drops_property_update_equal_to_current_value`: Verify matching properties are pruned.
- `test_compacted_update_applies_same_as_uncompacted_update`: Verify final state hash equality between raw and compacted updates.
- `test_compactor_reports_reduction_metrics`: Verify `CompactionMetrics` correctness.
