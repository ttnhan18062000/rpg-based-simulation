---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH5-MIND-AND-NEEDS
phase: done
date: 2026-04-25
tags: [ph5, mind, and, needs]
---

# TCK-20260425-PH5-MIND-AND-NEEDS

## Title

Implementation of Goals, Motives, Emotion, and Biological Needs

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Restore the non-strategic AI mind loop. This includes biological pressures (Hunger, Sleep), emotional appraisal (Panic, Aggression), and a unified goal scoring system that balances strategic directives with immediate needs.

## Scope

- Implement `GoalRegistry` and `GoalScorer` plugin system.
- Integrate `SensoryFilter` and `AppraisalSystem` into the `SimulationDomainLogic.execute_brain` loop.
- Implement biological debt accumulation and recovery.
- Restore "Town Loop" interactions for biological recovery (Inn for sleep, Tavern for hunger).
- Add parity tests for goal switching and need-driven behavior.

## Out of Scope

- Social contracts and reputation-based recruitment (Phase 9).
- Advanced narrative generation (Phase 11).

## Acceptance Criteria

- [x] Entities accumulate hunger and sleep debt over time.
- [x] High hunger/sleep debt triggers "Eat" or "Sleep" goals via `GoalRegistry`.
- [x] Appraisal System correctly identifies "Panic" state and triggers fleeing.
- [x] Sensory filtering limits the number of salient neighbors processed.
- [x] All Phase 5 contract tests pass.

## Related Tickets

- TCK-20260425-PH4-TACTICAL-AI (Closed)

## Related Docs

- resource_v2_e_phases.md
- legacy_checklist_verified.md

## Related Code Areas

- src/ai/goals/
- src/engine/domain_logic.py
- src/engine/cognition.py
- src/systems/routine.py
- src/systems/strategic.py
- src/engine/town_resolution.py

## Implementation Notes

- V2 uses `BiologicalComponent` to track debt.
- `GoalRegistry` now provides a extensible way to add new goal types.
- `execute_brain` is the primary entry point for the cognition pipeline.

## Test Summary

- `tests/parity/test_biological_needs.py`: Verified debt accumulation, goal triggering, and recovery.
- `tests/parity/test_cognition_pipeline.py`: Verified sensory filtering and emotional panic.

## Files Changed

- src/engine/domain_logic.py
- src/engine/town_resolution.py
- src/systems/strategic.py
- src/systems/routine.py
- src/ai/goals/base.py [NEW]
- src/ai/goals/scorers.py [NEW]
- src/ai/goals/__init__.py [NEW]

## Completion Summary

Phase 5 Milestone 1 is complete. The engine now supports biological needs, emotional state, and utility-based goal selection. The "Town Loop" recovery logic is restored and verified.
