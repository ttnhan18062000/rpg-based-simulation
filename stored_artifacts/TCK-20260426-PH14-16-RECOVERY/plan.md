---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-PH14-16-RECOVERY
artifact_type: plan
tags: [ph14, recovery]
---

# Plan: RPG-Core Logic Recovery (Phases 14-16)

## Goal
Achieve 100% parity with legacy RPG-core "Must-Have" features by recovering Multi-Attacker OA, Social Bonds, and AoE mechanics.

## Proposed Changes

### Phase 14: Multi-Attacker OA
- [x] Refactor `LegalityServiceV2` to return sorted engaged hostile IDs.
- [x] Update `MovementSystem` to collect all hostiles and call multi-resolution.
- [x] Implement `resolve_multi_attack` in `CombatResolutionSystem`.

### Phase 15: First-Class Social Bonds
- [x] Add `SocialBond` dataclass to `src/core/state.py`.
- [x] Update `SocialComponent` with `bonds` registry.
- [x] Refactor `SocialAppraisalSystem` to track Familiarity and Sentiment.
- [x] Integrate bonds into recruitment cost and evaluation.

### Phase 16: Advanced Combat & AoE
- [x] Add `verify_aoe_legality` to `LegalityServiceV2`.
- [x] Implement `resolve_aoe_attack` in `CombatResolutionSystem`.
- [x] Implement pre-loop splash damage resolution in `ApplyPath`.
- [x] Fix primary damage application in `resolve_aoe_attack`.

## Verification Plan
- `tests/parity/test_multi_oa_parity.py`
- `tests/social/test_social_bonds.py`
- `tests/combat/test_aoe_splash.py`
- Full suite regression test.
