# TCK-20260413-INTEL-CAPACITY-IMPLEMENTATION

## Title
Implement Intel Capacity (Cognition Capacity and Bounded Intelligence)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the cognition-capacity and bounded-intelligence extension for the strategic simulation engine, iteratively by milestones. Focus on Milestone 1 first (Cognition Capacity Foundation).

## Scope
- Milestone 1: Define the cognition-capacity contract and builder.
- Milestone 2: Integrate into strategic appraisal.
- Milestone 3: Apply to blockers, detours, and lead learning.
- Milestone 4: Apply to social reasoning and cooperation.
- Milestone 5: Apply to event interpretation and identity drift.
- Milestone 6: Expose through API and UI schemas.
- Milestone 7: Extend replay, graph export, and headless regression.
- Milestone 8: Complete documentation and verification pack.

## Out of Scope
- Unrelated world-systems or new story objects.
- Personality/Trait/Archetype/Emotion modifiers in Milestone 1.

## Acceptance Criteria
- Exact, typed, deterministic `CognitionCapacityProfile` model.
- Deterministic `CognitionCapacityBuilder` deriving profile from attributes.
- 100% test coverage for derivation logic including golden-value cases.
- Purity and non-mutation proven by tests.
- Documentation exactly matching implementation.

## Related Tickets
- TCK-20260412-STRATEGY-IMPLEMENTATION.md (Precursor)

## Related Docs
- intel_capacity_implementation.md
- intel_capacity_implementation_milestone_1.md

## Related Stored Artifacts
- None

## Related Code Areas
- `src/ai/cognition_capacity.py` (New)
- `src/ai/brain.py` (Integration entry)
- `src/ai/strategy/` (Integration targets)

## Assumptions / Open Questions
- Assumption: `SimulationModel` in `src/core/models/base.py` is the base for models.
- Assumption: `Attributes` and `AttributeCaps` in `src/core/gameplay/attributes.py` provide the input.

## Implementation Notes
- Follow strict formulas from `intel_capacity_implementation_milestone_1.md`.
- Use @clean-code and @brainstorming principles.

## Test Summary
- Unit tests for `CognitionCapacityBuilder` (Golden values, Determinism, Non-mutation).

## Files Changed
- `src/ai/cognition_capacity.py`
- `src/ai/strategic_appraisal.py`
- `src/ai/strategic_uncertainty_resolution.py`
- `src/ai/strategic_social_reasoning.py`
- `src/ai/strategic_event_interpretation.py`
- `src/core/models/decision.py`
- `src/core/models/cognition_telemetry.py`
- `src/api/schemas.py`
- `src/api/presenters/ai_presenter.py`
- `src/ui/cli/inspector.py`
- `src/utils/replay.py`
- `src/core/logic/cognition_graph_exporter.py`
- `src/testing/assertions.py`
- `tests/ai/test_intel_capacity_regression.py`
- `tests/ai/test_cognition_capacity_builder.py`
- `tests/ai/test_cognition_capacity_determinism.py`
- `tests/ai/test_cognition_capacity_non_mutation.py`
- `intel_capacity_implementation_milestone_*.md`

## Completion Summary
- Implemented full 8-milestone strategic cognition capacity engine.
- Established deterministic cognition profile derivation from entity attributes.
- Integrated bounded-intelligence limits into strategic appraisal, uncertainty, social reasoning, and event interpretation.
- Exposed full strategic state and cognition telemetry through API (schemas/presenters) and CLI (EntityInspector).
- Hardened verification with bit-identical regression tests covering replay and graph artifacts.
- Finalized documentation pack including feature spec, tuning guide, and UI contract.
- Verified 100% test stability for all cognition/capacity modules.
