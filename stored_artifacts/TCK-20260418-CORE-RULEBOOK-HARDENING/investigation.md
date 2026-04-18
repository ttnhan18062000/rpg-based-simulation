# Investigation: Rulebook and Quiet-Tick Bypasses

## Audit Findings

### 1. Legality Bypasses (Spatial/Occupancy)
- **Combat Targeting**: `src/actions/combat.py` calls `world.grid.has_line_of_sight` directly. It should be encapsulated in `LegalityService`.
- **Sidestep Sidestepping**: `src/core/logic/movement_model.py` calls `.manhattan()` directly for candidate selection in `_find_sidestep`.
- **Occupancy Check**: `src/core/logic/movement_model.py` has a manual loop over `nearby_entity_ids` to find a blocker. This should be a singular `LegalityService` call.

### 2. Quiet-Tick Progression
- **Entry Point**: `WorldLoop._step` calls `PreSystemsPhase.execute`.
- **Subsystems**: `PreSystemsPhase` calls `system_manager.tick`.
- **Risk**: If `PreSystemsPhase` is skipped or if logic inside `PreSystemsPhase` has early returns based on "no active entities", passive systems like biological decay or bonding might stop.
- **Current State**: `PreSystemsPhase` correctly calls these systems regardless of entity activity, but there are no specific regression tests enforcing this "no matter what" behavior if the phase order or logic changes.

## Proposed Fixes
- Add `get_occupant_id` to `LegalityService` using the existing O(1) spatial query pattern.
- Add `check_targeting_legality` to `LegalityService` to combine range and LOS.
- Refactor `CombatAction` and `MovementModel` to use these new methods.
- Add `tests/engine/test_quiet_tick_integrity.py` with 100% mocked actions to prove passive systems still tick.
