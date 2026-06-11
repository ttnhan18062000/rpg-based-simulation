---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-GOAL-REGISTRY
artifact_type: investigation
tags: [cog, goal, registry]
---

# Investigation - TCK-20260527-COG-GOAL-REGISTRY

## Objectives
- Understand how personality (bravery, greed, sociability, industry) can be utilized to score goals in `GoalRegistry`.
- Outline implementation of 4 new goal scorers: `combat_engage`, `combat_retreat`, `recover`, and `resolve_blocker`.
- Ensure deterministic tie-breaking of goal scores to prevent oscillation.
- Verify how goal scores translate into strategic projects and tactical actions downstream.
- Support observability logs to trace selected goals and rejected alternatives.

## Core Mechanics Investigation

### 1. Personality Traits
- Trait values exist in `entity.identity.personality` which is a `PersonalityComponent` consisting of:
  - `greed`: float
  - `bravery`: float
  - `sociability`: float
  - `industry`: float
- We should use these values to scale/adjust the utilities calculated in goal scorers.

### 2. Goal Scores & Project Transition
- Downstream strategic intelligence loops evaluate goal scores returned from `GoalRegistry.get_all_scores()`.
- The highest utility score (>= 20.0) with a valid target is selected to become the `current_project_id`.
- The project kind matches the goal kind (e.g. `"combat_engage"`, `"combat_retreat"`, `"recover"`, `"resolve_blocker"`).

### 3. New Goal Scorers Design

#### A. `combat_engage` Scorer
- Kind: `combat_engage`
- Condition: Hostiles detected within neighbor view (radius ~10).
- Calculation:
  - Base utility = 40.0
  - Bravery bonus = `entity.identity.personality.bravery * 40.0`
  - Stamina bonus = `entity.stamina.value / 2.0` (needs energy to fight)
  - Target: The nearest hostile entity ID and position.
- Downstream Behavior: Generates a project to fight or move to the hostile target.

#### B. `combat_retreat` Scorer
- Kind: `combat_retreat`
- Condition: Low HP, panic, or outnumbered.
- Calculation:
  - Base utility = 0.0 if `hp_ratio >= 0.5` else `(1.0 - hp_ratio) * 100.0`
  - Panic influence: Add panic level from `AppraisalSystem.evaluate_emotional_state` times 50.0.
  - Bravery penalty: Subtract `entity.identity.personality.bravery * 30.0`.
  - Target: Town center.

#### C. `recover` Scorer
- Kind: `recover`
- Condition: Wounded or low HP/stamina, but not actively in immediate high-danger panic combat (otherwise retreat/fight takes precedence).
- Calculation:
  - Utility based on missing HP: `(1.0 - hp_ratio) * 80.0`
  - Utility based on stamina debt: `(max_stamina - stamina) / max_stamina * 40.0`
  - Target: Town Inn (nearest building of type `"inn"` or town center).

#### D. `resolve_blocker` Scorer
- Kind: `resolve_blocker`
- Condition: Unresolved blocker in entity strategic state.
- Calculation:
  - Utility: `80.0` if active blockers are present (to prioritize resolving blockers over standard harvesting).
  - Target: Blocker subject/coordinates or a matching lead location.

### 4. Deterministic Tie-Breaking
- Goal scores are sorted by utility descending. In case of ties, we need a stable secondary key.
- Sorting should sort by `utility` descending, then by `kind` ascending to guarantee determinism.

### 5. Observability
- When projects are chosen, we want to log the chosen goal and rejected alternatives.
