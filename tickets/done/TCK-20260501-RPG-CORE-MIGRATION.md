---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260501-RPG-CORE-MIGRATION
phase: done
date: 2026-05-01
tags: [rpg, core, migration]
---

# TCK-20260501-RPG-CORE-MIGRATION

## Title
Migrating Phase 7 (Social Contract) and Phase 6 (Strategic Cognition) Legacy Logic

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the legacy logic for Phases 7 and 6 into the authoritative V2 engine, ensuring architectural parity and validating with migrated legacy tests.

## Scope
- **Phase 7: Social Contract Lifecycle**:
    - Offer creation and appraisal (incorporating trust, risk, and greed).
    - Party formation and shared objective propagation.
    - Contract resolution (success, failure, betrayal) with social consequences.
    - Negotiation lifecycle (counters and expiry).
- **Phase 6: Strategic Cognition Lifecycle**:
    - Strategic memory (failed lead suppression).
    - Project abandonment after repeated failures.
    - Enhanced blocker inference (tool requirements, teammate requirements).

## Out of Scope
- Visual UI for social contracts.
- Complex dialogue systems (prose-based).
- Full World Lifecycle (Phase 9).

## Acceptance Criteria
- [ ] `ContractAppraisalSystem` implements trust/risk/greed logic from legacy `RecruitmentNegotiationService`.
- [ ] `PartyCoordinationSystem` ensures group members share the same active objective.
- [ ] `test_social_contract_lifecycle.py` proves end-to-end recruitment, execution, and reward splitting.
- [ ] `test_strategic_memory.py` proves that failed leads are suppressed and projects are eventually abandoned.
- [ ] No regression in `test_strategic_lifecycle_v2.py`.

## Related Tickets
- TCK-20260430-PH5-COMBAT-LEGALITY-HARDENING (Completed)

## Related Docs
- [resource_v2_e3_phases_enhanced.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases_enhanced.md)
- [logic_checklist_exhaustive_v2.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive_v2.md)

## Related Code Areas
- `src/social/contracts.py`
- `src/systems/strategic.py`
- `src/social/appraisal.py`
- `src/systems/party.py` [NEW]

## Implementation Notes
- Use the V2 `StateUpdate` and `AuthoritativeApplyPipeline` patterns.
- Ensure social consequences (trust/reputation) flow through `ResourceTransactionResolver` or similar authoritative path.
- Keep the "PRG-core logic" as requested, optimizing for V2's deterministic nature.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
