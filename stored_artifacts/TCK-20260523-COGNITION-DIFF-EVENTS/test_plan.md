# test_plan.md - Diff & Event Tests

## Unit Tests
- `tests/unit/observability/cognition/test_cognition_graph_diff_builder.py`:
  - Verify same graph produces empty diff.
  - Verify added blocker node is detected.
  - Verify changed current project metadata is detected.
  - Verify deterministic key ordering of final output.
- `tests/unit/observability/cognition/test_cognition_event_mapper.py`:
  - Assert that strategic transitions correctly emit corresponding SimulationEvents.

## Integration Tests
- `tests/integration/observability/test_cognition_events_recorded.py`:
  - Run a mock simulation with project changes and verify events are logged to `simulation_events.jsonl`.
