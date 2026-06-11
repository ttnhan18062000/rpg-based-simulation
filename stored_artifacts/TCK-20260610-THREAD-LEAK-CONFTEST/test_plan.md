---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-THREAD-LEAK-CONFTEST
artifact_type: test_plan
tags: [thread, leak, conftest]
---

# Test Plan — TCK-20260610-THREAD-LEAK-CONFTEST

## Regression Surface (existing tests that must pass)
- `tests/unit/test_queue_worker_singleton.py` — exercises QueueDrainWorker lifecycle; must pass cleanly with the sentinel active.
- `tests/unit/test_memory_probe.py` — exercises `count_drain_workers()` directly; sentinel depends on this helper.
- All tests that currently pass must continue to pass — the sentinel fixture must not produce a false positive.

## New Tests Required (per AC)
1. **AC-1 / AC-4**: The session fixture itself is self-validating — it runs as an autouse session fixture and passes as long as thread count does not grow. No separate test file needed for this.
2. **AC-3**: The requirement for a "synthetic test that creates a QueueDrainWorker without stopping it" is covered by the existing `test_queue_worker_singleton.py` (from TCK-20260610-WORKER-SINGLETON-GUARD), which creates and starts workers and verifies `count_drain_workers()` returns non-zero while they run. The sentinel's correctness can be confirmed by verifying the helper returns > 0 during that test but returns 0 after teardown.

## Scoped Pytest Commands
```bash
# Primary: run the tests most directly affected
pytest tests/unit/test_queue_worker_singleton.py tests/unit/test_memory_probe.py -v

# Verification: confirm sentinel passes cleanly with memory_probe tests
pytest tests/unit/test_memory_probe.py -v --tb=short
```

## Anti-Drift Test Guards
- The sentinel fixture is an autouse session fixture, so it runs on every `pytest` invocation over the tests/ tree automatically.
- If a future change renames the thread in `queue.py`, a test that starts a worker and calls `count_drain_workers()` would catch the drift (the count would read 0 when the worker is supposed to be active).
