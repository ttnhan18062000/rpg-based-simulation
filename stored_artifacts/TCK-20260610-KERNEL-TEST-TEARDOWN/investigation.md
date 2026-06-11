---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-KERNEL-TEST-TEARDOWN
artifact_type: investigation
tags: [kernel, test, teardown]
---

# Investigation — TCK-20260610-KERNEL-TEST-TEARDOWN

## Per-File Audit Table

| File | Creates Kernel/EventRecorder | Has shutdown? | Fix needed? | Notes |
|---|---|---|---|---|
| `tests/perf/test_profiler_integrity.py` | YES — `Kernel(...)` inline in `test_recorded_tick_compute_includes_all_phases` | NO | YES | Three other tests use `BenchHarness.run_benchmark()` which also creates a Kernel but never calls shutdown |
| `tests/perf/test_dirty_parity.py` | YES — `kernel_opt` and `kernel_ref` both created inline in `test_dirty_set_vs_full_scan_parity` | NO | YES | Two kernels, neither shut down |
| `tests/perf/test_dirty_set_integrity.py` | YES — `kernel_with_audit` fixture returns a `Kernel(...)` | NO | YES | Fixture is a plain `return`, not a `yield` fixture |
| `tests/arena/test_arena_tactics.py` | YES — `baseline_kernel` created inline inside failure-path `if not result.conformance_passed:` block | NO | YES | Main `harness.run_scenario()` calls `kernel.shutdown()` internally; only the inline fallback kernel leaks |
| `tests/unit/core/test_catalog_smoke_simulation.py` | YES — `kernel = Kernel(...)` inline in `test_catalog_mode_smoke_simulation` | NO | YES | No teardown at all |
| `tests/unit/core/test_operational_flags.py` | YES — `kernel`, `k1`, `k2` all created inline | NO | YES | Three kernels across two tests: `test_safe_operational_flags_accepted` (1), `test_flags_cannot_alter_authoritative_semantics` (2) |
| `tests/unit/core/test_engine_integrity.py` | YES — `kernel1`, `kernel2` in `test_bit_identical_determinism`; `kernel` in `test_isolation_guard_trigger` | NO | YES | Three kernels across two tests |
| `tests/unit/core/test_signal_truth.py` | YES — `kernel` created inline in all four test functions | NO | YES | Four tests, each creates a `Kernel(...)` with no teardown |
| `tests/unit/resource/test_resource_intelligence_contract.py` | YES — `kernel` fixture returns `Kernel(...)` | NO | YES | Plain `return` fixture shared by three tests |
| `tests/unit/kernel/test_worker_equivalence.py` | YES — `dual_kernel_setup` fixture creates two kernels; `test_zero_worker_fallback_equivalence` creates two more inline | NO | YES | Four kernels total, none shut down |
| `tests/unit/kernel/test_replay_determinism.py` | YES — `kernel` and `kernel2` created inline in `test_transaction_trace_determinism` | NO | YES | Two kernels, neither shut down |

## Current Behavior of Kernel.shutdown()

`Kernel.shutdown()` (kernel.py:792) does the following in order:
1. Sets `self._stopped = True`
2. Calls `self._worker_manager.shutdown()` — stops the `ConcurrentExecutionAdapter` thread pool
3. If `_event_recorder` exists: calls `self._event_recorder.shutdown()` — stops the `QueueDrainWorker` thread, flushes remaining queue items, closes the JSONL file handle
4. If `_metric_recorder` exists: calls `self._metric_recorder.shutdown(tick)` — flushes metric telemetry
5. Computes final canonical hash, calls `self._replay.finalize()`, updates artifact repo manifest
6. Calls `self._cache_registry.clear_all()`

`EventRecorder.shutdown()` (event_recorder.py:155):
1. Calls `self._worker.stop()` — sets `running=False`, joins the `QueueDrainWorker` daemon thread with 1s timeout
2. Drains remaining queue items and flushes to file/stream
3. Closes the file handle

The daemon thread (`name="observability-drain-worker"`) is created at `EventRecorder.__init__` time (queue.py:112) and started immediately if `enabled=True`. Without `shutdown()`, the thread remains alive for the process lifetime but since it is a daemon it is reaped only when the main thread exits — across the full test suite, this means all worker threads from all prior tests are still running until the suite ends.

## Risks and Anti-Drift Hazards

- **Thread accumulation**: Each un-shut-down `Kernel` leaves one `QueueDrainWorker` daemon thread alive. Across 11 files × multiple tests this easily exceeds 20 concurrent threads, each sleeping in a loop and draining a shared `BoundedObservabilityQueue`. This causes measurable memory pressure and can cause MemoryError on long suite runs.
- **File handle leaks**: Any test that supplies a `run_dir` to `EventRecorder` will leave an unclosed JSONL file handle. Current tests pass no `run_dir` so this is low risk, but the pattern is fragile.
- **`BenchHarness` does not call shutdown**: `BenchHarness.run_benchmark()` creates a `Kernel` and discards it. Tests that use `BenchHarness` are affected the same way. Three tests in `test_profiler_integrity.py` use `BenchHarness`; these are fixed by adding a `shutdown()` call inside `BenchHarness.run_benchmark()` after the sampling phase — but that is out of scope for this ticket (it touches production code). Instead, the tests themselves should not be expected to call shutdown for the harness-managed kernel; those three tests are exempt. Only `test_recorded_tick_compute_includes_all_phases` creates a kernel directly and needs a fix.
- **Fixture-based kernels**: Two fixtures (`kernel_with_audit` in `test_dirty_set_integrity.py`, `kernel` in `test_resource_intelligence_contract.py`) use plain `return`. These must be converted to `yield` fixtures.
- **`dual_kernel_setup` fixture** in `test_worker_equivalence.py`: Creates two kernels. Both must be shut down in the fixture cleanup.
- **`test_arena_tactics.py`**: The `baseline_kernel` is only created inside the `if not result.conformance_passed:` branch. Under normal test-pass conditions this branch is never entered, so the leak is conditional. Still requires a fix for correctness.
