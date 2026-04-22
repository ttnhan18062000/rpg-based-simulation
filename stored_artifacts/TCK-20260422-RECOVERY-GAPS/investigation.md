# Investigation: Phase 7/8 Recovery Gaps

## Objective
Identify the missing authoritative substrate components and systems required to support Regional Hazards, Calamity Consequences, Entity Evolution, and Building Sabotage.

## Findings

### 1. State Model Gaps
- `AuthoritativeState` lacked registries for `regions` and `buildings`.
- `IdentityComponent` lacked fields for tracking evolution (`evolution_level`, `evolution_points`).
- `BuildingState` was not formally defined in `src_v2/core/state.py`.

### 2. Update Model Gaps
- `StateUpdate` lacked `WorldUpdate` and `BuildingUpdate` domains.
- `EntityUpdate` lacked the ability to transform the entity `kind` (role/archetype transformation).

### 3. Pipeline Gaps
- The `AuthoritativeApplyPipeline` did not include hooks for world-level dynamics (Hazards) or infrastructure changes (Sabotage).
- Evolution checks were not part of the authoritative tick loop.

### 4. Scenario Drift
- `src_v2/certification/scenarios.py` (specifically `INTEG_RESOURCE_LOOP`) was attempting to initialize `IdentityComponent` with a `navigation_target` field which does not exist in the V2 model, causing `TypeError` during scenario builds.
- Integrity tests in `tests_v2/integrity/test_logic_guards.py` were also referencing this non-existent field.

## Conclusion
The substrate requires immediate expansion of the core state models and the introduction of specialized systems within the `RESOLUTION` phase of the authoritative pipeline.
