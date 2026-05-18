# Investigation: Engine Bottlenecks

Profiling via `profile_subphases.py` and `test_perf_movement.py` revealed:
1. **Collection Phase (~10-19ms for 500 entities, ~100ms+ for 1000 entities):**
   - Root cause: `AuthoritativeState.readonly_view()` calls `to_readonly()`, which loops over all entities and calls `EntityState.to_readonly()`.
   - Whenever an entity moves or regens stamina, `_readonly_cache` is cleared. Rebuilding `to_readonly()` allocates new `IdentityComponent`, `ReadOnlyDict`, `CombatComponent`, etc.
   - Solution: Cache the read-only component wrappers directly on `self` during the first `to_readonly()` call. Subsequent ticks where only position/stamina change will copy the already-readonly component references, reducing allocation overhead to near zero.

2. **Locomotion Phase (~15-28ms for 500 entities):**
   - Root cause: `resolve_position_swaps` calls `sorted()`, queries spatial grid neighbors for every entity even if stationary, and repeatedly evaluates `_desired_next_step_for_swap` for neighbor pairs.
   - Solution: Early-out if entity has no target/update, cache desired next step, and iterate dict items directly.

3. **Action Routing Phase:**
   - Root cause: Re-allocating `sliding_state = replace(sliding_state, entities=working_entities)` inside loop over actors when `sliding_state.entities` already references `working_entities`.
