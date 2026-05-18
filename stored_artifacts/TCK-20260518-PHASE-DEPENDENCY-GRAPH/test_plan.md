# Phase Dependency Graph Verification Plan

## Unit Testing
Executed `pytest tests/unit/optimization/test_phase_dependency_graph.py`:
- `test_phase_metadata_definitions`: Verified all 17 phases are registered.
- `test_should_run_must_run_phases`: Verified unconditional execution of required phases.
- `test_force_full_scan_overrides_skips`: Verified full scan overrides.
- `test_cadence_gating_prevention`: Verified cadence gating.
- `test_dirty_set_short_circuiting`: Verified domain-based skipping.
**Status: 5/5 PASSED (0.29s)**

## Integration Parity Testing
Executed `pytest tests/integration/optimization/test_phase_skip_parity.py`:
- Ran identical 10-tick multi-domain scenarios with dynamic phase skipping enabled vs disabled (`force_full_scan=True`).
- Asserted 100% exact simulation state hash parity across all entity attributes and navigation coordinates.
- Asserted non-zero `phase_skips` recorded in `StateUpdate.metric_counters` during the optimized run.
**Status: 1/1 PASSED (0.24s)**

## Full Regression Testing
Executed `pytest tests/unit/optimization/ tests/integration/optimization/`:
**Status: 82/82 PASSED (0.72s)**
