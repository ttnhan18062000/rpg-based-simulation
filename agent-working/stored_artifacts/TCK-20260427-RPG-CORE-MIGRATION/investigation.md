---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260427-RPG-CORE-MIGRATION
artifact_type: investigation
tags: [rpg, core, migration]
---

# Investigation: RPG Core Logic Gaps (Phases 1-5)

## Overview
Detailed comparison between `src/` (V2) and `src_legacy/` to identify missing semantic laws and hardening requirements.

## Phase 1: Authoritative Mutation Boundary
- [ ] **Current State**: `ApplyPath` and `AuthoritativeApplyPipeline` exist and handle many transitions.
- [ ] **Gaps**: Some `[x]` marks in `resource_v2_e2_phases.md` might be premature. Need to verify if *any* direct mutations exist in systems.
- [ ] **Action**: Search for `entity.hp =` or similar direct assignments outside `ApplyPath`.

## Phase 3: Resource & Interaction Conservation
- [ ] **Current State**: `InteractionSystem` handles `ResourceNode` harvesting.
- [ ] **Gaps**: 
    - No support for `GroundItemState` pickup.
    - No support for `CorpseState` looting.
    - `AuthoritativeState` has the fields but they are "orphaned".
- [ ] **Action**: Extend `InteractionSystem` and `AuthoritativeApplyPipeline` to handle `ground_items` and `corpses`.

## Phase 4: Movement
- [ ] **Current State**: `MovementSystem` is a basic Manhattan step resolver.
- [ ] **Gaps**:
    - `src/core/movement_modes.py` is missing.
    - No support for "Pursue", "Retreat", "Hold", etc., in the authoritative pipeline.
- [ ] **Action**: Restore `movement_modes.py` and integrate semantic movement laws.

## Phase 5: Combat
- [ ] **Current State**: `CombatResolutionSystem` exists and handles basic damage.
- [ ] **Gaps**:
    - Death/Reward handoff needs hardening (multi-kill edge cases).
    - XP/Gold distribution needs to be strictly authoritative.
- [ ] **Action**: Verify reward laws in `CombatResolutionSystem.resolve_attack`.

## Checklist 1-5 Reconcilation
- Many items in `logic_checklist_exhaustive.md` are marked `[x]` but need verification against `src_legacy` bit-identical logic.
