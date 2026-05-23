# test_plan.md - Safety & Parity Tests

- `tests/certification/test_cognition_observability_parity.py`:
  - Run identical simulation seed and assert 100% parity of the final state hash when snapshot recorder is active vs inactive.
- `tests/perf/test_cognition_observability_overhead.py`:
  - Run a 100-entity, 100-tick simulation under LIGHT mode and measure total overhead to confirm it is under the budget threshold.
- `tests/unit/observability/cognition/test_cognition_false_positive_guards.py`:
  - Validate that temporary blockers or single lead exhaustions do not trigger false anomalies.
- `tests/integration/observability/test_cognition_observability_e2e.py`:
  - A full end-to-end integration test asserting the entire pipeline (capture -> diff -> event -> feature -> report -> CLI) executes flawlessly.
