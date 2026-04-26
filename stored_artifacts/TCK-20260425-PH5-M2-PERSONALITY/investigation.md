# Investigation — PH5 M2: Personality and Boredom

## Goal
Implement modifiers that shift AI utility based on personality, life stage, and repeated behavior (boredom).

## Components to Add/Modify

### 1. Personality Profile
Need a way to store persistent traits:
- `greed`: Increases utility of loot/harvest/trade.
- `bravery`: Reduces utility of flee, increases combat.
- `sociability`: Increases social goals.
- `industry`: Increases work goals (harvest/craft).

### 2. Life Stage
Entities should evolve their preferences:
- `CHILD`: High curiosity (explore), low industry.
- `ADULT`: High industry (work), high greed.
- `ELDER`: High rest, low bravery.

### 3. Boredom
Strategic state should track how many times a goal kind has been completed or actively pursued recently.
- `boredom: Dict[str, float]` in `StrategicComponent`.
- Each tick of an active project increases boredom for that kind.
- Completing an objective adds a chunk of boredom.
- Boredom decays over time.

## Modifier Pipeline
The `GoalRegistry.get_all_scores` returns base utilities. We need a `ModifierSystem` that applies:
1. **Personality Bias**: `base_utility * (1.0 + personality_modifier)`
2. **Life Stage Bias**: `utility * life_stage_multiplier`
3. **Boredom Tax**: `utility - (boredom * boredom_penalty_weight)`

## Affected Systems
- `StrategicIntelligenceSystem.evaluate_strategic_intent`: Should call the modifier pipeline.
- `ApplyPath.apply_generation`: Should handle boredom decay and passive personality effects? 
  Actually, boredom increase should happen during project resolution or ticking.

## Questions
- Should Boredom be per-goal-kind (e.g., 'harvesting') or per-objective-kind? 
  Probably per-goal-kind to prevent "looping" on the same activity.
