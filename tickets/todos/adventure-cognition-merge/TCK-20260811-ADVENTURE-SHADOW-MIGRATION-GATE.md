---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE
phase: open
date: 2026-08-11
tags: [testing, cognition, adventure, feature-flags]
---

# TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE

## Title
Staged migration and rollout plan for the new decision path

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Land the scorer alongside AdventureDecisionPhase, unit-testable in isolation; build a shadow-mode integration test running both paths side by side, diffing decisions without affecting committed state; only then remove AdventureDecisionPhase; full-corpus SimQ re-run before final cutover.

## Scope
- Shadow-mode integration test constructing one AuthoritativeState scenario, running both AdventureDecisionPhase.apply(state) and AdventureGoalScorer.score(entity,state)/materialization independently against the same unmodified state snapshot, asserting neither call path committed any change to state itself (pre/post equality or hash check)
- For each of the 15 route families, test asserts both paths select the same winning route family and same underlying raw_score (not utility) for representative scenario fixtures, surfacing normalization miscalibration as a named itemized diff report (not single pass/fail)
- Diff report explicitly separates raw_score mismatches from utility mismatches, so the exact scale-mismatch bug shape (design doc §4) is caught by the shadow test itself
- Migration step 4 scoped as: invoke the existing /simq-audit workflow (mode=full or mode=slow) as a pre-cutover gate and record its verdict -- not new SimQ infrastructure

## Out of Scope
- Building AdventureGoalScorer itself -- ADVENTURE-GOAL-SCORER's (C1) job; this ticket only tests it once it exists
- Deleting AdventureDecisionPhase -- DELETE-ADVENTURE-DECISION-PHASE's (C3) job, which is gated on this ticket's shadow test passing
- Reimplementing /simq-audit's Recalibrate/Classify-Drift/Report machinery -- this ticket only invokes the existing workflow as a gate

## Acceptance Criteria
- [ ] Shadow-mode integration test constructs one AuthoritativeState scenario, runs both AdventureDecisionPhase.apply(state) and AdventureGoalScorer.score(entity,state)/materialization independently against the same unmodified state snapshot, and asserts neither call path committed any change to state itself (pre/post equality or hash check)
- [ ] For each of the 15 route families, the test asserts both paths select the same winning route family and same underlying raw_score (not utility) for representative scenario fixtures
- [ ] Diff report explicitly separates raw_score mismatches from utility mismatches
- [ ] AdventureDecisionPhase removal (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE's work) is gated in that ticket's own acceptance criteria on this shadow-mode test passing first, encoded as a hard dependency
- [ ] Migration step 4 is scoped as 'invoke /simq-audit mode=full (or mode=slow) as pre-cutover gate and report its verdict' -- AC asserts the audit was run and its verdict recorded, not that new SimQ infrastructure was built

## Related Tickets
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-D22-DORMANT-WIRING-AUDIT
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF

## Related Docs
- docs/simulation_quality/audit_workflow.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/engine/pipeline.py
- src/ai/goals/base.py
- src/ai/goals/scorers.py
- src/observability/event_shapers.py
- src/domains/optimization/feature_flags.py
- src/domains/optimization/rollout_profiles.py

## Assumptions / Open Questions
- Design doc's own 'Open Questions For Implementation' leaves unresolved whether the shadow test needs its own dedicated scenario corpus or can reuse tests/integration/scenarios/ fixtures -- must be resolved at this ticket's own Investigate/Plan time, not deferred further; tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py is the most likely reuse candidate
- This ticket is scoped to steps 2+4 of the design's 4-step migration plan only (shadow diff test + gating the existing /simq-audit workflow), not step-1 scorer construction, to keep ownership from blurring with TCK-20260811-ADVENTURE-GOAL-SCORER
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md §7, §9

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
