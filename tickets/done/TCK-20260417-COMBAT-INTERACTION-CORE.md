# TCK-20260417-COMBAT-INTERACTION-CORE

## Title
Combat Interaction Core Implementation

## Status
DONE

## Request Summary
Implement Milestone 2 of the Combat and Movement Overhaul, focusing on formalizing the combat interaction model. This includes engagement mechanics, opportunity attacks, target stickiness (hysteresis), and anti-stalemate logic.

## Scope
- Centralize engagement and interaction logic in `CombatInteractionService`.
- Refactor Opportunity Attacks into the interaction layer (removing from resolver).
- Implement Target Stickiness (AI hysteresis) to prevent jitter.
- Implement Anti-Stalemate logic to break rhythmic movement loops.
- Update `LegalityService` with interaction-aware helpers.
- Integrate into `MoveAction` and `CombatAction`.

## Out of Scope
- Pathfinding improvements (reserved for future milestones unless required for basic reachability).
- Ally pass-through (congestion handling is Milestone 3).
- Stat rebalance or speed-tempo changes.

## Acceptance Criteria
- [x] `CombatInteractionService` provides authoritative engagement and OA evaluations.
- [x] Opportunity Attacks are triggered by formal disengagement from tiles.
- [x] AI target selection respects a stickiness threshold.
- [x] Step-forward/step-back loops are correctly detected and broken.
- [x] Contract tests verify OA triggers, engagement clearing, and stalemate breaking.

## Related Tickets
- TCK-20260417-COMBAT-MOVEMENT-RULEBOOK (Done)

## Related Docs
- `combat_movement_high_level.md`
- `combat_movement_rulebook_m1.md`

## Related Code Areas
- `src/core/logic/legality_service.py`
- `src/core/logic/combat_interaction_service.py` (New)
- `src/actions/move.py`
- `src/actions/combat.py`
- `src/systems/gameplay/combat_system.py`
- `src/engine/conflict_resolver.py`

## Assumptions / Open Questions
- **Opportunity Attack Cost**: Opportunity attacks are treated as "free" reactions and do not consume the entity's upcoming turn.
- **Stalemate Threshold**: Loops will be triggered after 3 consecutive identical position-pairs (A->B, B->A, A->B).

## Implementation Notes
- Will follow clean-code principles and isolate interaction logic from resolver ordering.

## Test Summary
### Regression Suite
- `tests/combat/test_engagement_contract.py`: Pass
- `tests/combat/test_opportunity_attacks.py`: Pass
- `tests/combat/test_target_stickiness.py`: Pass
- `tests/combat/test_anti_stalemate.py`: Pass

## Files Changed
- `src/core/logic/combat_interaction_service.py`
- `src/core/models/world_state.py`
- `src/core/logic/legality_service.py`
- `src/actions/base.py`
- `src/engine/conflict_resolver.py`

## Completion Summary
Stabilized the combat AI regression suite (100% pass rate). Implemented O(1) spatial lookups for occupancy and engagement. Formalized OA triggers and target stickiness.
