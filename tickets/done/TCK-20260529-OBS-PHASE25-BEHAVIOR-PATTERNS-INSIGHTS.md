# TCK-20260529-OBS-PHASE25-BEHAVIOR-PATTERNS-INSIGHTS

## Title

Pattern Detectors and Behavior Insights (Phase 25)

## Status

INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Detect behavioral problems and improvements post-run, converting them into structured findings and insights.

## Scope

- Implement immutable `BehaviorFinding` and `BehaviorInsight` models
- Implement `RepeatedFailureLoopDetector`, `BehaviorChangeProofDetector`, and `HiddenKnowledgeSuspicionDetector`
- Implement `BehaviorInsightGenerator` compiling findings into high-level summaries
- Guarantee zero simulation tick overhead

## Out of Scope

- Running pattern analyzers inside the engine tick loop

## Acceptance Criteria

- Fully covered by unit, integration, and compatibility tests
- All tests pass cleanly under the `not slow` marker
- Documentation in `docs/entity/entity_base.md` updated with Section 37

## Related Tickets

- None

## Related Docs

- `docs/entity/entity_base.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/behavior/`

## Assumptions / Open Questions

- None

## Test Summary

- Pending execution

## Files Changed

- Pending modification
