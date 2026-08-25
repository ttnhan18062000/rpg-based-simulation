---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-AFFECTION-CONTRACT-GATE
phase: open
date: 2026-08-24
tags: [social, information]
---

# TCK-20260824-AFFECTION-CONTRACT-GATE

## Title
Build a Shared Affection-Threshold Gate for Team-Up/Trade/Paid-Information

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants Team-Up, Trade, and Paid-Information actions gated on affection, built as a shared appraise_contract() threshold-gate helper -- a 6-idea, 3-milestone cluster all converging on the identical formula.

## Scope
- Build a shared threshold-gate helper accepting a ContractKind and returning (ContractStatus, ReasonCode, terms), reusing the existing bond.sentiment-priority-else-trust_history formula already implemented in SocialAppraisalSystem.appraise_contract()
- Route Team-Up, Trade, and Paid-Information each through the shared helper, mirroring _appraise_recruitment's existing hard-cancel pattern
- Decide whether Trade reuses the existing declared-but-unhandled ContractKind.MERCHANT value or needs a new kind; add whatever new ContractKind values Team-Up/Paid-Information need -- no fallthrough to default CANCELLED/UNKNOWN
- Gate PaidInformationTransactionSystem.enforce()'s ResourceTransferIntent on the shared helper's outcome (currently emits unconditionally, zero check today)
- Decide whether to reuse sentiment as-is for the 'affection' concept, or introduce a new named field -- no 'affection' field exists anywhere in src/ today
- Update docs/parity_ledger/social_narrative.yaml's existing verified appraise_contract() entries to reflect the change

## Out of Scope
- M6 ideas 39/40 (Conversation-adjacent consumers) -- this ticket must document whether it builds narrowly for the 3 named consumers or anticipates M6, but does not implement M6's consumers
- Idea 25's separate trust ledger (PP-04-adjacent), explicitly excluded from this cluster per the atlas

## Acceptance Criteria
- [ ] The shared threshold-gate helper accepts a ContractKind and returns (ContractStatus, ReasonCode, terms) using the existing bond.sentiment-priority-else-trust_history formula
- [ ] Team-Up/Trade/Paid-Information each route through the shared helper, mirroring _appraise_recruitment's existing hard-cancel pattern
- [ ] No fallthrough to default CANCELLED/UNKNOWN for any of the 3 consumers
- [ ] PaidInformationTransactionSystem.enforce() gates its ResourceTransferIntent on the shared helper's outcome

## Related Tickets
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
- TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/social_narrative.yaml
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md
- docs/brainstorm/rpg_feature_atlas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/appraisal.py
- src/engine/domain/core_actions.py
- src/core/strategic.py
- src/core/models/social.py
- src/engine/pipeline_phases/paid_information.py
- src/systems/social_systems/party_composition.py
- src/ai/goals/social_contract_scorer.py

## Assumptions / Open Questions
- Whether to reuse sentiment as-is (cheapest) or introduce a new named 'affection' field (more state, no current consumer justifies it alone) needs an explicit decision
- Whether to build narrowly for the 3 named consumers now or anticipate M6's ideas 39/40 is an unresolved question in the M1 epic's own Open Questions section
- Team-Up has no existing action/contract wiring anywhere (no TEAM_UP kind, no handler) -- this is new mechanism work, unlike Paid-Information which retrofits a live pipeline phase
- `layer: systems` chosen because the primary deliverable (shared appraise_contract() helper) lives in src/systems/social_systems/; no dedicated "social" layer is registered in registries/layer_registry.jsonl

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
