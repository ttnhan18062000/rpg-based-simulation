---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-THREAD-LEAK-CONFTEST
artifact_type: plan
tags: [thread, leak, conftest]
---

# Plan — TCK-20260610-THREAD-LEAK-CONFTEST

## Ordered Steps

### Step 1 — Append session-scoped fixture to tests/conftest.py
**File:** `tests/conftest.py`

Add the following fixture at the end of the file (after line 106):

```python
@pytest.fixture(scope="session", autouse=True)
def _observability_worker_thread_sentinel():
    from tests.tools.memory_probe import count_drain_workers
    before = count_drain_workers()
    yield
    after = count_drain_workers()
    leaked = after - before
    if leaked > 0:
        pytest.fail(
            f"QueueDrainWorker thread leak detected: {leaked} thread(s) remained after test session "
            f"(before={before}, after={after}). "
            "A test created a QueueDrainWorker without calling shutdown(). "
            "Check tests that create Kernel or EventRecorder instances."
        )
```

Key decisions:
- `autouse=True` at session scope wraps the entire test run automatically.
- Only growth triggers failure — pre-existing workers (before > 0) are allowed.
- Uses `count_drain_workers()` from memory_probe.py; counting logic stays in one place.
- `yield`-fixture ensures teardown runs even if tests fail.
- `pytest.fail()` (not `assert`) is correct for conftest-level failures.

## Files to Change
- `tests/conftest.py` — append session fixture (no other changes)

## Explicit Scope Guards (what NOT to touch)
- Do NOT modify `src/observability/queue.py` — no production code changes.
- Do NOT modify `tests/tools/memory_probe.py` — helper already implemented.
- Do NOT add new test files — the sentinel is self-validating.
- Do NOT modify the existing conftest hooks (pytest_addoption, pytest_runtest_setup, etc.).

## Dependency Map
- Step 1 has no dependencies — it is the only step.
- Step 1 depends on `tests/tools/memory_probe.py:count_drain_workers` being available (already implemented by TCK-20260610-MEMORY-DEBUG-TOOL).

## Acceptance Criteria Mapped to Steps
- AC-1 (session fixture counts at start/end): Step 1.
- AC-2 (full suite passes sentinel): Step 1 + confirmed by running scoped tests.
- AC-3 (synthetic test triggers sentinel): Covered by existing test_queue_worker_singleton.py behavior; no new test file needed.
- AC-4 (sentinel does not affect passing tests): Confirmed by running tests — yield fixture and growth-only check ensure no false positives.

## Deviations
(None so far.)
