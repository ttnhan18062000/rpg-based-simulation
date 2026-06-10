# TCK-20260610-WORKER-SINGLETON-GUARD

## Title
Add safeguard against multiple QueueDrainWorker instances attaching to the global queue singleton

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`_global_queue` in `src/observability/queue.py` is a module-level singleton. When multiple `EventRecorder` instances (or multiple `Kernel` instances) are created in the same process without proper teardown, each one creates and starts a new `QueueDrainWorker` — all draining the same global queue concurrently. This amplifies resource usage and means a single logical queue accumulates multiple competing drain loops. The fix is to add a guard: track whether a worker is already running on the global queue and either reuse it or raise a clear error when a second start is attempted.

## Scope
- Add a guard in `src/observability/queue.py` (or `src/observability/event_recorder.py`) that prevents more than one active `QueueDrainWorker` from draining the global queue at a time
- Preferred approach: track a module-level `_global_worker` reference alongside `_global_queue`; if a worker is already started, return the existing one instead of creating a new one
- If an explicit "replace" is needed, the old worker must be stopped before the new one starts
- Add a function `get_active_worker_count() -> int` (or similar introspection helper) to make the guard testable
- Update unit test for `QueueDrainWorker` to cover the guard path

## Out of Scope
- Fixing missing `shutdown()` calls in tests (see TCK-20260610-KERNEL-TEST-TEARDOWN)
- Thread-count monitoring at the pytest conftest level (see TCK-20260610-THREAD-LEAK-CONFTEST)
- Changing the bounded queue capacity or drain behaviour
- Changing the `EventRecorder` per-instance queue (only the global-queue path is in scope)

## Acceptance Criteria
- [ ] Creating two `EventRecorder` instances backed by the global queue does not result in two concurrent `QueueDrainWorker` threads running on the same queue
- [ ] A new unit test asserts that a second `start()` on the same global queue either reuses the existing worker or raises a descriptive `RuntimeError`
- [ ] `get_active_worker_count()` (or equivalent) returns 1 after two recorders are created, not 2
- [ ] Existing worker tests remain green

## Related Tickets
- TCK-20260610-KERNEL-TEST-TEARDOWN
- TCK-20260610-THREAD-LEAK-CONFTEST

## Related Docs
- None.

## Related Stored Artifacts
None.

## Related Code Areas
- `src/observability/queue.py`
- `src/observability/event_recorder.py`
- `tests/unit/` (any existing QueueDrainWorker unit tests)

## Assumptions / Open Questions
- The module-level singleton pattern is intentional (shared across all recorders in a process); this ticket does not remove it, only guards it.
- If `EventRecorder` uses a per-instance queue (not the global one), the guard applies at the EventRecorder level only for global-queue-backed recorders.
- The exact API for the guard (module-level registry vs. class-level counter) is left to the implementer to decide based on the current structure.

## Implementation Notes

Investigation revealed that `EventRecorder` uses a per-instance `BoundedObservabilityQueue`, not the global one. The guard was therefore placed entirely in `src/observability/queue.py` at the module level, alongside the existing `_global_queue` / `_queue_lock` pattern. `EventRecorder` was not modified.

Added to `queue.py`:
- `QueueDrainWorker.is_alive()` — delegates to `self._thread.is_alive()`.
- `_global_worker: Optional[QueueDrainWorker] = None` module-level singleton.
- `_global_worker_lock = threading.Lock()` to guard check-and-start atomically.
- `get_or_start_global_worker(queue)` — returns alive worker or starts a new one; lock held for the full check-and-start sequence.
- `get_active_global_worker_count() -> int` — returns 1 if alive, else 0; used in tests.

## Test Summary

5 new tests in `tests/unit/test_queue_worker_singleton.py`:
- `test_global_worker_singleton` — two calls return the same object; count == 1.
- `test_global_worker_reused_on_second_start` — identity check on repeated calls.
- `test_global_worker_restarted_when_dead` — dead worker is replaced on next call.
- `test_zero_when_no_worker` — count == 0 when `_global_worker` is None.
- `test_one_when_worker_alive` — count == 1 after start.

All 13 tests passed (5 new + 4 existing queue tests + 4 existing memory probe tests).

## Files Changed

- `src/observability/queue.py` — added `is_alive()`, `_global_worker`, `_global_worker_lock`, `get_or_start_global_worker()`, `get_active_global_worker_count()`
- `tests/unit/test_queue_worker_singleton.py` — new test file (5 tests)
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-179

## Completion Summary

Added module-level global worker singleton guard to `src/observability/queue.py`. The `get_or_start_global_worker()` function uses a threading.Lock to ensure only one `QueueDrainWorker` can be alive on the global queue at a time. A dead worker is safely replaced. The `EventRecorder` per-instance path was confirmed to be unaffected (it uses its own queue). Parity ledger entry INFRA-179 added. All tests green.
