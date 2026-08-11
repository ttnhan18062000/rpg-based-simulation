---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION
phase: open
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION

## Title
Relocate _threat_resolved() into the shared arbiter and extend evaluate_project_switch()'s lock check

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Move _threat_resolved() (currently adventure-specific, src/domains/adventure/phase.py) to src/systems/strategic_systems/, co-located with evaluate_project_switch(), which becomes its sole caller. Add a state: AuthoritativeState parameter to evaluate_project_switch(), thread it through call sites, and extend the lock-expiry condition to also check not _threat_resolved(entity, state). This closes a real pre-existing gap: the function's own docstring already claimed broader scope than only AdventureDecisionPhase ever exercised.

## Scope
- Relocate _threat_resolved() from src/domains/adventure/phase.py to src/systems/strategic_systems/intelligence.py (co-located with evaluate_project_switch)
- Add state: AuthoritativeState parameter to evaluate_project_switch(); thread through all 3 real production call sites: intelligence.py:1345, intelligence.py:1426, phase.py:192
- Extend the lock-expiry condition in evaluate_project_switch() (intelligence.py:991-996) to additionally check not _threat_resolved(entity, state), as an additive check, not a replacement of the existing locked-branch comparison
- Bring the SpatialQueryService.nearby_entities dependency along with the relocation
- Update STRAT-236's text AND v2_evidence fields (both, not just v2_evidence) in docs/parity_ledger/strategic_cognition.yaml to cite the new location and generalized scope
- New regression test: a COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure system, with threat resolved, is now also early-released

## Out of Scope
- AdventureGoalScorer construction and tier-5 materialization -- ADVENTURE-GOAL-SCORER's (C1) job
- Deleting AdventureDecisionPhase or relocating _resolve_cognition_profile_id/_supports_adventure_routing -- DELETE-ADVENTURE-DECISION-PHASE's (C3) job; this ticket owns _threat_resolved's relocation specifically, resolving the ambiguous C2/C3 boundary in C3's own favor for the eligibility helpers only
- Shadow-mode comparison test infrastructure -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job

## Acceptance Criteria
- [ ] evaluate_project_switch()'s signature gains state: AuthoritativeState; all 3 real production call sites (intelligence.py:1345, intelligence.py:1426, phase.py:192) thread state through, with no behavior change on the raw/unlocked comparison path
- [ ] Locked current project + entity HP>80% + no hostile within radius 10.0 results in the lock being treated as expired and falls through to raw comparison, byte-identical to today's AdventureDecisionPhase-only behavior for adventure-originated projects
- [ ] A COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure system, with threat resolved, is now also early-released -- new regression test required, closing the STRAT-236 documented-but-never-wired gap
- [ ] STRAT-236's text AND v2_evidence fields in docs/parity_ledger/strategic_cognition.yaml both cite the new location and generalized scope

## Related Tickets
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260627-P2A-SPAWN-LOCK-COND

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/systems/strategic_systems/intelligence.py
- src/engine/spatial_query.py

## Assumptions / Open Questions
- OPEN DESIGN DECISION (must be resolved explicitly at Plan time, not silently picked): 25 direct test call sites across 5 test files (test_score_normalization.py, test_interruption_resistance.py, test_project_continuity.py, test_strategic_reprioritization.py, test_quest_activation_pathway.py) call evaluate_project_switch(entity, candidate, current_tick=...) with no state argument. Implement must explicitly choose: (a) require state and update all 25 call sites with minimal AuthoritativeState fixtures, or (b) give it a default Optional[AuthoritativeState]=None and skip the _threat_resolved check when None. The larger-blast-radius option must not be picked silently.
- tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py's AST-based assertions need re-verification post-relocation
- phase.py:151's existing gate and the new evaluate_project_switch check will both evaluate _threat_resolved redundantly on the same tick when routing succeeds -- disclosed as harmless, not to be 'optimized away' as part of this ticket
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md §5

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
