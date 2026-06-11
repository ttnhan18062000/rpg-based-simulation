---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260420-CORE-MOVEMENT-SLICE
phase: done
date: 2026-04-20
tags: [core, movement, slice]
---


# TCK-20260420-CORE-MOVEMENT-SLICE

## Title
First Official RPG Slice: Deterministic Grid Movement

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the first official gameplay slice for `src` by porting deterministic grid movement from the original `src`, ensuring it adheres to the frozen substrate contract without semantic drift.

## Scope
- Capture original movement behavior from `src/actions/move.py` and `src/ai/pathfinding.py`.
- Define V2 movement contract (Authoritative State, Work Contract, Apply Contract).
- Implement local reference path for movement in `src`.
- Integrate movement into replay, runtime, and certification surfaces.
- Add parity and certification tests.

## Out of Scope
- Combat interaction.
- Pathfinding (finding the path is AI; this slice is about the *execution* of a move).
- Complex obstacles or dynamic avoidance (beyond basic occupancy).

## Acceptance Criteria
- Movement follows the 6-phase authoritative loop.
- Position updates are bit-identical to original `src` given same seed/input.
- Movement is visible in `PressureSignals` (e.g., worker utilization if applicable).
- Certification gate passes with movement scenarios.
- Divergence log reflects any intentional changes (e.g., disaggregated utilization).

## Related Tickets
- None

## Related Docs
- [resource_phase4_high_level.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase4_high_level.md)
- [src_overview.md](file:///home/vboxuser/Work/rpg-based-simulation/src_overview.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/apply.py`
- `src/core/state.py`
- `src/core/governance.py`

## Assumptions / Open Questions
- **Assumption**: Movement is a "Local" work kind for this slice.
- **Question**: Should we implement a basic `MovementSystem` or keep it inside `Kernel` for now? (Prefer `MovementSystem` per architecture rules).

## Implementation Notes
- Use `LegalityService` parity where possible.
- Ensure `NavigationUpdate` and `SpatialUpdate` equivalents exist in `src`.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
