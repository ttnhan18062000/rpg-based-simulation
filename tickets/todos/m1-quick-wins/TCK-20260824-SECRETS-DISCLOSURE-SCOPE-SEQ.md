---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
phase: open
date: 2026-08-24
tags: [information, feature-flags]
---

# TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Title
Scope Secrets, Confidence & Selective Disclosure, Sequenced After Belief Assimilation Goes Live

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This idea extends the Information Sourcing/Trust system almost exactly, but that whole system is flag-gated OFF (ENABLE_BELIEF_ASSIMILATION-adjacent) with a documented trap where flipping the flag alone activates a phase with nothing to process. The author wants this ticket scoped now, sequenced after whatever ticket gets that system live.

## Scope
- Scope schema extensions for secrecy/confidence-tier metadata and selective-disclosure logic, extending the Information Sourcing/Trust system (src/domains/information/)
- Land scope/design artifacts only -- no implementation until ENABLE_BELIEF_ASSIMILATION is confirmed live by TCK-20260824-ROLLOUT-FLAG-DECISIONS' flag decision
- Name TCK-20260824-ROLLOUT-FLAG-DECISIONS as a blocking dependency in Related Tickets, with SEQUENCE.md placing this strictly after it
- State whether any DECEPTIVE_DETECTED wiring reuses trust.py's existing delta (-0.25, currently zero callers) or needs a new writer
- Document that idea 13/C14's SocialBond.sentiment ledger and this concern's SourceTrustEntry/source_trust ledger are structurally separate, with no shared implementation

## Out of Scope
- Any implementation before C1's flag decision lands and actually activates the system generally (not just per-world compile-time seeding, which today only populates Branch A for the urban_political profile)
- Idea 12's flag-free alternative path (wiring BeliefContradictionService into an always-on strategic_intelligence phase, bypassing the flag) -- if C1 or a related ticket takes that path instead, this ticket's sequencing premise needs re-evaluation

## Acceptance Criteria
- [ ] Ticket scope is limited to design/plan artifacts (schema extension for secrecy/confidence-tier metadata, selective-disclosure logic) -- no implementation lands until ENABLE_BELIEF_ASSIMILATION is confirmed live by C1's flag decision
- [ ] Related Tickets explicitly names C1's resulting ticket ID as a blocking dependency, and SEQUENCE.md places this strictly after it
- [ ] Any DECEPTIVE_DETECTED wiring states whether it reuses trust.py's existing delta or needs a new writer
- [ ] Ticket documents that SocialBond.sentiment (C14) and SourceTrustEntry/source_trust are structurally separate ledgers with no shared implementation

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
- TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
- TCK-20260817-HOTFIX-BELIEF-ASSIMILATED-TESTS-BYPASS-SHADOW-SHAPERS
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (blocking dependency -- this ticket must not be scheduled for implementation before C1's ENABLE_BELIEF_ASSIMILATION decision lands)
- TCK-20260824-AFFECTION-CONTRACT-GATE

## Related Docs
- docs/audits/D19_domain_phase_inventory.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/information/schema.py
- src/domains/information/trust.py
- src/domains/information/contradiction.py
- src/domains/information/phase.py
- src/domains/information/router.py
- src/domains/information/assimilation.py
- src/core/strategic.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Hard sequencing dependency on TCK-20260824-ROLLOUT-FLAG-DECISIONS (C1) -- must not be scheduled for implementation before C1's ENABLE_BELIEF_ASSIMILATION decision lands and actually activates the system generally
- What "system live" precisely means (flag ON alone vs. a generalized non-compile-time-seed writer for Branch A) needs precise definition before real work starts
- If C1 or a related ticket takes idea 12's flag-free alternative path instead, this ticket's sequencing premise needs re-evaluation
- `layer: strategy` chosen because the Information Sourcing/Trust system implements knowledge management/perception within strategic cognition (Mechanics Bible ch04); no `information`-specific layer is registered in `registries/layer_registry.jsonl` as of this ticket's creation

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
