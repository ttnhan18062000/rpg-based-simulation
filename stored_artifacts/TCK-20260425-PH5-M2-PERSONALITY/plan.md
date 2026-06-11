---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH5-M2-PERSONALITY
artifact_type: plan
tags: [ph5, m2, personality]
---

# PH5 M2: Personality, Boredom, and Life Stage

Implement modifiers that add psychological depth to entity decision making.

## Proposed Changes

### [Core State] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Add `PersonalityComponent`:
  - `greed: float`
  - `bravery: float`
  - `sociability: float`
  - `industry: float`
- Add `LifeStage` enum: `CHILD`, `ADULT`, `ELDER`.
- Update `IdentityComponent` to include `personality: PersonalityComponent` and `life_stage: LifeStage`.

### [Strategic State] [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py)
- Update `StrategicComponent` to include `boredom: Dict[str, float]`.
- Update `StrategicUpdate` to include `boredom_delta: Dict[str, float]`.

### [AI Modifiers] [NEW] [personality.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/personality.py)
- Implement `PersonalityService` that maps traits to utility modifiers for specific goal kinds.

### [AI Modifiers] [NEW] [life_stage.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/life_stage.py)
- Implement `LifeStageService` that provides multipliers based on age/stage.

### [AI Modifiers] [NEW] [score_modifiers.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/score_modifiers.py)
- Implement a unified `ScoreModifierSystem` that orchestrates all modifiers.

### [Strategic System] [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic.py)
- Integrate `ScoreModifierSystem` into `evaluate_strategic_intent`.
- Ensure boredom increases when a project is active.

### [Apply Path] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Implement boredom decay (passive reduction each tick).
- Apply `boredom_delta` from updates.

## Verification Plan

### Automated Tests
- `tests/ai/test_personality_goal_modifiers.py`:
  - Verify greedy entity prefers harvesting/loot.
  - Verify brave entity prefers combat over fleeing.
  - Verify bored entity switches goals even if the current one has high base utility.
  - Verify life stage multipliers are applied correctly.

### Manual Verification
- Replay inspection of goal scores to ensure modifiers are visible and correct.
