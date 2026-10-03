---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260322-RPG_REFINEMENT
artifact_type: plan
tags: [rpg_refinement]
---

# Implementation Plan: RPG Core Refinement (TCK-20260322-RPG_REFINEMENT)

## Goal Description
Transition the WorldLoop simulation from reactive behaviors to proactive, personality-driven RPG logic. This involves deep refinement across the "Soul, Body, Action, and Social" pillars, ensuring the 7-step Cognitive Pipeline is fully leveraged.

## Proposed Changes

### [The Soul] AI Cognitive Pipeline & Emotions
- **Mind Aspect**: Enhance `emotional_state` triggers. Add "Boredom" decay logic to `AIBrain`.
- **AIBrain**: 
    - Refine `_sensory_perception_phase` with more nuanced saliency (consider rarity, level difference).
    - Refine `_memory_appraisal_phase` to update `mood` based on recent events (victory/defeat).
    - Implement `_deliberation_tactical_phase` to use `mood` and `personality` as multipliers for goal scoring.

### [The Body] Genetics & Evolution
- **Progression Aspect**: Ensure `genetic_seed` is set at birth.
- **Attributes**: 
    - Expand `check_breakthroughs` to include `50` and `100` milestones.
    - Implement unique "Pillar Traits" for high-tier breakthroughs (e.g., `str_100` -> `Colossus`, `int_100` -> `Archmage`).

### [The Action] Tactical Refinement
- **Goal Scorers**:
    - Implement `SupportGoal` for "Generous Thinking" (healing/buffing allies).
    - Add hysteresis logic to `CombatGoal` and `FleeGoal` using `last_goal` to reduce jitter.
- **Stances**: Define `ActionStyle` effects in `ConflictResolver` (e.g., Aggressive: +10% ATK, -10% DEF).

### [The Social] Economy & Memory
- **Narrative Memory**: Implement `record_memory()` in `MindAspect` to store key highlights.
- **Trade**: Scale trade bonuses with `Fame` and `Charisma`.

---

## Verification Plan

### Automated Tests
- `pytest tests/unit/ai/test_cognitive_pipeline.py`
- `pytest tests/unit/core/test_attributes.py` (for breakthroughs)
- `pytest tests/integration/test_rpg_refinement.py` (NEW)

### Manual Verification
- Observe hero behavior over 1000 ticks in `CombatArena` to verify goal stability and proactive movement.
