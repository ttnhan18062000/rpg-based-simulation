# Test Plan: Phase 1 Behavioral Realism

## Existing Tests to Run
- `pytest tests/unit/ai/`: Ensure current AI baseline still works (despite OCEAN/Motive transition).
- `pytest tests/api/test_introspection_api.py`: Ensure current entity inspection doesn't break.

## New Tests to Add
### Behavioral Divergence
- `tests/unit/ai/test_personality_divergence.py`:
  - Scenario: A "Greedy" entity and a "Cautious" entity see a loot chest guarded by a strong mob.
  - Expected: Cautious entity flees/avoids; Greedy entity attempts to loot or approaches.
  - Scenario: Two entities with different "Aggression" levels see a weak mob.
  - Expected: Higher aggression entity attacks; Lower aggression entity might wander or wait.

### Belief System
- `tests/unit/ai/test_belief_system.py`:
  - Test belief creation on first sight.
  - Test confidence increase on subsequent sights.
  - Test stale tick increment and confidence decay when target is out of sight.
  - Test belief-based decision: AI chooses to FLEE from a "High Threat" belief even if the target is actually low HP (but hasn't been seen recently).

### Inspection Schema
- `tests/api/test_phase1_inspection.py`:
  - Assert that `PersonalityProfile` and `PersonalMotive` list are present in the entity payload.
  - Assert that `entity_memory` uses the new `BeliefRecord` structure.

## Core Scenarios
1. **The Brave Hero**: Hero with high "Loyalty" and low "Caution" stays to defend an ally even when at low HP.
2. **The Smart Coward**: Mob with high "Caution" avoids the player after seeing them kill a nearby ally (high threat estimate).
3. **The Persistent Loot**: Scavenger with high "Greed" keeps returning to a loot source even after being attacked.

## Regression Surface
- AI "Locked" states (Combat/Flee).
- Pydantic model serialization/rebuild.
- Entity generation in `generator.py`.
