# TCK-20260412-STRAT-EVENT-REP

## Title
Event-driven Strategic Reprioritization Implementation

## Status
DONE

## Request Summary
Implement Milestone 5 of the strategic cognition layer: ensuring that major narrative events (trauma, home damage, betrayal) trigger structural reprioritization (concerns, project pivots, social feedback) based on identity and attachment.

## Scope
- `StrategicEventInterpreter` for reflective appraisal.
- `last_interpreted_event_tick` persistence.
- Divergent concern generation (PlaceAttachment).
- Social feedback loop for betrayal.
- Integration tests for reprioritization flow.

## Acceptance Criteria
- [x] Events trigger concerns via reflective appraisal.
- [x] Projects pivot or suspend based on concern priority.
- [x] Attachment modulates concern priority (divergence).
- [x] Betrayal affects future recruitment (feedback).
- [x] 100% test pass for new integration suite.

## Implementation Notes
- Implemented `StrategicEventInterpreter` in `src/core/logic/`.
- Updated `AIBrain._strategic_appraisal_phase` to include a reflective interpret turn.
- Hardened `StrategicUpdate` and `ActionSystem` for tick persistence.
- Added divergence to `ConcernGenerationService`.
- Added betrayal aversion to `RecruitmentNegotiationService`.

## Test Summary
- `pytest tests/integration/strategy/test_strategic_event_consequences.py`: 3/3 PASSED.
- `pytest tests/unit/ai/strategy/test_recruitment_negotiation.py`: 4/4 PASSED.

## Files Changed
- `src/core/logic/strategic_event_interpreter.py` [NEW]
- `src/core/logic/strategic_consequence_service.py` [MODIFY]
- `src/core/logic/concern_generation.py` [MODIFY]
- `src/core/logic/project_mutation_service.py` [MODIFY]
- `src/ai/brain.py` [MODIFY]
- `src/ai/strategy/recruitment_negotiation.py` [MODIFY]
- `src/actions/base.py` [MODIFY]
- `src/systems/gameplay/action_system.py` [MODIFY]
- `src/core/models/life_events.py` [MODIFY]
- `src/core/aspects/mind.py` [MODIFY]
- `tests/integration/strategy/test_strategic_event_consequences.py` [NEW]
