---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE
phase: open
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE

## Title
Delete AdventureDecisionPhase and relocate its eligibility helpers

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Remove the AdventureDecisionPhase class and its pipeline.py registration entirely, once the new scorer-based path is live. _resolve_cognition_profile_id/_supports_adventure_routing move to wherever AdventureGoalScorer lives, unchanged internally. This is the final step-3 cutover of the staged migration plan.

## Scope
- Remove AdventureDecisionPhase class and its ENABLE_ADVENTURE_ROUTING-gated registration in src/engine/pipeline.py
- Relocate _resolve_cognition_profile_id and _supports_adventure_routing (currently src/domains/adventure/phase.py lines 49-96) to AdventureGoalScorer's module (src/ai/goals/), byte-identical internally
- Migrate the 5-6 tests currently importing AdventureDecisionPhase directly to exercise the AdventureGoalScorer/tier-5 path with equivalent coverage
- Update STRAT-236 text+v2_evidence and docs/simulation/domains/adventure_contract.md's 'Engine Phase' section so neither references AdventureDecisionPhase/phase.py as the live mechanism

## Out of Scope
- _threat_resolved() relocation and evaluate_project_switch() signature change -- confirmed this belongs to THREAT-RESOLVED-ARBITER-RELOCATION (C2), not this ticket; C3's own investigation only names the eligibility helpers as its relocation scope
- Building AdventureGoalScorer itself -- ADVENTURE-GOAL-SCORER's (C1) job, a hard prerequisite for this ticket
- Building the shadow-mode diff test -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job, also a hard prerequisite for this ticket

## Acceptance Criteria
- [ ] This ticket's Implement phase does not proceed until TCK-20260811-ADVENTURE-GOAL-SCORER (C1) and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4) are both in tickets/done/ -- Scope must verify both exist and are DONE before allowing Implement to proceed; if not, this ticket is held/blocked
- [ ] AdventureDecisionPhase class and its pipeline.py registration are removed; grep for AdventureDecisionPhase in src/engine/pipeline.py returns no matches
- [ ] _resolve_cognition_profile_id and _supports_adventure_routing exist byte-identical in AdventureGoalScorer's module (src/ai/goals/), same inputs/outputs as before
- [ ] All 5-6 tests currently importing AdventureDecisionPhase directly are migrated to exercise the AdventureGoalScorer/tier-5 path with equivalent coverage
- [ ] STRAT-236 text+v2_evidence and adventure_contract.md's 'Engine Phase' section no longer reference AdventureDecisionPhase/phase.py as the live mechanism

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
- TCK-20260810-D22-DORMANT-WIRING-AUDIT
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER

## Related Docs
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- PRIMARY RISK -- this ticket's real 'delete' action is explicitly gated behind TCK-20260811-ADVENTURE-GOAL-SCORER and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE landing first -- creating/implementing this ticket ahead of those must be rejected or held at Scope if attempted prematurely
- Blast radius wider than '2 functions relocate' -- 6 test files break immediately on deletion
- Confirmed via sibling investigation: _threat_resolved's relocation belongs to TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION, not this ticket
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md §5, §7

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
