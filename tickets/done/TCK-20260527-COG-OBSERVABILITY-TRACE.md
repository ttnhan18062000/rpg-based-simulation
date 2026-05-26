# TCK-20260527-COG-OBSERVABILITY-TRACE

## Title

Upgrade Observability to Provide Cognition-to-Action Trace and Causal Trace Fields

## Status

DONE

## Request Summary

Make strategic observability prove behavior rather than just exposing state. Connect state changes to behavioral consequences by adding causal trace fields to the strategic project changed events, mapping resulting actions and positions, and adding automated tests for diagnostic trace validation.

## Scope

- Add `source_goal_score`, `resulting_action`, and `target_pos` causal trace fields to `StrategicProjectChanged` event schema in `src/observability/cognition/events.py`.
- Update `build_snapshot_record` in `src/observability/cognition/schema.py` and `record_tick` in `src/observability/cognition/recorder.py` to extract and populate these causal trace fields.
- Update `map_diff_to_events` in `src/observability/cognition/event_mapper.py` to resolve and map these fields dynamically.
- Write unit and integration tests under `tests/unit/strategic/test_cognition_causal_trace.py` to verify trace extraction and message formatting.

## Out of Scope

- Introducing new database schemas or non-cognition events.
- Creating a separate frontend visualization dashboard.

## Acceptance Criteria

- `StrategicProjectChanged` contains the three causal fields (`source_goal_score`, `resulting_action`, `target_pos`).
- Diagnostic event message formatting outputs the fields when they are present.
- Unit tests verify transition bounds and ensure all strategic test suites pass.

## Related Tickets

- None

## Related Docs

- `entity_cognition_fix_phase0.md` (Task 9)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/cognition/events.py`
- `src/observability/cognition/schema.py`
- `src/observability/cognition/recorder.py`
- `src/observability/cognition/event_mapper.py`
- `tests/unit/strategic/test_cognition_causal_trace.py`

## Assumptions / Open Questions

- Causal field mapping targets the primary entity active state structure in a single tick boundary.

## Implementation Notes

- Python Enum f-string prints their string values using `.value` to prevent raw enum representation.
- Mocking requires `set_override_mode` for the `ObservabilityConfig` to run safely.

## Test Summary

- Enriched strategic cognition causal trace tests pass: `pytest tests/unit/strategic/test_cognition_causal_trace.py` successfully completed.

## Files Changed

- `src/observability/cognition/events.py`
- `src/observability/cognition/schema.py`
- `src/observability/cognition/recorder.py`
- `src/observability/cognition/event_mapper.py`
- `tests/unit/strategic/test_cognition_causal_trace.py`

## Completion Summary

- Implemented full trace propagation for cognition-to-action changes. Added target position, source goal score, and resulting action to the active strategic project transition events. Added test suite covering direct verification of transition bounds. All tests pass successfully.
