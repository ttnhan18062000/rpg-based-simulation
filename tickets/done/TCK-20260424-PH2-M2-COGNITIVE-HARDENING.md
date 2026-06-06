# TCK-20260424-PH2-M2-COGNITIVE-HARDENING

## Title
Phase 2 Milestone 2: Cognitive Hardening

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement selective attention, emotional appraisal, and goal hysteresis to deepen entity cognition and ensure persistence in behavior.

## Scope
- Implement `SensoryFilter` (Saliency) in `cognition.py`.
- Implement `AppraisalSystem` (Panic/Grudge) in `cognition.py`.
- Integrate hysteresis logic into `tactical.py`.
- Add `AptitudeComponent` and link to `EvolutionSystem`.

## Acceptance Criteria
- Entities prioritize salient targets over generic neighbors.
- Entities flee when panicked (low HP/overwhelmed).
- Entities resist task switching during "Lock" periods.
- Growth bonuses scale with aptitudes.

## Related Tickets
- TCK-20260424-PH2-M1-RPG-RECOVERY (Done)

## Related Docs
- [rpg_refinement_pillars.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/rpg_refinement_pillars.md)

## Implementation Notes
- Uses `StrategicComponent` for project locking.
- Uses `AptitudeComponent` for genetic determinism.
