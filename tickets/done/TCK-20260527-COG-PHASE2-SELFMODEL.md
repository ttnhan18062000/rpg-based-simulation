# TCK-20260527-COG-PHASE2-SELFMODEL

## Title

Phase 2 — Bottom-Up Entity Self Model

## Status

DONE

## Request Summary

Build the internal interpretation layer: entities must be able to assess their own condition, interpret their needs, estimate capabilities, and maintain personal knowledge/unknowns — without hardcoding adventure readiness views.

## Scope

- `SelfModelBundle` (grouping dataclass in `src/core/self_model.py`)
- `SelfAwarenessComponent`, `NeedInterpretationComponent`, `CapabilityEstimateComponent`, `KnowledgeModelComponent`
- Four cognition services: `SelfAssessmentService`, `NeedInterpretationService`, `CapabilityEstimateService`, `KnowledgeModelService`
- `SelfModelUpdatePhase` orchestrator with dirty-check
- Trace events: `SelfAwarenessUpdatedEvent`, `NeedInterpretedEvent`, `CapabilityEstimateUpdatedEvent`, `KnowledgeFactLearnedEvent`, `KnowledgeUnknownRecordedEvent`
- 7 new test files
- `docs/entity/entity_base.md` and diagram update
- `docs/test_coverage/phase2_self_model_coverage.md`

## Out of Scope

- `AdventureReadinessComponent`
- `QuestReadinessComponent`, `CombatReadinessComponent`
- Combat engagement cognition
- Full adventure route selection
- Party formation logic
- Long-term combat learning

## Acceptance Criteria

- Wounded entity knows it is vulnerable (low_health weakness + healing need dominant)
- Hungry entity has food need
- Weak-weapon entity has equipment weakness
- Unknown material produces knowledge gap (UnknownFact, not fake knowledge)
- Better equipment improves capability estimate
- Provider partial answer does not leak hidden truth
- Self-model update stays inside performance budget
- 166+ strategic tests still pass (no regression)

## Related Tickets

- TCK-20260527-COG-PHASE1-* (all done)

## Related Docs

- entity_enhance_phase2.md
- docs/entity/entity_base.md
- docs/mechanics/

## Related Stored Artifacts

- stored_artifacts/TCK-20260527-COG-PHASE1-*/

## Related Code Areas

- src/core/state.py
- src/core/builder.py
- src/core/self_model.py
- src/cognition/
- src/world/providers/information.py

## Assumptions / Open Questions

- `SelfModelBundle` groups all four components under one field on `EntityState` to minimize schema noise.
- Entity-owned `KnowledgeFact` in `self_model.py` is intentionally separate from provider-side `KnowledgeFact` in `information.py`.
- Dirty detection is done by comparing tick-stamped fields; no separate DirtySet entry needed for self-model (it is derived state, not authoritative mutation source).

## Implementation Notes

- Fully implemented clean stateless services: `SelfAssessmentService`, `NeedInterpretationService`, `CapabilityEstimateService`, and `KnowledgeModelService`.
- Grouped everything under the dataclass `SelfModelBundle`.
- Designed `SelfModelUpdatePhase` as a central update pipeline runner.
- Added a high-performance dirty check in `SelfModelUpdatePhase.run` that bypasses need interpretation and capability estimation when raw values haven't changed, conserving critical CPU budgets for 100+ entities (<5 microseconds per clean entity update).
- Created a robust frozen trace events structure under `src/cognition/trace_events.py` capturing transitions and learning milestones.
- Excluded self-model components from the canonical hash computation (derived data) but included in dict serialization.

## Test Summary

- Fully created unit test suites covering every service and phase:
  - `tests/unit/entity/test_phase2_self_model_components.py` (25/25 passed)
  - `tests/unit/cognition/test_phase2_self_assessment_service.py` (19/19 passed)
  - `tests/unit/cognition/test_phase2_need_interpretation_service.py` (15/15 passed)
  - `tests/unit/cognition/test_phase2_capability_estimate_service.py` (15/15 passed)
  - `tests/unit/cognition/test_phase2_knowledge_model_service.py` (15/15 passed)
  - `tests/unit/cognition/test_phase2_self_model_phase.py` (5/5 passed)
- Created 5 high-fidelity strategic gameplay integration scenarios under `tests/integration/scenarios/test_phase2_self_model_scenarios.py` (5/5 passed).
- Added a strict performance timing budget test under `tests/perf/test_phase2_self_model_budget.py` (1/1 passed).
- All 100/100 Phase 2 tests successfully pass (0 failures).
- Verified zero regressions on existing codebase: 166/166 strategic tests successfully pass.

## Files Changed

- `src/core/self_model.py` (NEW)
- `src/core/state.py` (MODIFIED)
- `src/core/builder.py` (MODIFIED)
- `src/cognition/__init__.py` (NEW)
- `src/cognition/self_assessment.py` (NEW)
- `src/cognition/need_interpretation.py` (NEW)
- `src/cognition/capability_estimate.py` (NEW)
- `src/cognition/knowledge_model.py` (NEW)
- `src/cognition/self_model_phase.py` (NEW)
- `src/cognition/trace_events.py` (NEW)
- `docs/entity/entity_base.md` (MODIFIED)
- `docs/entity/entity_aspect_relationship_diagram.mmd` (MODIFIED)
- `docs/test_coverage/phase2_self_model_coverage.md` (NEW)
- `tests/unit/entity/test_phase2_self_model_components.py` (NEW)
- `tests/unit/cognition/test_phase2_self_assessment_service.py` (NEW)
- `tests/unit/cognition/test_phase2_need_interpretation_service.py` (NEW)
- `tests/unit/cognition/test_phase2_capability_estimate_service.py` (NEW)
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` (NEW)
- `tests/unit/cognition/test_phase2_self_model_phase.py` (NEW)
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py` (NEW)
- `tests/perf/test_phase2_self_model_budget.py` (NEW)

## Completion Summary

- Implemented the bottom-up entity self model layers with perfect acceptance criteria coverage.
- Fully verified all behavior, safety properties, performance budget limits, and information opacity constraints under unit, integration, and performance benchmarking.
- Strategic integrity is 100% preserved. No temporary run data or certification reports left behind. Done!
