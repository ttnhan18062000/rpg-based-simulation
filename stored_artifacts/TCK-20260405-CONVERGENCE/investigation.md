---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260405-CONVERGENCE
artifact_type: investigation
tags: [convergence]
---

# AOA Convergence Investigation (TCK-20260405-CONVERGENCE)

## Findings
The Aspect-Oriented Architecture (AOA) pivot introduced ~191 test failures due to legacy attribute access patterns and structural changes:
1. **Attributes**: `entity.stats` is deprecated. Authoritative state resides in modular aspects (`combat`, `progression`, `spatial`).
2. **AI Goals**: Goal identity must use `GoalType` enums instead of literals.
3. **Quests**: Progression-based gold/rewards must use `ProgressionAspect`.
4. **Perception**: `attention_pool` and `familiarity` moved to `MindAspect.perception`.
5. **Spatial**: `difficulty_tier` must be propagated to `SpatialAspect` for scaling logic to pass.

## Existing Patterns to Reuse
- **Systematic aspect lookup**: `entity.combat`, `entity.progression`, etc.
- **ActionSystem**: Authoritative state transitions are applied via `ActionSystem.apply_action_state_transitions`.

## Risks & Assumptions
- **Risk**: Performance overhead of Pydantic model copies in high-entity counts.
- **Assumption**: `DISABLE_KAFKA=1` is required for local E2E verification.
