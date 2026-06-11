---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260418-CORE-RULEBOOK-HARDENING
phase: done
date: 2026-04-18
tags: [core, rulebook, hardening]
---

# TCK-20260418-CORE-RULEBOOK-HARDENING

## Title

Harden Authoritative Rulebook and Quiet-Tick Lifecycle Contract

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Milestone 1 of the Combat and Movement Overhaul corrective plan (combat_movement_updated.md). This includes hardening the LegalityService as the singular source of truth for spatial/occupancy rules and protecting quiet-tick passive progression against future drift.

## Scope

- Audit and consolidate raw legality math (distance, occupancy, LOS) into `LegalityService`.
- Replace duplicate logic in `MovementModel` and `CombatAction` with `LegalityService` calls.
- Implement drift guards/tests for quiet-tick passive progression.
- Document authoritative rulebook and passive progression contracts.

## Out of Scope

- Implementing combat-context modifiers (Milestone 2).
- Implementing anti-oscillation logic (Milestone 3).
- Full routing of AI/UI/Gen through LegalityService (kept as shared primitives where preferred).

## Acceptance Criteria

- `LegalityService` is the sole authority for action/movement/combat validation.
- `MovementModel` uses `LegalityService` for sidestep distance and occupancy checks.
- `CombatAction` uses `LegalityService` for targeting (including LOS).
- Tests prove that passive systems (biological decay, lifecycle, registered subsystems) advance even on quiet ticks (no actions).
- No raw Manhattan or grid-access math remains in sensitive validation paths.

## Related Tickets

- None

## Related Docs

- [combat_movement_updated.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_updated.md)

## Related Stored Artifacts
- [plan.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-CORE-RULEBOOK-HARDENING/plan.md)
- [test_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-CORE-RULEBOOK-HARDENING/test_plan.md)
- [investigation.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-CORE-RULEBOOK-HARDENING/investigation.md)

## Related Code Areas

- `src/core/logic/legality_service.py`
- `src/core/logic/movement_model.py`
- `src/actions/combat.py`
- `src/engine/phases/presystems.py`

## Assumptions / Open Questions

- "AI/UI/Gen" preference for shared primitives in `tmp/msg.txt` applies to `MovementModel`'s internal distance checks (Manhattan) but not its occupancy checks?
- "Drift guards" refer primarily to regression tests ensuring passive systems are called every tick.

## Implementation Notes

- Add `get_occupant_id` to `LegalityService` to support MovementModel's yielding logic.
- Add `check_targeting_legality` to `LegalityService` to encapsulate range + LOS.

## Test Summary

- `tests/engine/test_quiet_tick_integrity.py`: 4/4 PASSED (Verified Scenario 1, 2, 3 and Subsystem advancement)
- `tests/combat/test_combat_movement_rulebook.py`: 9/9 PASSED (Verified LegalityService expansion)
- `tests/combat/test_world_time_progression.py`: 2/2 PASSED (Verified baseline time mechanics)

## Files Changed

- `src/core/logic/legality_service.py`: Added `get_occupant_id`, `check_targeting_legality`, `get_distance`.
- `src/core/logic/movement_model.py`: Refactored to use `LegalityService`.
- `src/actions/combat.py`: Refactored `validate()` to use `LegalityService`.
- `src/core/models/snapshot.py`: Added `get_entity_at()`.
- `tests/engine/test_quiet_tick_integrity.py`: [NEW] Drift guard regression tests.
- `tests/combat/test_combat_movement_rulebook.py`: Added unit tests for new `LegalityService` methods.

## Completion Summary

- Consolidating spatial and combat legality logic into the authoritative `LegalityService`.
- Refactored `MovementModel` and `CombatAction` to remove raw math and centralized rulebook calls.
- Implemented drift guard regression tests to ensure passive systems (decay, lifecycle, social bonding) advance during quiet ticks.
- Achieved 100% test passing rate for Milestone 1 scope.
