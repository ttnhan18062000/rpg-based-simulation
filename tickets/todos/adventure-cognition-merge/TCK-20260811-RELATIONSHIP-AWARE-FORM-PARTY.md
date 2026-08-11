---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
phase: open
date: 2026-08-11
tags: [cognition, adventure, social]
---

# TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Title
Wire relationship-aware trust/bonds into FORM_PARTY scoring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by making FORM_PARTY route generation relationship-aware via src/systems/social_systems/ trust/relationship data instead of a flat sociability scalar. Investigation found this is the lowest-risk, most-buildable of the design's 3 signal-enrichment ideas: FORM_PARTY generation already partially uses relationship data (the nemesis block) but PartyCompositionScorer.score() never reads trust_history/bonds for the specific candidates being considered.

## Scope
- PartyCompositionScorer.score() (src/systems/social_systems/party_composition.py:105) reads the specific candidate's real trust_history/bonds (SocialComponent) in addition to role-diversity/OCEAN-compatibility
- AdventureRouteScorer's confidence_bonus / personality_bias terms (scoring.py lines 207-208, 224) for FORM_PARTY incorporate the candidate's trust_history/bonds value alongside the existing sociability scalar
- Two otherwise-identical FORM_PARTY candidate pools differing only in one candidate's trust_history value produce different comp_score/confidence for that candidate
- New regression test alongside existing test_sociability_weight_is_0_40_on_form_party_route

## Out of Scope
- Memory-informed candidates (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) and capability-estimate confidence (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) -- separate tickets
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- orthogonal but touches the same files; recommend landing after that migration settles

## Acceptance Criteria
- [ ] FORM_PARTY confidence/benefit for a specific candidate incorporates that candidate's real per-entity trust_history/bonds value
- [ ] Two otherwise-identical FORM_PARTY candidate pools differing only in one candidate's trust_history value produce different comp_score/confidence for that candidate
- [ ] Regression test added alongside existing test_sociability_weight_is_0_40_on_form_party_route
- [ ] FORM_PARTY sociability weight of 0.40 (docs/mechanics/04_strategic_cognition.md §6.4-6.6) remains bit-identical for the existing weighted term; new trust/bonds term is additive, not a replacement

## Related Tickets
- TCK-20260628-E41F-PARTY-SCORER
- TCK-20260628-E43G-NEMESIS-RELATION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/generator.py
- src/domains/adventure/scoring.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/party_composition.py
- src/core/models/social.py

## Assumptions / Open Questions
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer/Generator 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- New trust/bonds read must stay the entity's own subjective belief, per scoring.py's documented information-opacity boundary, not omniscient world truth
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
