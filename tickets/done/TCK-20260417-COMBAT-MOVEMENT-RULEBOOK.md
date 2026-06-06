# TCK-20260417-COMBAT-MOVEMENT-RULEBOOK

## Title
Combat and Movement Rulebook Milestone 1 Implementation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement Milestone 1 of the Combat and Movement Overhaul, focusing on locking the rulebook contract for space, timing, and world progression.

## Scope
- Define exact Manhattan distance and cardinal movement rules.
- Define one-unit-per-tile occupancy rules.
- Define orthogonal adjacency and engagement rules.
- Define AoE legality (center/radius/LOS).
- Define readiness-based action turns.
- Separate world-time progression from entity action turns in the engine loop.
- Implement rule-contract tests.
- Document the rulebook.

## Out of Scope
- Anti-stalemate logic (Milestone 2).
- Combat context modifiers (Milestone 2).
- Movement intentions and congestion handling (Milestone 3).
- AI tactical heuristics (Milestone 4).
- Stat rebalance (Milestone 5).

## Acceptance Criteria
- Engine obeys one explicit spatial and temporal rulebook.
- World-time and entity-turn cadence are structurally separated.
- Rule-contract tests pass for distance, adjacency, occupancy, and AoE legality.
- Determinism tests for tick progression pass.
- Documentation for the rulebook exists and is exact.

## Related Tickets
None

## Related Docs
- [combat_movement_high_level.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_high_level.md)
- [combat_movement_implementation_milestone_1.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_implementation_milestone_1.md)

## Related Stored Artifacts
None

## Related Code Areas
- `src/core/models/vectors.py`
- `src/core/world/grid.py`
- `src/engine/world_loop.py`
- `src/engine/phases/scheduling.py`
- `src/engine/phases/presystems.py`
- `src/systems/infrastructure/manager.py`

## Assumptions / Open Questions
- Assumption: Manhattan distance is `abs(dx) + abs(dy)`.
- Assumption: Adjacency is orthogonal only (distance == 1).

## Implementation Notes
- Will follow the brainstorming skill to design the contract first.
- Will follow clean-code principles.

## Test Summary
- `tests/combat/test_combat_movement_rulebook.py`: 6 tests passed (Manhattan, Adjacency, Occupancy, AoE).
- `tests/combat/test_world_time_progression.py`: 2 tests passed (Biological Decay and Hero Lifecycle on quiet ticks).

## Files Changed
- `src/core/models/types.py`: Added `LocationTarget`.
- `src/core/logic/legality_service.py`: Created authoritative rulebook service.
- `src/actions/combat.py`: Refactored validation to use `LegalityService`.
- `src/actions/move.py`: Refactored validation to use `LegalityService`.
- `src/systems/gameplay/action_system.py`: Added authoritative re-validation and supported `LocationTarget`.
- `src/engine/phases/presystems.py`: De-coupled passive progression (decay, lifecycle) from action loops.
- `src/engine/phases/resolution.py`: Removed redundant lifecycle call.

## Completion Summary
- Successfully unified simulation laws into a centralized `LegalityService`.
- Established a structural authority boundary in `ActionSystem` to ensure rule compliance.
- Decoupled world-time progression from entity turn cadence, ensuring that passive world effects (hunger, bonding) are 100% deterministic and auditable regardless of entity activity levels.
- All core rulebook constraints (Manhattan distance, orthogonal adjacency, occupancy) are now enforced with 100% test coverage.
