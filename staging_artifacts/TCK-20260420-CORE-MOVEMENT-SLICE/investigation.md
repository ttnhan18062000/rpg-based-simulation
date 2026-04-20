# Investigation: Deterministic Grid Movement

## Original `src` Logic
- **`MoveAction.validate`**: 
  - Verifies actor is alive.
  - Verifies target is walkable (grid check).
  - Verifies target occupancy (LegalityService check).
  - Verifies no "double claims" in the same tick (occupied set).
- **`MoveAction.apply`**:
  - Emits `NavigationUpdate` and `SpatialUpdate`.
  - NO direct mutation (AOA Stabilization).

## `src_v2` Gaps
- `MovementIntention` enum needs to be present in `src_v2`.
- `NavigationUpdate` and `SpatialUpdate` models need to be defined in `src_v2`.
- `LegalityService` needs to be ported or its occupancy logic extracted.
- The `Kernel` tick loop (Phase 2: Scheduling, Phase 3: Collection) needs to be updated to handle movement work.

## Constraint Audit
- Movement must follow the 6-phase authoritative loop.
- It is a "Local" work kind for this milestone.
- Replay must capture the new updates.
