# TCK-20260424-PH2-M1-RPG-RECOVERY

## Title
Phase 2 Milestone 1: RPG Core Recovery

## Status
OPEN

## Request Summary
Reintegrate the fundamental RPG interaction loop (Combat, Movement, Progression) into the V2 Engine.

## Scope
- Implement `ENTITY_BRAIN` work kind in `worker_logic.py`.
- Update `DeterministicScheduler` to dispatch `ENTITY_BRAIN`.
- Resolve logic gaps in `SimulationDomainLogic`.
- Verify combat/movement parity in a multi-tick simulation.

## Acceptance Criteria
- Entities correctly identify hostiles and move to engage.
- Combat is resolved authoritatively in the `ApplyPath`.
- XP is awarded and evolution triggers on kill.
- 100% passing parity tests in `tests/parity/test_rpg_recovery.py`.

## Related Tickets
- None (Phase 1 closure complete)

## Related Docs
- [rpg_refinement_pillars.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/rpg_refinement_pillars.md)

## Implementation Notes
- Uses `TacticalDecisionSystem` for brain logic.
- Uses `AuthoritativeApplyPipeline` for refinement.
- Adheres to the Law of 6 Phases.

## Test Summary
- TBD
