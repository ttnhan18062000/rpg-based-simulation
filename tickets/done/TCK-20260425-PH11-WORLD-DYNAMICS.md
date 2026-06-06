# TCK-20260425-PH11-WORLD-DYNAMICS

## Title
Phase 11: Environmental Hazards, Calamity, and Region Transformation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Recover world-state dynamics, calamity spread, and dynamic region modifiers in the V2 engine.

## Scope
- Expand RegionState with kind, weather, and active_modifiers.
- Implement EnvironmentService for hazard/weather effects.
- Implement TransformationService for regional type shifts.
- Update ApplyPath to handle regional authoritative updates.
- Verify suppression logic for worker actions.
- [NEW] Integrate CalamityService for maturity and boss spawns.
- [NEW] Integrate RaidService for faction raids.
- [NEW] Orchestrate macro dynamics in WorldDynamicsSystem.

## Out of Scope
- Full macro-war system (Phase 11.4).

## Acceptance Criteria
- [x] RegionState supports kind, weather, and modifiers.
- [x] WorldUpdate handles regional authoritative deltas.
- [x] EnvironmentService correctly calculates stat penalties and hazard drain.
- [x] TransformationService correctly triggers type shifts at thresholds.
- [x] Suppression prevents RECRUIT/SABOTAGE actions in restricted regions.
- [x] Calamity spawns boss at high intensity centers on interval.
- [x] Maturity advances every 1000 ticks.
- [x] Raids spawn on interval.
- [x] 100% pass rate for tests/world/.

## Related Tickets
- TCK-20260424-PH9-FINAL-CLOSURE

## Related Docs
- resource_v2_e_phases.md (Phase 11)
- legacy_checklist.md

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/world/environment.py
- src/world/transformation.py
- src/world/calamity.py
- src/world/raid.py
- src/engine/world_dynamics.py

## Implementation Notes
- Priority fix applied to TransformationService to ensure extreme states are preferred.
- LegalityServiceV2 handles action suppression.
- WorldDynamicsSystem now orchestrates macro systems (Calamity, Raid, Transformation).

## Test Summary
- tests/world/test_hazards.py (PASSED)
- tests/world/test_weather.py (PASSED)
- tests/world/test_transformations.py (PASSED)
- tests/world/test_suppression.py (PASSED)
- tests/world/test_world_dynamics.py (PASSED)
- tests/world/test_calamity_raid.py (PASSED)

## Files Changed
- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/world/environment.py (NEW)
- src/world/transformation.py (NEW)
- src/world/calamity.py (NEW)
- src/world/raid.py (NEW)
- src/engine/world_dynamics.py (MODIFIED)
- src/engine/pipeline.py (MODIFIED)
- tests/world/test_hazards.py (NEW)
- tests/world/test_weather.py (NEW)
- tests/world/test_transformations.py (NEW)
- tests/world/test_suppression.py (NEW)
- tests/world/test_world_dynamics.py (NEW)
- tests/world/test_calamity_raid.py (NEW/FIXED)

## Completion Summary
- Finalized Phase 11 World Dynamics recovery and engine integration.
- Deterministic macro-system orchestration established.
