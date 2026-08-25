---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-RELATIONSHIP-ROLE-FIELD
phase: open
date: 2026-08-24
tags: [social]
---

# TCK-20260824-RELATIONSHIP-ROLE-FIELD

## Title
Add Relationship Roles Alongside Relationship Scores, with a Real Consumer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
SocialBond has exactly three fields today; the author wants a role concept added as an additive field. A real risk (from the Merit Scorecard) is that a label with no consumer is invisible -- this codebase has a track record of adding fields nothing ever reads. The author wants the consumer scoped alongside the field, not as a follow-up.

## Scope
- Add an additive role field (enum, NEUTRAL/UNSET default) to SocialBond, named distinctly from the existing unrelated PartyRole enum (party_composition.py's TANK/HEALER/DPS/SUPPORT combat role) -- e.g. RelationshipRole/BondRole
- Extend SocialBondUpdate/RelationshipService.process_update() so role can only be set through the authoritative SocialUpdate path (per SOC-217)
- Wire one real consumer (PartyCompositionScorer or SocialAppraisalSystem.appraise_contract()) to produce a measurably different score for two otherwise-identical bonds differing only in role, with a new test asserting this using fixed familiarity/sentiment
- Add a new SOC-### parity_ledger entry and a docs/mechanics/04_strategic_cognition.md section documenting the formula -- not schema-only with docs deferred

## Out of Scope
- Wiring additional consumers beyond the one chosen for this ticket's AC (PartnerFitEvaluator and others noted as explicit out-of-scope follow-ons)
- Deepening PartnerFitEvaluator's existing pre-existing direct read of social.bonds -- not a new violation to fix here, and not license to add further coupling

## Acceptance Criteria
- [ ] SocialBond gains an additive role field (enum, NEUTRAL/UNSET default); existing construction/serialization continues to work unmodified when omitted
- [ ] SocialBondUpdate/RelationshipService.process_update() support setting role only through the authoritative path
- [ ] A real consumer produces a measurably different score for two otherwise-identical bonds differing only in role, asserted by a new test with fixed familiarity/sentiment
- [ ] docs/mechanics/04_strategic_cognition.md and social_narrative.yaml gain a new SOC-### entry documenting the formula

## Related Tickets
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/social_systems_contract.md
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/models/social.py
- src/core/updates.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/party_composition.py
- src/systems/social_systems/appraisal.py
- src/domains/cooperation/evaluators.py
- src/systems/world_systems/groups.py
- src/engine/tactical.py
- src/engine/combat.py
- src/core/state.py
- src/domains/adventure/generator.py

## Assumptions / Open Questions
- Which role values are wanted, and which single consumer to wire for initial AC, is a real design decision this ticket must make explicit
- The new field/enum name must avoid collision with the existing unrelated PartyRole enum, and must be reconciled against the existing but distinct nemesis_ids concept if a 'rival' role value is added

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
