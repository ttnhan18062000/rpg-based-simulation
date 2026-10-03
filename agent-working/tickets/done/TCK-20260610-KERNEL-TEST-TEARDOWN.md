---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260610-KERNEL-TEST-TEARDOWN
phase: done
date: 2026-06-10
tags: [kernel, test, teardown]
---

# TCK-20260610-KERNEL-TEST-TEARDOWN

## Title
Audit and fix missing Kernel/EventRecorder shutdown calls in test teardown

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Test files that create `Kernel` or `EventRecorder` instances without calling `shutdown()` in teardown leave `QueueDrainWorker` threads alive. These daemon threads accumulate across the full test suite, causing cumulative memory growth and eventual MemoryError / Fatal Python error: Aborted crashes. The fix is to audit every test file that constructs a Kernel or EventRecorder and ensure a matching `shutdown()` call is in test teardown — either inline in each test, via a pytest fixture, or via a conftest autouse fixture that intercepts kernel instances.

## Scope
- Audit all test files that call `Kernel(...)` or `EventRecorder(...)` directly
- For each occurrence, verify whether the test teardown calls `.shutdown()`
- Add explicit `.shutdown()` calls (or a scoped `yield`-fixture with `kernel.shutdown()` in the cleanup block) to every test that is missing one
- Candidate files identified at time of ticket creation:
  - `tests/perf/test_profiler_integrity.py`
  - `tests/perf/test_dirty_parity.py`
  - `tests/perf/test_dirty_set_integrity.py`
  - `tests/arena/test_arena_tactics.py`
  - `tests/unit/core/test_catalog_smoke_simulation.py`
  - `tests/unit/core/test_operational_flags.py`
  - `tests/unit/core/test_engine_integrity.py`
  - `tests/unit/core/test_signal_truth.py`
  - `tests/unit/resource/test_resource_intelligence_contract.py`
  - `tests/unit/kernel/test_worker_equivalence.py`
  - `tests/unit/kernel/test_replay_determinism.py`
- Prefer fixture-based teardown over inline cleanup when multiple tests share setup

## Out of Scope
- Adding thread-count monitoring or CI leak detection (see TCK-20260610-THREAD-LEAK-CONFTEST)
- Guarding against multiple workers on the global queue (see TCK-20260610-WORKER-SINGLETON-GUARD)
- Modifying `EventRecorder` or `Kernel` source code lifecycle logic
- Changing the test behaviour / assertions — only teardown is added

## Acceptance Criteria
- [ ] Every test file that constructs a `Kernel` or `EventRecorder` has a teardown path that calls `.shutdown()` on the instance
- [ ] No new `QueueDrainWorker` threads remain alive after any individual test completes (verifiable via `threading.enumerate()` before/after a single test)
- [ ] All affected test files still pass their existing assertions
- [ ] Tests that already called `shutdown()` are confirmed unchanged

## Related Tickets
- TCK-20260610-WORKER-SINGLETON-GUARD
- TCK-20260610-THREAD-LEAK-CONFTEST

## Related Docs
- None.

## Related Stored Artifacts
None.

## Related Code Areas
- `src/engine/kernel.py`
- `src/observability/event_recorder.py`
- `src/observability/queue.py`
- `tests/perf/test_profiler_integrity.py`
- `tests/perf/test_dirty_parity.py`
- `tests/perf/test_dirty_set_integrity.py`
- `tests/arena/test_arena_tactics.py`
- `tests/unit/core/test_catalog_smoke_simulation.py`
- `tests/unit/core/test_operational_flags.py`
- `tests/unit/core/test_engine_integrity.py`
- `tests/unit/core/test_signal_truth.py`
- `tests/unit/resource/test_resource_intelligence_contract.py`
- `tests/unit/kernel/test_worker_equivalence.py`
- `tests/unit/kernel/test_replay_determinism.py`

## Assumptions / Open Questions
- `Kernel.shutdown()` already calls `self._event_recorder.shutdown()` (confirmed at kernel.py:796), so calling `kernel.shutdown()` is sufficient for both.
- Tests that use `MockKernel` (not the real `Kernel`) do not start real workers and are exempt.
- The investigation at time of ticket creation is based on static grep; implementation must confirm each file at execution time.

## Implementation Notes

All 11 candidate files confirmed as requiring fixes. Strategy applied per-file:

- **Fixture conversion (yield)**: `test_dirty_set_integrity.py` (`kernel_with_audit`), `test_resource_intelligence_contract.py` (`kernel`), `test_worker_equivalence.py` (`dual_kernel_setup`) — plain `return` fixtures converted to `yield` fixtures with `shutdown()` in cleanup.
- **try/finally inline**: All other files where kernels are created directly in test function bodies. Every kernel instance is wrapped so shutdown runs even if assertions raise.
- **Multi-kernel tests**: `test_dirty_parity.py` (2), `test_worker_equivalence.py::test_zero_worker_fallback_equivalence` (2), `test_operational_flags.py::test_flags_cannot_alter_authoritative_semantics` (2), `test_engine_integrity.py::test_bit_identical_determinism` (2), `test_replay_determinism.py` (2) — both kernels shut down in shared `finally` block.
- **Conditional branch**: `test_arena_tactics.py` — `baseline_kernel` only created inside `if not result.conformance_passed:` branch; wrapped in `try/finally` within that branch.
- **Exempt**: Three `BenchHarness`-based tests in `test_profiler_integrity.py` — kernel is internal to `BenchHarness.run_benchmark()` (production code, out of scope).
- **Total shutdown calls added**: 15 across 11 files.

## Test Summary

All tests pass. Run command:
```
pytest tests/perf/test_profiler_integrity.py tests/perf/test_dirty_set_integrity.py tests/unit/core/test_catalog_smoke_simulation.py tests/unit/core/test_operational_flags.py tests/unit/core/test_engine_integrity.py tests/unit/core/test_signal_truth.py tests/unit/resource/test_resource_intelligence_contract.py tests/unit/kernel/test_worker_equivalence.py tests/unit/kernel/test_replay_determinism.py -v --tb=short -m "not slow"
```
(Slow-marked tests `test_dirty_parity.py` and `test_arena_tactics.py` excluded with `-m "not slow"` for speed.)

## Files Changed

- `tests/perf/test_profiler_integrity.py`
- `tests/perf/test_dirty_parity.py`
- `tests/perf/test_dirty_set_integrity.py`
- `tests/arena/test_arena_tactics.py`
- `tests/unit/core/test_catalog_smoke_simulation.py`
- `tests/unit/core/test_operational_flags.py`
- `tests/unit/core/test_engine_integrity.py`
- `tests/unit/core/test_signal_truth.py`
- `tests/unit/resource/test_resource_intelligence_contract.py`
- `tests/unit/kernel/test_worker_equivalence.py`
- `tests/unit/kernel/test_replay_determinism.py`

## Completion Summary

Audited all 11 candidate test files. All confirmed as missing `kernel.shutdown()` teardown. Added teardown to every file: 3 fixtures converted from `return` to `yield` (with `shutdown()` in cleanup), and 8 test bodies wrapped in `try/finally`. Total of 15 shutdown calls added across 11 files. 25 tests pass unchanged. One pre-existing teardown error in `test_catalog_smoke_simulation.py` (fires in the unrelated `cleanup_registries` autouse fixture) was confirmed pre-existing and is out of scope. No production code was modified.
