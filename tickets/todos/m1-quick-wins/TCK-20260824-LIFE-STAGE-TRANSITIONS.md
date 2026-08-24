---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-LIFE-STAGE-TRANSITIONS
phase: open
date: 2026-08-24
tags: [cognition]
---

# TCK-20260824-LIFE-STAGE-TRANSITIONS

## Title
Implement Life Stage Transitions (Life Stages & Rites of Passage)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
LifeStageService.get_goal_multipliers() already runs unflagged, consumes identity.life_stage, but nothing ever writes that field -- no life_stage_set field exists on IdentityUpdate today. The author wants a new typed field added plus the apply-path work to make it real.

## Scope
- Add IdentityUpdate.life_stage_set: Optional[LifeStage]=None following the exact typed-field pattern of role_set/faction_set/evolution_level_set (not IdentityPatch's generic property_updates dict)
- Implement IdentityPatch.apply() to apply life_stage_set into IdentityComponent.life_stage, and verify ApplyPath._fast_replace_identity does not silently drop it on the fast path
- Implement a concrete age-based transition trigger that fires deterministically; add a test asserting identity.life_stage flips at the defined boundary
- Explicitly resolve (or explicitly defer with rationale) whether the age-based trigger reuses/aligns with cohort.py's get_age_bracket() thresholds (young/adult/elder string brackets) versus the separate LifeStage(str,Enum) (CHILD/ADULT/ELDER) -- the roadmap itself flags this as a blocking duplicate-representation question that must be settled before implementation
- Decide whether compute_elder_attribute_update() (cohort.py, currently a second independent orphan 'elder' stat-penalty mechanism with zero callers) should be wired to the same age signal or remain deliberately separate from LifeStageService's ELDER goal multipliers

## Out of Scope
- The cohort-level aggregate demographics system tested by test_demographics.py -- this ticket concerns per-entity IdentityComponent.life_stage only

## Acceptance Criteria
- [ ] IdentityUpdate gains life_stage_set: Optional[LifeStage]=None following the role_set/faction_set precedent exactly
- [ ] IdentityPatch.apply() applies life_stage_set into IdentityComponent.life_stage, and ApplyPath._fast_replace_identity is verified not to silently drop it on the fast path
- [ ] A concrete age-based transition trigger fires deterministically; a test asserts identity.life_stage flips at the defined boundary
- [ ] The investigation/plan explicitly resolves (or explicitly defers with rationale) whether the trigger reuses/aligns with cohort.py's get_age_bracket() thresholds

## Related Tickets
None.

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/ai/life_stage.py
- src/ai/score_modifiers.py
- src/engine/patches.py
- src/engine/apply.py
- src/domains/demographics/cohort.py
- src/core/builder.py

## Assumptions / Open Questions
- The duplicate-representation question (LifeStage enum vs. get_age_bracket() string tiers) must be settled before implementation per the roadmap's own explicit instruction, not discovered mid-ticket
- Whether compute_elder_attribute_update() should be wired to the same age signal as this trigger, or remain a deliberately separate mechanism, is an open decision this ticket must make explicit
- layer set to `strategy` (AI goal hierarchy / bounded cognition) since the driving consumer is LifeStageService.get_goal_multipliers(); the change also touches core/engine apply-path files, but no combined layer exists in the registry

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
