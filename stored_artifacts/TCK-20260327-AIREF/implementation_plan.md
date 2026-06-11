---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [airef]
---

# AI Refinement E2E Final Stabilization Plan (Forced Engagement)

I have identified the final logical hurdle in the `1012 < 1012` failure:
- **Default AI State**: Mobs added via `add_mob` default to `AIState.WANDER`.
- **The Issue**: In the first tick, even with high speed and initiative, the Boss might choose to `MOVE` randomly (Wander) instead of attacking, especially since the `CombatGoal` score at Tick 0 might be competing with other goals.
- **The Solution**: Explicitly set the Boss to `AIState.HUNT` and set its `combat_target_id` to the Hero's ID. This forces the `HuntHandler` to immediately transition to `Combat` and execute an `ATTACK` on the first tick.

## User Review Required

> [!NOTE]
> This ensures the "Soul" (Memory) story begins immediately upon the first tick of the simulation.

## Proposed Changes

### [Tests] [test_combat_arena_e2e.py](file:///d:/Projects/rpg-based-simulation/tests/e2e/test_combat_arena_e2e.py)

#### [MODIFY] `test_nemesis_recognition_and_fear_bias`
- Set Boss `ai_state = AIState.HUNT`.
- Set Boss `combat_target_id = 1`.

## Verification Plan

### Automated Tests
- `pytest tests/e2e/test_combat_arena_e2e.py::TestAIRefinementE2E::test_nemesis_recognition_and_fear_bias`
- Expect 100% pass rate.
