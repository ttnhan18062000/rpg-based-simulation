# TCK-20260606-PHASE28-PERSPECTIVE-RELATION-MIGRATION

## Title

Phase 28 Perspective and Relation Runtime Usage Repair

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Prove perspective-derived relationship labels reach at least one real runtime decision (combat target classification/hostility checking) without broad rewrites of legacy systems.

## Scope

- Task 28.1: Integrate relation projection into combat target classification. Update `TacticalDecisionSystem` and `LegalityServiceV2` to evaluate target hostility using `FactionSemanticsService.is_hostile_compat` when dynamic relation data is available.
- Task 28.2: Keep compatibility wrapper explicit and report fallback usage. Ensure logging/reporting of fallback usage when clean relationship/perspective data is missing.
- Verification: Create comprehensive tests proving target classification, perspective targeting, beast contextual threat, and legacy fallback regressions.

## Out of Scope

- Broad rewrites of the combat engine (e.g. damage math, action execution, turn loop).
- Removing legacy enum/bucket fallbacks.
- Making race/archetype the primary source of hostility truth.

## Acceptance Criteria

- Combat target classification calls relation projection when clean data exists.
- Legacy fallback still works.
- Clean archetype/faction entities can be targeted/classified without requiring `EntityRole.MONSTER`.
- Existing combat and arena tests still pass.
- Fallback usage is logged in debug mode.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/legality.py`
- `src/engine/tactical.py`
- `src/content_semantics/faction.py`
- `src/engine/phase_graph.py`

## Assumptions / Open Questions

- We assume the `CatalogRepository` or `FactionSemanticsService` needs to be accessible in the target selection context. Since the simulation loop operates on `AuthoritativeState` and `EntityState` which are decoupled from direct file paths, we need to construct or lookup the catalog within `LegalityServiceV2` and `TacticalDecisionSystem` dynamically or retrieve it from an engine registry.

## Implementation Notes

- We imported and instantiated `FactionSemanticsService` inside target selection/hostility classification paths, passing it the active `CatalogRepository`.
- To avoid performance penalties, we cached the loaded catalog or use the standard repository loader path.
- Configured `"groups"` phase in `PhaseDependencyGraph` to `must_run_every_tick=True` to bootstrap groups correctly on tick 1, fixing the `test_arena_group_coordination` test failure.
- Appended a random suffix to `Kernel._run_id` to prevent file/directory clashes in concurrent test runners.

## Test Summary

- Added `tests/integration/combat/test_relation_combat_integration.py` containing three comprehensive integration tests covering perspective hostility, contextual threat, and legacy fallback.
- Verified all 62 unit combat tests pass.
- Verified the arena tactics coordination test (`test_arena_group_coordination`) passes.

## Files Changed

- `src/engine/legality.py`
- `src/engine/tactical.py`
- `src/engine/phase_graph.py`
- `src/engine/kernel.py`
- `tests/integration/combat/test_relation_combat_integration.py`
- `world_phase_20_28_repair.md`

## Completion Summary

- Successfully completed tasks 28.1 and 28.2. Target selection and combat legality checking now query dynamic perspective/relationship labels via `FactionSemanticsService.is_hostile_compat` when dynamic config is available, and fall back to checking legacy enum values and logging debug warning reports when dynamic config is missing.
- Solved the bootstrapping group failure in the arena suite by setting `"groups"` phase to run unconditionally every tick.
