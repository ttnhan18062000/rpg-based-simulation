# TCK-20260328-BACKEND-RESTRUCTURE: Backend Modularization & Refactor

## Goal
Restore and complete the architectural refactoring of the RPG simulation backend. This involves decoupling the monolithic `WorldLoop` into domain-specific systems (`CombatTrackingSystem`, `GoalSystem`, `TerritorySystem`, `MemorySystem`) and finalizing the `StatsProxy` transition (cleanup of legacy `effective_*` methods).

## User Review Required
> [!IMPORTANT]
> This refactor involves major structural changes to `src/engine/world_loop.py` and the creation of new modules in `src/mechanics/` and `src/ai/`. 
> Current test failures (32 FAILED) indicate the `StatsProxy` migration is incomplete.

## Scope
- **Phase 1: Restore Subsystem Extraction**
    - `src/mechanics/combat_tracking.py`: Engagement and threat decay.
    - `src/ai/goal_system.py`: AI goal derivation (Utility AI).
    - `src/mechanics/territory.py`: Territory debuffs and defender alerts.
    - `src/mechanics/perception.py`: Entity memory and terrain mapping. 
- [x] Phase 2: Subsystem Extraction
    - [x] Extract Telemetry logic to `src/systems/telemetry_system.py`
    - [x] Extract World Evolution logic to `src/systems/world_evolution_system.py`
    - [x] Move Combat Visualization/AI states to `ActionSystem`
- [/] Phase 3: Finalize StatsProxy Cleanup & Integration
    - [x] Audit codebase for remaining `effective_` methods
    - [x] Remove legacy shims from `Entity` model
    - [x] Verify all 628 tests pass (unit)
    - [/] Fix 7 failing E2E and integration tests
    - [ ] Refactor `tests/` directory structure
- **Phase 4: Integration & Stabilization**
    - Update `WorldLoop` to delegate to these new systems.
    - Fix all regression tests.

## Acceptance Criteria
- [ ] `WorldLoop` is reduced in complexity and delegates core logic.
- [ ] New systems have dedicated unit tests.
- [ ] No `effective_*` methods remain in the codebase.
- [ ] Full `pytest` execution passes (100% success).

## Related Tickets
- `TCK-20260327-WINDBIGMOD-CLEANUP` (Included)
- `TCK-20260322-RPG_REFINEMENT`

**Tier:** standard
**Type:** chore
**Priority:** P1
