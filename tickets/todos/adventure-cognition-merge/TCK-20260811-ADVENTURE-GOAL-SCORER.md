---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-ADVENTURE-GOAL-SCORER
phase: open
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-ADVENTURE-GOAL-SCORER

## Title
Build AdventureGoalScorer and its materialization path

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create a new AdventureGoalScorer implementing the existing GoalScorer protocol, registered under a new GoalKind.ADVENTURE_ROUTE enum member, that wraps AdventureDecisionService.decide() unchanged and folds it into GoalRegistry.get_all_scores() as one candidate among many in tier 5 of the strategic hierarchy -- instead of running as a structurally-independent earlier pipeline phase invisible to tiers 1-4. This subjects adventure routing to the same tier-5 arbitration as every other project-switch candidate.

## Scope
- New GoalKind.ADVENTURE_ROUTE member added to src/core/strategic.py
- New AdventureGoalScorer class in src/ai/goals/ implementing GoalScorer.score(entity, state) -> GoalScore, wrapping AdventureDecisionService.decide() unchanged
- Registration via GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer()) in src/ai/goals/__init__.py
- Utility normalization: utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX, with raw_score of 2.9 normalizing to utility==100.0 exactly
- GoalScore.metadata carries route_family and raw_score
- New materialization branch (tier-5 winner path) calling RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...) across all 15 mapped route families -- never best_candidate.utility
- Ineligible entities / DEFER_WITH_REASON results produce GoalScore(utility=0, target_id=None) that never clears the 20.0 tier-5 floor
- Dedicated regression test asserting materialized ADVENTURE_ROUTE winner's ProjectState.score equals metadata["raw_score"], never best_candidate.utility

## Out of Scope
- Wiring AdventureGoalScorer into src/engine/pipeline.py or deleting AdventureDecisionPhase -- that is DELETE-ADVENTURE-DECISION-PHASE's (C3) job, gated on this ticket and ADVENTURE-SHADOW-MIGRATION-GATE (C4) landing first
- Shadow-mode comparison test and /simq-audit pre-cutover gate -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job
- _threat_resolved() relocation and evaluate_project_switch() signature change -- THREAT-RESOLVED-ARBITER-RELOCATION's (C2) job
- Closing STRAT-185's null test_path is a nice-to-have opportunity, not guaranteed in this ticket's scope

## Acceptance Criteria
- [ ] GoalKind.ADVENTURE_ROUTE is a new member in src/core/strategic.py; AdventureGoalScorer (new, in src/ai/goals/) implements GoalScorer.score(entity, state) -> GoalScore and is registered via GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer()) in src/ai/goals/__init__.py
- [ ] AdventureGoalScorer.score() calls AdventureDecisionService.decide() unchanged and returns GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=(raw_score/_ADVENTURE_ROUTE_SCORE_MAX)*_GOAL_UTILITY_SCORE_MAX, metadata={"route_family":...,"raw_score":raw_score,...}); a raw_score of 2.9 normalizes to utility==100.0 exactly
- [ ] When ADVENTURE_ROUTE wins tier 5, the new materialization branch calls RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...) -- never best_candidate.utility -- across all 15 mapped route families, preserving the existing (None,None) handling for DEFER_WITH_REASON
- [ ] A dedicated regression test asserts the materialized ADVENTURE_ROUTE winner's ProjectState.score equals metadata["raw_score"], never best_candidate.utility
- [ ] Ineligible entities and DEFER_WITH_REASON results produce GoalScore(utility=0, target_id=None) that never clears the 20.0 tier-5 floor
- [ ] Tie-break ordering (sort by -utility then kind) has a deliberate string-value decision for GoalKind.ADVENTURE_ROUTE, not an arbitrary one

## Related Tickets
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
- TCK-20260810-D22-DORMANT-WIRING-AUDIT
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/ai/goals/base.py
- src/ai/goals/scorers.py
- src/ai/goals/__init__.py
- src/core/strategic.py
- src/domains/adventure/service.py
- src/domains/adventure/mapper.py
- src/domains/adventure/phase.py
- src/domains/adventure/schema.py
- src/domains/adventure/scoring.py
- src/systems/strategic_systems/intelligence.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- RouteFamily has 16 members but _MAP covers 15 (DEFER_WITH_REASON excluded, returns (None,None)) -- implementation must preserve this None-handling, not force all 16 through the mapper
- STRAT-185 parity entry still has test_path:null; closing it here is an opportunity, not a guaranteed scope item
- Getting the raw_score-not-utility rule wrong (design doc §4) would independently reproduce the just-fixed TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
