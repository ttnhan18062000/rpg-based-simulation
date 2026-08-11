---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
phase: open
date: 2026-08-11
tags: [cognition, world]
---

# TCK-20260811-REGION-STABILIZATION-GOAL-SCORER

## Title
Generalize GoalScorer-wrapper pattern to region stabilization (events.py)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Apply the same wrapper pattern used for adventure to src/systems/world_systems/events.py:98/stabilize_project (RegionStabilizationGoalScorer), which today unconditionally overwrites current_project_id without going through the arbiter. Part of the design's Goal #4 (generalizing the wrapper pattern to the other confirmed arbiter-bypass sites); explicitly out of scope for direct implementation in the original design but a natural follow-on.

## Scope
- Resolve the missing-enum-member gap first: events.py's stabilize/exploration/investigate project/objective kinds are currently raw strings with no matching ProjectKind/ObjectiveKind enum member -- add ProjectKind.STABILIZE (or explicitly justify reusing an existing member) so _score_scale_max()'s isinstance(kind, ProjectKind) classification does not silently fall through to the wrong scale
- New RegionStabilizationGoalScorer (GoalScorer) wrapping EventInterpreter's existing unchanged internal danger-interpretation logic, producing a GoalScore with raw score in metadata (never utility)
- EventInterpreter.interpret_regional_danger()'s stabilize-project path no longer sets current_project_id_set directly; the resulting GoalScore must clear evaluate_project_switch() too
- tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance and ::test_no_pivot_when_resistance_high re-run against the new scorer path with equivalent assertions

## Out of Scope
- contracts.py / SocialContractGoalScorer -- structurally independent bypass site, covered by TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
- events.py line 179's current_project_id_set=None clear -- that is a clear, not a steal, explicitly out of scope
- AdventureGoalScorer -- TCK-20260811-ADVENTURE-GOAL-SCORER's job

## Acceptance Criteria
- [ ] The missing ProjectKind/ObjectiveKind enum-member gap is resolved explicitly (new ProjectKind.STABILIZE added, or an existing member reused with explicit rationale recorded) -- not left as a raw string
- [ ] EventInterpreter.interpret_regional_danger()'s stabilize-project path no longer sets current_project_id_set directly
- [ ] RegionStabilizationGoalScorer produces a comparable GoalScore that must clear evaluate_project_switch() to become current_project_id
- [ ] tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance and ::test_no_pivot_when_resistance_high pass against the new scorer path with equivalent assertions
- [ ] Materialized ProjectState.kind uses a real ProjectKind enum member
- [ ] Follows the same raw-score/utility separation requirement as TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/world_systems/events.py
- src/systems/event_interpreter.py
- src/core/strategic.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- NEW FINDING undocumented by the design doc: events.py's stabilize/exploration/investigate kinds are raw strings with no matching ProjectKind/ObjectiveKind enum member today -- skipping this fix risks reproducing the exact TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class; must be resolved as part of this ticket's own scope, not silently deferred
- Same real-behavior-change caveat as TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER: today stabilize always wins the project slot, post-migration it competes and can lose
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns / Goal #4)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
