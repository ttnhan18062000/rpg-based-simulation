# Investigation: MovementPlanCache

## Current State & Problem
During simulation ticks, entities frequently evaluate their next movement step towards a target position (`NavigationSystem.get_next_step`). When many entities move long distances across multiple ticks or are waiting in congestion, recomputing pathfinding steps or flow field directions repeatedly is computationally expensive.

## Proposed Optimization
We will implement an authoritative `MovementPlanCache` that caches the calculated next step for an entity given its current tile, target tile, and the current `occupancy_version`.

### Data Structures
- `MovementPlanKey`: `(entity_id, current_tile, target_tile, occupancy_version)`
- `MovementPlan`: `(next_step, valid_until_tick)`
- `MovementPlanCache`: Maintains cached plans and an internal `occupancy_version`. When any entity moves or changes lifecycle state (tracked via `DirtySet`), `occupancy_version` is incremented and specific entity plans are invalidated.

### Integration
In `MovementSystem.resolve_move`:
1. Check if a valid, unblocked plan exists in `state.movement_cache`.
2. If cache hit, use the cached `next_step` as `effective_target`.
3. If cache miss, compute `effective_target` via `NavigationSystem.get_next_step` and verify legality. If legal and successful, cache the plan for up to 10 ticks.
