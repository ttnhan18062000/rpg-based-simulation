# Plan: MovementPlanCache

## 1. Implement `MovementPlanCache` (`src/engine/movement_cache.py`)
- Define `MovementPlanKey` frozen dataclass with `entity_id`, `current_tile`, `target_tile`, `occupancy_version`.
- Define `MovementPlan` frozen dataclass with `next_step`, `valid_until_tick`.
- Implement `MovementPlanCache` class:
  - Internal dictionary `_cache`.
  - Property `occupancy_version`.
  - Methods: `get(key, current_tick)`, `put(key, plan)`, `invalidate_for_dirty(dirty)`.

## 2. Integrate into `AuthoritativeState`, `Kernel`, and `Pipeline`
- Add `movement_cache` field to `AuthoritativeState`.
- In `AuthoritativeApplyPipeline.refine` and `Kernel._phase_init`, call `movement_cache.invalidate_for_dirty(update.dirty_set)` when a dirty set is present.

## 3. Update `MovementSystem.resolve_move` (`src/engine/movement.py`)
- Construct `MovementPlanKey`.
- Check `state.movement_cache.get(...)`.
- On miss or if cached move fails legality, recalculate via `NavigationSystem.get_next_step`.
- If successful, put the successful `next_step` into `state.movement_cache`.

## 4. Verification
- Create unit test suite `tests/unit/optimization/test_movement_plan_cache.py`.
- Run unit tests and regression test suite.
