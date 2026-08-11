---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
phase: open
date: 2026-08-11
tags: [social, cognition]
---

# TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Title
Generalize GoalScorer-wrapper pattern to social-contract acceptance (contracts.py)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Apply the same wrapper pattern used for adventure to src/systems/social_systems/contracts.py:187 (SocialContractGoalScorer), which today unconditionally overwrites current_project_id without going through the arbiter. Part of the design's Goal #4 (generalizing the wrapper pattern to the other confirmed arbiter-bypass sites); a natural follow-on now that the pattern is established.

## Scope
- New GoalKind member (e.g. SOCIAL_CONTRACT) added to src/core/strategic.py
- New SocialContractGoalScorer (GoalScorer) delegating to ContractService's existing unchanged internal contract-acceptance logic, producing a GoalScore with raw score in metadata (never utility) per the wrapper pattern
- ContractService.accept_contract() no longer sets current_project_id_set directly; the resulting GoalScore must clear evaluate_project_switch()'s comparison to become current_project_id
- Materialized ProjectState.kind uses a real ProjectKind enum member, respecting _score_scale_max's enum-identity classification (not string value)
- tests/unit/strategic/test_strategic_social_contracts.py::test_accepted_contract_spawns_project_and_objective rewritten as a scorer-output assertion (not just extended)

## Out of Scope
- events.py / RegionStabilizationGoalScorer -- structurally independent bypass site with different data shapes, covered by TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
- AdventureGoalScorer and its own materialization path -- TCK-20260811-ADVENTURE-GOAL-SCORER's job; this ticket follows the same pattern but is a separate materialization path

## Acceptance Criteria
- [ ] ContractService.accept_contract() no longer sets current_project_id_set directly
- [ ] Accepting a contract produces a GoalScore (via new SocialContractGoalScorer) that must clear evaluate_project_switch()'s comparison to become current_project_id
- [ ] An entity with a high-lock current project + a newly-accepted low-urgency contract keeps its current project (the contract does not win)
- [ ] An entity with no current project, or a contract that legitimately outscores the lock, does switch
- [ ] Materialized ProjectState.kind uses a real ProjectKind enum member
- [ ] Follows raw-score/normalized-utility separation: metadata["raw_score"], never utility, goes into ProjectState.score
- [ ] docs/mechanics and the relevant parity ledger entry updated in the same session

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/contracts.py
- src/ai/goals/base.py
- src/core/strategic.py
- src/systems/strategic_systems/intelligence.py
- src/ai/goals/scorers.py

## Assumptions / Open Questions
- This is a real behavior change: today accepting a contract ALWAYS wins the project slot; post-migration it competes and can lose -- this is the explicit point, not a regression
- Needs empirical validation of normalization constants (not assumable by formula alone)
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns / Goal #4)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
