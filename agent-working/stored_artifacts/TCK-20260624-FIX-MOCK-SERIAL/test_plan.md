# Test Plan: TCK-20260624-FIX-MOCK-SERIAL

## Scoped Pytest Command (Primary — 7 target tests)
```bash
python3 -m pytest \
  tests/unit/core/test_operational_flags.py::test_flags_cannot_alter_authoritative_semantics \
  tests/unit/core/test_signal_truth.py::test_signal_truth_dropped_work \
  tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative \
  tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update \
  "tests/integration/kernel/test_kernel_boundaries.py::test_hook_isolation_from_authoritative_state" \
  "tests/integration/kernel/test_kernel_boundaries.py::test_authoritative_hash_purity" \
  tests/integration/kernel/test_simulation_kernel_contract.py::test_kernel_tick_execution_order \
  -v --tb=short 2>&1 | tail -40
```

## Cascade Tests (5 teardown-error tests that should clear)
```bash
python3 -m pytest \
  tests/unit/resource/test_transaction_grouping.py::test_group_failure_rollback \
  tests/unit/certification/test_catalog_scenario_state_builder.py::test_tick_zero_entities_alive \
  tests/unit/runtime/test_registry_bootstrap_modes.py::test_content_source_report_is_frozen \
  tests/docs/test_doc_integrity.py::test_link_integrity \
  tests/integration/perf/test_phase10_graceful_degradation.py::test_recovery_from_degraded_to_normal_when_pressure_drops \
  -v --tb=short 2>&1 | tail -20
```

## Expected Results
- All 7 primary tests: PASSED
- All 5 cascade tests: PASSED (no teardown ERRORs)
- No QueueDrainWorker thread leak warnings

## Regression Scope
- Only test files modified; no production source changes.
- Run full signal_truth file to verify other tests still pass:
  `python3 -m pytest tests/unit/core/test_signal_truth.py -v`
- Run full kernel_boundaries file:
  `python3 -m pytest tests/integration/kernel/test_kernel_boundaries.py -v`
