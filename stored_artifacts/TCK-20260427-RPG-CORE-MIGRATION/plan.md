---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260427-RPG-CORE-MIGRATION
artifact_type: plan
tags: [rpg, core, migration]
---

# Implementation Plan: RPG Core Migration (Phases 1-11)

## Goal
Complete the migration of RPG core logic from `src_legacy/` to `src/`, ensuring authoritative mutation, determinism, and full logic parity.

## Proposed Changes

### 1. Authoritative Interaction (Phase 3)
- **Problem**: `InteractionSystem` only supports `ResourceNode`.
- **Solution**: 
    - Update `AuthoritativeState` to ensure `ground_items` and `corpses` are properly integrated.
    - Extend `InteractionSystem.enforce` to handle `GroundItemState` and `CorpseState`.
    - Update `AuthoritativeApplyPipeline._route_interaction_intent` to recognize non-node interaction targets.

### 2. Semantic Movement (Phase 4)
- **Problem**: `MovementSystem` lacks semantic modes and `movement_modes.py` is missing.
- **Solution**:
    - Restore `src/core/movement_modes.py` with `MovementMode` Enum (Pursue, Retreat, etc.).
    - Implement `MovementSystem.resolve_semantic_move` to handle these modes.
    - Update `NavigationComponent` to include `current_mode`.

### 3. Combat Hardening (Phase 5)
- **Problem**: Reward distribution and target rejection need hardening.
- **Solution**:
    - Refine `CombatResolutionSystem.resolve_attack` to ensure rewards are distributed only on valid kills.
    - Ensure `AuthoritativeApplyPipeline` suppresses attacks on already-dead targets within the same tick.

### 4. Checklist Auditing (Phases 6-11)
- **Problem**: Unreliable `[x]` marks.
- **Solution**:
    - Systematically verify each checklist section (Town, Shop, Blacksmith, etc.) against `src_legacy`.
    - Update `logic_checklist_exhaustive.md` and `resource_v2_e2_phases.md` with truthful statuses.

## Verification Plan
- Run existing determinism tests.
- Create new parity tests for looting and movement modes.
- Run `verify_checklist.py`.
