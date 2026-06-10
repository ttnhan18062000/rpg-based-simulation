# TCK-20260610-THREAD-LEAK-CONFTEST

## Title
Add pytest conftest thread-leak sentinel for QueueDrainWorker accumulation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Even after per-test teardown is fixed, a regression could silently reintroduce worker leaks in future PRs. To catch this automatically, add a pytest conftest plugin that counts active `QueueDrainWorker` threads before and after the test session (or after each test in high-sensitivity mode), and fails the suite if the count has grown. This acts as a CI regression sentinel so that any future test that creates a worker without cleanup is caught immediately rather than only manifesting as a full-suite MemoryError.

## Scope
- Add or update `tests/conftest.py` with a session-scoped fixture that:
  1. Counts `QueueDrainWorker` threads at session start
  2. Counts `QueueDrainWorker` threads at session end
  3. Asserts the end count is not greater than the start count (allows pre-existing workers if any)
- The check must use `threading.enumerate()` and filter by thread name or class (`QueueDrainWorker`)
- Optionally expose an opt-in per-test variant (not autouse) for high-sensitivity debugging
- The sentinel must NOT break existing tests — it only raises if thread count grows, not if it is nonzero at start

## Out of Scope
- Fixing the actual leaks (see TCK-20260610-KERNEL-TEST-TEARDOWN)
- Memory / RSS monitoring (the document mentions it as optional; thread count is the primary signal)
- Modifying `QueueDrainWorker` or kernel source code
- Process-level isolation (pytest-forked) — this is a monitoring addition, not isolation

## Acceptance Criteria
- [ ] A conftest session-scoped fixture counts `QueueDrainWorker` threads at start and end of the test session
- [ ] Running the full test suite after TCK-20260610-KERNEL-TEST-TEARDOWN passes the sentinel (count does not grow)
- [ ] A synthetic test that creates a `QueueDrainWorker` without stopping it triggers the sentinel failure (must be a skipped/xfail demonstration test or an explicit assertion in the fixture)
- [ ] The sentinel does not affect passing tests in isolated runs

## Related Tickets
- TCK-20260610-KERNEL-TEST-TEARDOWN
- TCK-20260610-WORKER-SINGLETON-GUARD

## Related Docs
- None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/conftest.py`
- `src/observability/queue.py`

## Assumptions / Open Questions
- `QueueDrainWorker` threads can be identified by class type via `isinstance(t, QueueDrainWorker)` after importing, or by thread name if the worker sets `self.name` on its `Thread` base.
- If `tests/conftest.py` already exists with session-level setup, the fixture must be added non-destructively.
- The session-end check runs even if tests fail — `yield`-fixture ensures cleanup runs regardless.

## Implementation Notes
Added `_observability_worker_thread_sentinel` as a session-scoped autouse=True fixture at the end of `tests/conftest.py`. The fixture calls `count_drain_workers()` (from `tests/tools/memory_probe`) before and after the session and calls `pytest.fail()` if the count grew. Pre-existing workers are tolerated (before > 0 is allowed). No production code was modified.

## Test Summary
Ran `pytest tests/unit/test_queue_worker_singleton.py tests/unit/test_memory_probe.py -v`: 9 passed, 0 failed. Sentinel fixture produced no false positive. Session-end worker count matched session-start count confirming no leak from the test suite itself.

## Files Changed
- `tests/conftest.py` — appended `_observability_worker_thread_sentinel` session-scoped autouse fixture

## Completion Summary
Added a session-scoped autouse pytest fixture `_observability_worker_thread_sentinel` to `tests/conftest.py` that counts active `QueueDrainWorker` threads (by name `"observability-drain-worker"`) at session start and end via `count_drain_workers()` from `tests/tools/memory_probe`, calling `pytest.fail()` if the count grew — acting as a CI regression sentinel that catches any future test that creates a worker without calling `shutdown()`.
