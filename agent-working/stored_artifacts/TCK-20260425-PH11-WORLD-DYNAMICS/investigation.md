---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260425-PH11-WORLD-DYNAMICS
artifact_type: investigation
tags: [ph11, world, dynamics]
---

# Phase 10 World Dynamics Investigation

## Research Findings
- `RegionState` in `src/core/state.py` is the authoritative container for regional state.
- `ApplyPath.apply_generation` in `src/engine/apply.py` merges regional updates from `StateUpdate.world_updates`.
- `LegalityServiceV2` in `src/engine/legality.py` provides a centralized check for action validity.

## Technical Approach
1. Expand `RegionState` with `kind`, `weather`, and `active_modifiers`.
2. Expand `WorldUpdate` to handle these new fields.
3. Create `EnvironmentService` for stat impacts.
4. Create `TransformationService` for kind shifting.
5. Fix transformation priority by sorting by requirement count (most complex first).
