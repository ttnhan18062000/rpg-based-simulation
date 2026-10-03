---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-ENUM-DRIFT
artifact_type: plan
tags: [cog, enum, drift]
---

# Implementation Plan: TCK-20260527-COG-ENUM-DRIFT

## Goal
Eliminate enum and string drift across strategic cognition, goal scoring, and event emissions.

## Proposed Changes

### 1. `src/core/strategic.py`
- Add canonical `GoalKind(str, Enum)` class:
  ```python
  class GoalKind(str, Enum):
      HARVESTING = "harvesting"
      FATIGUE = "fatigue"
      HUNGER = "hunger"
      SOCIAL = "social"
      TOWN_RETURN = "town_return"
      COMBAT_ENGAGE = "combat_engage"
      COMBAT_RETREAT = "combat_retreat"
      RECOVER = "recover"
      RESOLVE_BLOCKER = "resolve_blocker"
  ```

### 2. `src/ai/goals/__init__.py` and Scorers
- Update `GoalRegistry` registrations to use `GoalKind` constants.
- Update scorers in `src/ai/goals/scorers.py` to return `GoalKind` enums.
- Update `GoalRegistry` in `src/ai/goals/base.py` to assert that registered keys must be instances or values of `GoalKind`.

### 3. Event / Serialization Validation
- Add check/assertion in `StrategicCognitionEvent` or state-loading system to validate all strategic kind enums are valid.
