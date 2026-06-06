# TCK-20260424-PH2-M3-REGIONAL-SOVEREIGNTY

## Title
Phase 2 Milestone 3: Regional Sovereignty

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement regional trauma (Dread) accumulation and environmental hazards to drive emergent geographic behavior and risk management.

## Scope
- Implement trauma accumulation in `ApplyPath` on entity death.
- Integrate regional trauma bias into `AppraisalSystem`.
- Implement regional HP drain (Hazards) in `ApplyPath`.

## Acceptance Criteria
- Entity deaths increase local region `trauma_score`.
- High trauma biases entities toward panic and flight.
- Regions with high hazard levels correctly apply periodic HP drain.

## Related Tickets
- TCK-20260424-PH2-M2-COGNITIVE-HARDENING (Done)

## Related Docs
- [rpg_refinement_pillars.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/rpg_refinement_pillars.md)

## Implementation Notes
- Uses `RegionState` for persistent environmental state.
- Trauma acts as a multiplicative panic modifier.
