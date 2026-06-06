# TCK-20260527-COG-CAPACITY-ENFORCEMENT

## Title

Make Capacity Enforcement Unconditional and Testable

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Separate capacity enforcement from strategic mutation, making it unconditional, idempotent, and testable. Ensure that trimming of projects, leads, concerns, and hypotheses is executed deterministically on its cadence, preserving active projects and highest-priority items while emitting trace events.

## Scope

- Decouple capacity enforcement from active strategic updates.
- Implement capacity enforcement during the fused strategic pass on its own cadence.
- Ensure enforcement is deterministic, preserving the active/current project and highest-priority items.
- Emit structured observability trace events when capacity trimming occurs.
- Write comprehensive unit and regression tests verifying correct capacity trimming.

## Out of Scope

- Modifying the core strategic project selection logic.

## Acceptance Criteria

- Cognition capacity limits are enforced unconditionally during `fused_strategic_pass()`. ✅
- Active projects and highest-priority blockers/concerns/leads are preserved during trimming. ✅
- Observatory trace events capture entity ID, trimmed fields, counts before/after, and dropped IDs. ✅
- Unit tests verify idempotent trimming and correct prioritization. ✅

## Related Tickets

- `TCK-20260527-COG-BELIEF-INTEGRATION.md`

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- `staging_artifacts/TCK-20260527-COG-CAPACITY-ENFORCEMENT/`

## Related Code Areas

- `src/systems/strategic_systems/detour.py`
- `src/systems/strategic_systems/intelligence.py`
- `tests/unit/strategic/test_capacity_enforcement.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- `DetourSuggestionSystem.enforce_bandwidth()` in `detour.py` was refactored to trim leads, concerns, hypotheses, and projects — not just leads. Each collection is sorted by priority metric (certainty, urgency, confidence, active_project_id) before trimming.
- `CognitionCapacityTrimmed` observability events are emitted via `logger.debug` with entity ID, before/after counts, and dropped IDs.
- `enforce_bandwidth` is called **unconditionally** inside `fused_strategic_pass()` (section "4. Capacity Enforcement") after all cognition items are accumulated but before navigation decisions. This ensures trimming happens every tick regardless of cadence.
- The call returns a `StrategicUpdate` that is merged into `strat_up` so removals propagate through the standard authoritative apply path.

## Test Summary

- **Tests run**: `tests/unit/strategic/test_capacity_enforcement.py` (11 tests), full strategic suite (135 tests)
- **Tests added**: `test_capacity_enforcement.py` — 11 new tests covering leads/concerns/hypotheses/projects trimming, noop under-limit, active project priority, and unconditional wiring in `fused_strategic_pass`
- **All 135 strategic tests pass** — no regressions

## Files Changed

- `src/systems/strategic_systems/detour.py` — `enforce_bandwidth` refactored to include projects and hypotheses trimming + observability logs
- `src/systems/strategic_systems/intelligence.py` — `fused_strategic_pass` wired to call `enforce_bandwidth` unconditionally (section 4, after intent merge)
- `tests/unit/strategic/test_capacity_enforcement.py` — [NEW] 11-test suite for capacity enforcement

## Completion Summary

Cognition capacity enforcement is now unconditional and runs every tick for every active entity in `fused_strategic_pass`. All four cognition collections (leads, concerns, hypotheses, projects) are capped to their profile limits, with active projects and highest-priority items retained. Observability trace events are emitted on any trim. 135 strategic tests pass cleanly.
