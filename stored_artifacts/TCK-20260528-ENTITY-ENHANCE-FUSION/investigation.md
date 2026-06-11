---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260528-ENTITY-ENHANCE-FUSION
artifact_type: investigation
tags: [entity, enhance, fusion]
---

# Investigation Notes - RPG Cognitive & World Loop Fusion

## 1. Duplicate Test Filename Fix
We successfully identified and resolved the duplicate `test_social_contracts.py` conflict by renaming:
- `tests/unit/strategic/test_social_contracts.py` -> `tests/unit/strategic/test_strategic_social_contracts.py`.
This removes the `import-mismatch` error during full `pytest` collection, enabling trustworthy CI signals.

## 2. Spatial Combat Engagement Capping
In the original Phase 4 implementation, combat target consideration evaluates all pairs of nearby entities. Under 100+ entities, this degrades performance to ~11.2ms (violating the 5ms budget).
**Resolution Strategy**:
We will modify the target candidate selection in `CombatEngagementPhase` or `CombatEngagementService` to use a spatial radius lookup (re-using the optimization spatial index where available or a simple Euclidean filter capped to the `N` closest hosts, e.g., max 8 targets).

## 3. Knowledge Assimilation Persistence
The `InformationBeliefPhase` processed facts but was flagged in `entity_enhance_fix.md` as not persisting them properly back into the authoritative state because components were reattached late or incorrectly.
We will inspect how `InformationBeliefPhase` constructs `StrategicUpdate` or `PropertyUpdate` and ensure that `self_model.knowledge` updates are stored inside the `EntityUpdate` and successfully committed by the `ApplyPath`.
