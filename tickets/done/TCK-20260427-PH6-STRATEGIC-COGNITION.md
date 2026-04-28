# TCK-20260427-PH6-STRATEGIC-COGNITION

## Title
Implement Phase 6 — Strategic Cognition Hardening

## Status
DONE

## Request Summary
Implement and stabilize the Phase 6 strategic cognition engine, including deterministic blocker resolution, detour suggestions, and authoritative state signaling for resolution events.

## Scope
- Implement Blocker generation on action failure in `AuthoritativeApplyPipeline`.
- Implement Detour suggestion and project switching in `StrategicIntelligenceSystem`.
- Integrate `DetourSuggestionSystem` into the main decision loop.
- Verify with regression tests (Strategic Cognition & Progression).

## Out of Scope
- Full AI "Personality" implementation (reserved for later phases).
- Complex group-strategy (Phase 8).

## Acceptance Criteria
- [x] Failed actions generate appropriate `BlockerState`.
- [x] Blocked projects trigger detour searches.
- [x] Actors switch to high-utility detours.
- [x] Regression tests pass for the full strategic loop (615 tests passing).

## Related Tickets
- None

## Related Docs
- `resource_v2_e2_phases.md`
- `logic_checklist_exhaustive.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260427-PH6-STRATEGIC-COGNITION/plan.md`
- `stored_artifacts/TCK-20260427-PH6-STRATEGIC-COGNITION/investigation.md`
- `stored_artifacts/TCK-20260427-PH6-STRATEGIC-COGNITION/walkthrough.md`

## Related Code Areas
- `src/systems/strategic.py`
- `src/systems/detour.py`
- `src/engine/pipeline.py`
- `src/engine/evolution.py`

## Assumptions / Open Questions
- Assumption: `LegalityServiceV2` provides enough detail in `reason` to infer blocker types. [VERIFIED]

## Implementation Notes
- Resolved `AttributeError` in `StrategicIntelligenceSystem.resolve_blockers` by ensuring resolved blockers are signaled via `StrategicUpdate` before removal.
- Hardened `AuthoritativeApplyPipeline` to preserve non-spatial updates (e.g. HP loss) during occupancy conflicts (Partial Rejection Law).
- Synchronized `EvolutionSystem` growth with `ApplyPath` Recalculation Gate to prevent stat drift.

## Test Summary
- Verified 615 tests passing.
- Stabilized `tests/progression/test_leveling.py` and `test_attribute_growth.py`.
- Certified strategic cognition tests: `test_access_blocker_resolution`, `test_blocker_inference_and_detour`, `test_detour_completion_and_resumption`.

## Files Changed
- `src/systems/strategic.py`
- `src/engine/pipeline.py`
- `src/engine/evolution.py`
- `tests/progression/test_leveling.py`
- `tests/progression/test_attribute_growth.py`

## Completion Summary
Phase 6 stabilization is complete. The engine now correctly handles strategic blockers and detours with bit-identical parity to V2 laws. Occupancy conflicts no longer cause unrelated data loss, and progression stats are correctly derived from attributes at the final recalculation gate.
