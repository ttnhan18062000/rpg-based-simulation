---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260407-PHASE1-DS
artifact_type: investigation
tags: [phase1, ds]
---

# Investigation: Phase 1 Behavioral Realism

## Root Cause Analysis (AOA Regression)
- **Problem**: AI was crashing with `AttributeError: 'mappingproxy' object has no attribute 'pos'`.
- **Cause**: `EnvironmentSystem._update_entity_memory` was overwriting typed `BeliefRecord` with raw `dict` objects. When frozen, these became `mappingproxy` dicts.
- **Fix**: Removed legacy `EnvironmentSystem` logic. Entity perception is now handled exclusively by `BeliefService.refresh_belief_from_observation` within the AIBrain sensory phase.

## Design Decisions
- **Pure-Functional BeliefService**: Every belief refresh returns a NEW record. The caller is responsible for updating the entity's memory. This prevents mutation of frozen snapshot data.
- **Read-Only Bond Lookups**: Added `get_bond_or_none()` to `SocialRegistry` to avoid lazy-creation mutations on frozen snapshots.

## Conflict Resolution
- `TCK-20260407-PHASE1-PERSONALITY.md` covered the initial model merge.
- `TCK-20260407-PHASE1-DS.md` (this ticket) refined the implementation to handle AOA isolation and strict perception rules.

## Final State
- Behavioral divergence is stable.
- AI uses subjective beliefs for flee/hunt decisions.
- Memory corruption from legacy systems is eliminated.
