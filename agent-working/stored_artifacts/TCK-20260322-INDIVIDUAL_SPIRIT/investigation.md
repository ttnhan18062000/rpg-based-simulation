---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260322-INDIVIDUAL_SPIRIT
artifact_type: investigation
tags: [individual_spirit]
---

# Investigation: Milestone 10 - The Individual Spirit

## Findings
- **Cognitive Pipeline**: `AIContext` and `Perception` are the primary places for decision-making logic.
- **Combat Resolution**: `CombatAction` handles damage and death logic.
- **Persistence**: `MindAspect` is part of the `Entity` model, which is snapshotted.
- **Refinement**: `find_region_at` is the correct way to map coordinates to regions.

## Risks
- **Mood Recovers (Implicitly)**: The code doesn't have an explicit mood recovery tick yet, but standard `MindAspect` logic handles `last_killer_id`.
- **Target Loops**: Prioritizing nemeses might lead to "target locking" if not careful (addressed by only prioritizing if they are within range).
- **Death Memory**: Needs to be careful with entity IDs if entities respawn or are reused (using unique IDs prevents this).
