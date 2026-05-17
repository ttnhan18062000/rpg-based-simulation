# Test Plan: MovementCandidateSelector

## Objectives

Verify `MovementCandidateSelector` strictly filters candidate entities according to state, update, readiness, and cadence rules while maintaining exact determinism and full-scan fallback compliance.

## Test Cases (`tests/unit/optimization/test_movement_candidate_selector.py`)

1. `test_movement_selector_skips_entity_without_target`
   - Entity active/alive but `target` is None -> skipped.
2. `test_movement_selector_skips_entity_already_at_target`
   - Entity active/alive, `position == target` -> skipped.
3. `test_movement_selector_skips_inactive_or_dead_entity`
   - Entity inactive or dead (alive=False) -> skipped.
4. `test_movement_selector_includes_entity_with_target_and_readiness`
   - Entity active/alive, `target != position`, `readiness >= move_cost` -> included.
5. `test_movement_selector_includes_entity_when_target_changed`
   - Entity with low readiness but `ent_upd` sets new target -> included.
6. `test_movement_selector_force_full_scan_includes_all_movable_entities`
   - `force_full_scan` is True -> includes entities with `target != position` even if readiness is low.
7. `test_movement_selector_is_deterministic`
   - Running selection multiple times with shuffled input candidates produces identical sorted tuples.

## Execution

```bash
pytest tests/unit/optimization/test_movement_candidate_selector.py -v
pytest tests/unit/ -m "not slow"
```
