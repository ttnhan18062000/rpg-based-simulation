# TCK-20260414-LEARNING-SOCIAL-CONSEQUENCE

## Title
Strategic Learning Loops & Social Consequences

## Status
DONE

## Request Summary
Address learning, social consequences, and graph relationships from the updated implementation plans.

## Scope
- Anti-cheating candidate-zone and hypothesis tests (vague information stays vague).
- End-to-end source-trust application and future-weighting tests (durable learning proof).
- Deterministic post-breach/post-success future-recruitment tests.
- Thresholded repeated-event mutation tests (directive shifts after multiple near-deaths/betrayals).
- Downstream feedback-loop tests (betrayal affects later recruitment).
- Expand graph export coverage to obligations, contracts, zones, and hypotheses.

## Out of Scope
- Cognition derivation hardening (covered in TCK-COGNITION).

## Acceptance Criteria
- Regression tests prove that vague rumores do not collapse to exact coordinates without direct evidence.
- `StrategicLearningService` improvements to use authoritative trust.
- Social tests prove recruitment is harder after a contract breach.
- Directive mutation occurs only after repeated thresholded events.
- Cognition graph exports obligations and recruitment offers as relational edges.

## Related Tickets
- TCK-20260414-INFRA-REMEDIATION (Parallel)
- TCK-20260414-COGNITION-EXPLAINABILITY-HARDENING (Parallel)

## Related Docs
- intel_capacity_implementation_updated.md
- strategy_implementation_updated_v2.md

## Related Code Areas
- `src/core/logic/cognition_graph_exporter.py`
- `src/ai/strategic_uncertainty_resolution.py`
- `src/core/logic/social_state_applicator.py`
- `src/core/logic/event_interpreter.py`

## Implementation Notes
- Use `MemorySalienceService` or similar to track event history for thresholds.
- Ensure `CandidateZone` search results degrade uncertainty correctly.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
