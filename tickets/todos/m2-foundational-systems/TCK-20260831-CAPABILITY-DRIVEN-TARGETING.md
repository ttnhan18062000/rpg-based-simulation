---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-CAPABILITY-DRIVEN-TARGETING
phase: open
date: 2026-08-31
tags: [cognition, combat]
---

# TCK-20260831-CAPABILITY-DRIVEN-TARGETING

## Title
Let subjective capability estimates drive tactical target selection

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Let subjective capability drive tactical target selection instead of pure group-bias/HP/distance/trust scoring. TacticalDecisionSystem.target_score() has zero CapabilityEstimateService reads today, even though CapabilityContext.for_combat() already exists shaped exactly for this consumer, and a directly-reusable precedent (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) already established the accepted ad-hoc call-site-local pattern for working around the still-unpopulated upstream prerequisite.

## Scope
- Wire CapabilityContext.for_combat(enemy_ids, enemy_data) into TacticalDecisionSystem.target_score() (src/engine/tactical.py:394-426) so scoring reflects CapabilityEstimateService.estimate(...).combat.enemy_type for hostiles mapped into combat_enemies.
- Reuse the ad-hoc call-site-local CapabilityContext construction pattern from TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING (accepted per docs/mechanics/04_strategic_cognition.md §6.12, STRAT-227) rather than fixing the upstream SelfModelUpdatePhase prerequisite gap.
- Explicitly disclose that capability_context is still never populated in production (src/cognition/self_model_phase.py) as a known/accepted limitation, resolved locally per the precedent.
- Keep target_score() strictly read-only — no write-back into entity.self_model.

## Out of Scope
- Fixing SelfModelUpdatePhase's capability_context production-population gap upstream — out of scope, same as the precedent ticket.
- Any change to COMB-254's post-sort legality filter behavior.

## Acceptance Criteria
- [ ] For a hostile mapped into CapabilityContext.combat_enemies, target_score()'s priority reflects a real CapabilityEstimateService.estimate(...).combat.enemy_type value instead of purely HP/distance/trust.
- [ ] The capability_context-never-populated prerequisite is explicitly disclosed and resolved via an ad-hoc call-site-local CapabilityContext inside tactical.py, mirroring the precedent ticket.
- [ ] target_score() stays read-only — no write-back into entity.self_model, existing CapabilityEstimateService unit tests pass unchanged.
- [ ] COMB-254's post-sort legality filter still runs unchanged after the re-scored sort.

## Related Tickets
- TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py
- src/cognition/capability_estimate.py
- src/cognition/self_model_phase.py

## Assumptions / Open Questions
- The capability_context-never-populated-in-production prerequisite gap persists and is intentionally worked around here, not fixed upstream — matches the precedent ticket's accepted pattern.
- Existing CapabilityEstimateService unit tests must continue to pass unchanged.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
