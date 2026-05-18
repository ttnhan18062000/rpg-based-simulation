# TCK-20260425-PH5-M2-PERSONALITY

## Title

Implementation of Personality, Boredom, and Life-Stage AI Modifiers

## Status

DONE

## Request Summary

Introduce psychological depth to AI decision-making by applying personality traits, boredom (repeated behavior tax), and life-stage biases to goal scoring.

## Scope

- Create `PersonalityComponent` and `LifeStage` models.
- Implement `boredom` tracking and decay in the strategic stratum.
- Create a modifier pipeline that applies trait biases and boredom taxes to base goal utilities.
- Integrate the modifier pipeline into the strategic intent evaluation.
- Add parity tests for trait-driven behavior.

## Out of Scope

- Social relationships affecting personality (Phase 9).
- Dynamic personality shifts (Trauma affecting traits - Phase 11).

## Acceptance Criteria

- [x] Greedy entities prioritize high-value resources.
- [x] Boredom accumulates during active projects and decays during inactivity.
- [x] Life stage modifiers correctly shift preferences (e.g. Elders prefer Rest).
- [x] Personality traits are correctly persisted and applied in the V2 engine.
- [x] All new tests in `tests/ai/test_personality_goal_modifiers.py` pass.

## Related Tickets

- TCK-20260425-PH5-MIND-AND-NEEDS (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/state.py
- src/core/strategic.py
- src/systems/strategic.py
- src/ai/personality.py
- src/ai/life_stage.py
- src/ai/score_modifiers.py

## Implementation Notes

- Modifiers are applied in `ScoreModifierSystem`.
- Boredom is incremented in `StrategicIntelligenceSystem` whenever a project is active.
- Boredom decays passively in `ApplyPath.apply_generation`.

## Test Summary

- `tests/ai/test_personality_goal_modifiers.py`: Verified personality bias, boredom accumulation/switch, and life stage shifts.
- `scratch/test_boredom_logic.py`: Verified passive boredom decay and delta application in the engine.

## Files Changed

- src/core/state.py
- src/core/strategic.py
- src/core/updates.py
- src/systems/strategic.py
- src/engine/apply.py
- src/ai/personality.py [NEW]
- src/ai/life_stage.py [NEW]
- src/ai/score_modifiers.py [NEW]

## Completion Summary

Phase 5 Milestone 2 is complete. AI entities now possess psychological traits, developmental stages, and behavioral variety through boredom. This completes the "Mind and Needs" recovery for Phase 5.
