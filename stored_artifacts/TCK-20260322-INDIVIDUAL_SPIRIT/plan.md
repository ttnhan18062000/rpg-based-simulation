---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260322-INDIVIDUAL_SPIRIT
artifact_type: plan
tags: [individual_spirit]
---

# Plan: Milestone 10 - The Individual Spirit

## Overview
Implement persistent AI personality (grudges, mood, memory) and integrate it into combat, movement, and exploration logic.

## Steps
1.  **Aspect Enhancement**: Add `grudges`, `mood`, `memory_locations` to `MindAspect`.
2.  **Combat Integration**:
    *   `CombatAction` updates `grudges` on hit.
    *   `CombatAction` records regional trauma on death and sets `last_killer_id`.
3.  **AI Logic Adjustments**:
    *   `AIContext.nearest_enemy` prioritizes targets with high grudges (Nemeses).
    *   `should_flee` adjusted based on `mood`.
4.  **Spatial Percpetion Bias**:
    *   `find_frontier_target` penalizes regions with negative memory.

## Affected Files
- `src/core/aspects/mind.py`
- `src/actions/combat.py`
- `src/ai/states.py`
- `src/ai/perception.py`

## Verification
- Unit tests for each of the 4 features.
- Manual verification of frontier bias.
