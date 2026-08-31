---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260831-TRUST-GATED-TEACHING
phase: open
date: 2026-08-31
tags: [social, economy]
---

# TCK-20260831-TRUST-GATED-TEACHING

## Title
Gate the teach/train action on trust instead of gold alone

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Teach on trust, not gold. Investigation found execute_train() is currently solo/gold-gated (flat TRAIN_COST=50) with no target/teacher entity concept at all, so this is new mechanism work — adding a second party to the action — not the one-line gold-to-trust threshold swap the idea's title implies. M1 idea 13's shared trust-gate helper is reusable for the gating logic.

## Scope
- Extend the teach/train action to accept both a teacher entity_id and a target entity_id (currently execute_train() has no target/teacher entity concept at all).
- Gate the action on trust between teacher and target using SocialAppraisalSystem.appraise_contract()'s shared hard-cancel threshold (trust_score<0.2 or bond.sentiment<-0.8).
- Make and state an explicit decision, in Scope, on whether trust replaces the 50-gold TRAIN_COST entirely or gates alongside it — this changes existing economy behavior and may touch Mechanics Bible Ch3 (economic conservation).
- Emit a domain-specific IdentityUpdate(recipes_learned=[skill_id]) directly (not a shared generic mutation) when trust clears.
- Add a test file covering execute_train — none currently exists.

## Out of Scope
- Widening ContractService.get_project_mapping()'s tier-5 goal materialization coverage, even if a new ContractKind.TEACH is introduced — per the AFFECTION-CONTRACT-GATE precedent's own anti-drift note.

## Acceptance Criteria
- [ ] A teach action exists accepting both teacher entity_id and target entity_id, gated on trust between them.
- [ ] When trust is below the shared hard-cancel threshold (trust_score<0.2 or bond.sentiment<-0.8), the action is refused and emits no IdentityUpdate(recipes_learned).
- [ ] When trust clears, the action emits its own domain-specific IdentityUpdate(recipes_learned=[skill_id]) directly, not a shared generic mutation.
- [ ] The ticket makes an explicit decision on gold-replacement-vs-additional-gate and states it in Scope, not left ambiguous.

## Related Tickets
- TCK-20260824-AFFECTION-CONTRACT-GATE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/domain/core_actions.py
- src/systems/social_systems/appraisal.py
- src/core/strategic.py
- src/systems/social_systems/relationships.py

## Assumptions / Open Questions
- Open design question, unresolved: does teaching replace the 50-gold TRAIN_COST entirely or add trust as an additional gate alongside gold — this changes existing economy behavior and needs an explicit planner decision.
- No existing test file covers execute_train at all.
- `layer: economy` chosen because the ticket's central open decision (TRAIN_COST gold-replacement-vs-additional-gate) is an economic-conservation question and no `social` layer is registered; `systems` was the runner-up.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
