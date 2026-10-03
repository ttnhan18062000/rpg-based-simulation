# Test Plan — TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER

## Real evidence
- `tests/unit/resource/test_resource_governor_contract.py::
  test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure` — real, uninstrumented
  `Kernel` with `max_worker_count=0`, 5 real ticks, confirms `RuntimeMode.NORMAL` throughout.
  Manually confirmed via a standalone repro script before/after: DEGRADED every tick before the
  fix, NORMAL every tick after.
- `tests/unit/kernel/test_worker_bounds.py::test_worker_utilization_is_zero_when_workers_disabled`
  — direct `WorkerManager.get_stats()` unit check.
- `tests/unit/kernel/test_worker_bounds.py::
  test_worker_utilization_reflects_real_saturation_when_workers_enabled` — real thread-barrier
  saturation of 2 real workers, confirms `worker_utilization == 1.0` still reported accurately
  (normal-case unregressed).

## Regression suites run
- `tests/unit/resource/`, `tests/unit/kernel/`, `tests/unit/engine/` (`-m "not slow and not
  extra_slow"`) — 361 passed, 2 skipped.
- `tests/unit/engine/test_scenario_runtime_service.py`,
  `tests/unit/engine/test_scenario_checkpointer.py` — 41 passed, 1 skipped (the 2 of 3 real
  `max_worker_count=0` call sites with dedicated test files).
- `tests/cli/test_infra_isolation.py` (the `BROKER_DISABLED=1` real call site) — 4 passed.

## Acceptance criteria mapping
- Real, uninstrumented run with `max_worker_count=0` starts in and stays in `RuntimeMode.NORMAL`
  absent real pressure → done, the new Kernel-level test.
- Fix scoped to the correct layer with rationale recorded → `WorkerManager.get_stats()`, per the
  investigation's consumer-grep (only the governor decides on this value; every other consumer
  just displays it, so fixing the source is correct for all of them).
- Normal (`max_workers > 0`) worker-pressure escalation confirmed unregressed → done, the real
  thread-barrier saturation test.
- All 3 real call sites confirmed correctly governed → done, all three test suites pass.
