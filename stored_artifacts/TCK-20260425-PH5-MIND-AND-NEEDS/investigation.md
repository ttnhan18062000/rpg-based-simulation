# Investigation: Phase 5 - Mind and Needs

## Current State Analysis
- `BiologicalComponent` exists in `EntityState` with `hunger`, `sleep_debt`, and `rest_pressure`.
- `ApplyPath.apply_generation` already accumulates hunger (0.1) and sleep debt (0.05) per tick.
- `RoutineService` exists and has basic biological need evaluation logic.
- `SensoryFilter` and `AppraisalSystem` exist in `cognition.py` but are not yet integrated into the main `SimulationDomainLogic`.

## Open Questions
- Should "Sleep" and "Eat" be `Project` types or just immediate `ENTITY_ACT` tasks?
- **Decision**: They should be `Projects` so they can have objectives (e.g., "Go to Inn", "Rest at Inn") and benefit from strategic continuity.

# Test Plan: Phase 5 - Mind and Needs

## Unit Tests
- `RoutineService.evaluate_biological_needs`: Verify concern generation thresholds.
- `SensoryFilter.filter_saliency`: Verify distance/hostility/focus weights.
- `AppraisalSystem.evaluate_emotional_state`: Verify panic trigger at low HP or high trauma.

## Integration Tests
- `SimulationDomainLogic.execute_brain`: Verify that biological needs eventually force a project change.
- `ApplyPath`: Verify that "REST" and "EAT" actions correctly reduce biological debt.

## Parity Tests
- Compare goal switching frequency with legacy behavior (if possible, otherwise contract-based verification).
