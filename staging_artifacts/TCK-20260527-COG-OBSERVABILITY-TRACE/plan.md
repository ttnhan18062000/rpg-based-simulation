# Implementation Plan - Observability Trace (Task 9)

## Proposed Changes

- Add causal fields `source_goal_score`, `resulting_action`, and `target_pos` to `StrategicProjectChanged` model in `src/observability/cognition/events.py`.
- Update mapping and serialization pipelines in `src/observability/cognition/event_mapper.py`, `schema.py`, and `recorder.py` to extract these fields.
- Add trace testing in `tests/unit/strategic/test_cognition_causal_trace.py`.

## Verification Plan

Run the newly created unit/integration test suite:
`pytest tests/unit/strategic/test_cognition_causal_trace.py`
