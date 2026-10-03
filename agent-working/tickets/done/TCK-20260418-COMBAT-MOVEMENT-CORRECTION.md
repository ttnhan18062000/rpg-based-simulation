---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260418-COMBAT-MOVEMENT-CORRECTION
phase: done
date: 2026-04-18
tags: [combat, movement, correction]
---

# TCK-20260418-COMBAT-MOVEMENT-CORRECTION

## Title
Implement Combat and Movement Overhaul Corrective Update

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the work specified in `combat_movement_updated.md`, which addresses remaining gaps and "thin parts" in the combat and movement overhaul across 7 milestones.

## Scope
- [x] Milestone 1: Rulebook hardening and quiet-tick drift guards
- [x] Milestone 2: Combat-context layer and anti-stalemate proof
- [x] Milestone 3: Movement anti-oscillation and congestion edge cases
- [x] Milestone 4: Tactical depth (cover, chokepoints, group coordination)
- [x] Milestone 5: Stat-ownership rebalance and role ceilings
- [x] Milestone 6: Arena harness resource hardening and scenario expansion
- [x] Milestone 7: Finalize structured reason authority and doc-integrity

## Out of Scope
- Rebuilding foundations that are already materially implemented (Manhattan, OA, stuck-threshold, wounds, etc.)
- Broad architectural changes outside the narrowed corrective scope.

## Acceptance Criteria
- All 7 milestones in `combat_movement_updated.md` are completed and verified.
- Rulebook is singular and authoritative.
- Combat context is real and proven.
- Movement anti-oscillation is broader than stuck-threshold.
- Tactical cover/chokepoint claims are real or narrowed.
- Speed-as-tempo and role ceilings are directly proven.
- Arena harness is authoritative and resource-stable.
- Structured reasons and documentation integrity are authoritative.

## Related Tickets
- None

## Related Docs
- [combat_movement_updated.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_updated.md)
- [overhaul_spec.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/overhaul_spec.md)

## Related Stored Artifacts
- [walkthrough.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-COMBAT-MOVEMENT-CORRECTION/walkthrough.md)
- [plan.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-COMBAT-MOVEMENT-CORRECTION/plan.md)
- [plan_task.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260418-COMBAT-MOVEMENT-CORRECTION/plan_task.md)

## Related Code Areas
- Legality service
- Combat interaction module
- Movement model
- Tactical AI evaluators
- Derived stat calculations
- Arena runner
- Action/Reason models

## Implementation Notes
- Completed structured reason authority and rejection auditing in Milestone 7.
- Hardened Arena regression harness with watchdog and resource isolation in Milestone 6.
- Established authoritative specification in `docs/overhaul_spec.md`.

## Test Summary
- Verified with 14 arena regression tests in `tests/arena/`.
- New observability audit tests in `tests/arena/test_observability_audit.py` (ALL PASSED).

## Files Changed
- `src/core/logic/legality_service.py`
- `src/actions/move.py`
- `src/actions/combat.py`
- `src/ai/tactical/tactical_evaluator.py`
- `src/engine/arena/runner.py`
- `src/core/models/arena.py`
- `src/engine/phases/resolution.py`
- `src/engine/phase_guard.py`
- `src/engine/arena/metrics.py`
- `docs/overhaul_spec.md` (NEW)
- `tests/arena/test_observability_audit.py` (NEW)

## Completion Summary
Full corrective overhaul successfully implemented across all 7 milestones. The simulation engine now features authoritative spatial legality, structured and auditable reasoning for all tactical decisions, anti-stalemate movement guarantees, and a hardened arena regression harness with sub-second performance monitoring and watchdog protection.
