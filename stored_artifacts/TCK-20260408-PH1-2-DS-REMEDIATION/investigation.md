---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260408-PH1-2-DS-REMEDIATION
artifact_type: investigation
tags: [ph1, ds, remediation]
---

# Investigation for TCK-20260408-PH1-2-DS-REMEDIATION

## Findings

### 1. Reputation Split
- **Source A:** `src/core/models/reputation.py` defines a `ReputationProfile`. This is used by `Entity` directly.
- **Source B:** `src/core/models/life_events.py` also defines a `ReputationProfile`. This is used by `IdentityAspect`.
- **Conflict:** `ActionSystem` and `ReputationService` may be updating one while the UI/API reads from another (or both).
- **Resolution:** Delete `src/core/models/reputation.py`. Move all relevant logic to `src/core/models/life_events.py` (or a unified location). Ensure `IdentityAspect` is the single owner.

### 2. Inspection Serialization
- **Issue:** `EntityPresenter.to_full_schema` (line 171) does `entity_memory=list(mind.perception.entity_memory)`, which returns keys.
- **Requirement:** It should serialize `BeliefRecord` objects using a proper schema (`BeliefRecordSchema`).

### 3. AIPresenter Explanation Logic
- **Issue:** `AIPresenter.get_explanation` (line 38) does `d = entity.spatial.pos.manhattan(pos)` where `pos` is a `BeliefRecord`.
- **Requirement:** Change to `d = entity.spatial.pos.manhattan(belief.pos)`.

### 4. ActionSystem Gossip Ordering
- **Issue:** `_process_proximity_gossip` and `_process_social_interpretation` append updates to `all_updates`, but this happens *after* `_apply_updates` has already run for that entity in `apply_action_state_transitions`.
- **Requirement:** Run social interpretation and gossip *before* final update application, or run a second application pass. Given AOA constraints, collecting all updates and then applying them once is better.

### 5. Archetype Seeding
- **Issue:** `IdentityAspect.archetype` defaults to `BALANCED`. Builders often omit explicit assignment.
- **Requirement:** Update entity formation/builders to enforce archetype diversity (either explicitly passed or randomly sampled from weighted distribution).

### 6. Legacy Personality
- **Issue:** `src/core/logic/personality.py` uses OCEAN traits which conflict with the new RPG-axes personality in `MindAspect`.
- **Requirement:** Delete or quarantine the OCEAN-based module.

## Assumptions
- Removing `src/core/models/reputation.py` won't break legacy non-AOA components if we update references.
- `BeliefRecord` contains enough info for the UI.

## Risks
- Merging reputation models might cause Pydantic validation errors if schemas differ slightly.
- Changing `ActionSystem` ordering might have subtle side-effects on event salience if not careful.
