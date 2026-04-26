# TCK-20260427-PH6-STRATEGIC-COGNITION

## Title
Implement Phase 6 — Strategic Cognition Hardening

## Status
INPROGRESS

## Request Summary
Implement the legacy logic for strategic cognition (Phase 6) into the V2 engine. This includes project continuity, blocker inference, lead resolution, and detour suggestions.

## Scope
- Implement Blocker generation on action failure in `AuthoritativeApplyPipeline`.
- Implement Detour suggestion and project switching in `StrategicIntelligenceSystem`.
- Integrate `DetourSuggestionSystem` into the main decision loop.
- Verify with regression tests.

## Out of Scope
- Full AI "Personality" implementation (reserved for later phases).
- Complex group-strategy (Phase 8).

## Acceptance Criteria
- [ ] Failed actions generate appropriate `BlockerState`.
- [ ] Blocked projects trigger detour searches.
- [ ] Actors switch to high-utility detours.
- [ ] Regression tests pass for the full strategic loop.

## Related Tickets
- None

## Related Docs
- `resource_v2_e2_phases.md`
- `logic_checklist_exhaustive.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/systems/strategic.py`
- `src/systems/detour.py`
- `src/engine/pipeline.py`
- `src/engine/domain_logic.py`

## Assumptions / Open Questions
- Assumption: `LegalityServiceV2` provides enough detail in `reason` to infer blocker types.

## Implementation Notes
- Will use `StrategicUpdate` to pass blockers from pipeline to state.

## Test Summary
- None yet.

## Files Changed
- None yet.

## Completion Summary
- None yet.
