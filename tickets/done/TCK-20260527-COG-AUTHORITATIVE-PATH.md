# TCK-20260527-COG-AUTHORITATIVE-PATH

## Title

Establish single authoritative strategic planning path and clarify cognition-to-action boundaries

## Status

DONE

## Request Summary

Ensure that strategic decisions are handled exclusively by the pipeline-level `StrategicIntelligenceSystem.fused_strategic_pass()`, and that `CognitionDomain.execute_brain()` acts solely as a read-only tactical/appraisal provider. Document boundaries clearly and add verification tests.

## Scope

- Add clear code comments detailing strategic planning, emotional appraisal, tactical decision, and action execution boundaries.
- Add tests to `tests/unit/strategic/test_cognition_authoritative_path.py` to prove:
  - Each entity receives exactly one strategic decision update per strategic tick.
  - Tactical decisions consume the selected strategic state, rather than a parallel cognition output.

## Out of Scope

- Modifying core pathfinding grid logic or spatial query caching.
- Restructuring the RabbitMQ background distribution worker.

## Acceptance Criteria

- `CognitionDomain.execute_brain` remains read-only to strategic updates (`strategic=None`).
- Tactical decision makers use `entity.strategic.current_project_id` to steer behavior.
- All tests in `tests/unit/strategic/test_cognition_authoritative_path.py` pass without regression.

## Related Tickets

- `TCK-20260527-COG-ENUM-DRIFT` (Done)

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/engine/domain/cognition.py`
- `src/systems/strategic_systems/intelligence.py`
- `tests/unit/strategic/test_cognition_authoritative_path.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Added `test_single_strategic_update_per_tick` and `test_tactical_consumes_selected_strategic_state` to `tests/unit/strategic/test_cognition_authoritative_path.py`.
- verified all 139 strategic unit tests passed.

## Files Changed

- `src/engine/domain/cognition.py`
- `src/engine/tactical.py`
- `tests/unit/strategic/test_cognition_authoritative_path.py`

## Completion Summary

- Added block comments in `cognition.py` and `tactical.py` clearly demarcating strategic planning, emotional appraisal, tactical decisions, and action boundaries.
- Implemented and successfully ran new unit tests verifying the single authoritative strategic pass and tactical consumption of strategic state.
