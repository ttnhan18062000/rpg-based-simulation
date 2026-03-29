# Test Plan: RPG Core Refinement (TCK-20260322-RPG_REFINEMENT)

## Objectives
Verify that the RPG world transitions from reactive to proactive logic without regressions in combat stability. Ensure that the 4 pillars (Soul, Body, Action, Social) are correctly implemented.

## Test Cases

### 1. The Soul (Cognitive Pipeline)
- **Mood Influence**: 
    - Verify that `CombatGoal` score increases when `mood > 0.7` (Confidence).
    - Verify that `FleeGoal` score increases when `mood < 0.3` (Fear).
- **Boredom/Hysteresis**:
    - Verify that an entity stays in `AIState.WANDER` for at least 5 ticks before switching back to `AIState.IDLE` (unless interrupted).
    - Verify that `boredom_multipliers` correctly penalize the `CombatGoal` after 50 consecutive ticks of combat.

### 2. The Body (Evolution)
- **Attribute Aptitude**:
    - Verify that a hero with `agi_aptitude = 1.25` grows Agility faster than a hero with `1.0`.
- **Breakthroughs**:
    - Verify that reaching `50 Strength` adds the `Vanguard` trait.
    - Verify that reaching `100 Strength` adds the `Colossus` trait.

### 3. The Action (Stances)
- **Tactical Styles**:
    - Verify that `ActionStyle.AGGRESSIVE` increases damage dealt but also increases damage received in `ConflictResolver`.

### 4. The Social (Relationships)
- **Fame influence**:
    - Verify that low-level mobs flee from a hero with `Fame > 100` even at full HP.

## Automated Verification Scripts
- `pytest tests/unit/ai/test_cognitive_pipeline.py` (Expand with mood/boredom tests)
- `pytest tests/unit/core/test_attributes.py` (Expand with breakthrough tests)
- `pytest tests/integration/test_rpg_refinement.py` (New scenarios for proactivity)
