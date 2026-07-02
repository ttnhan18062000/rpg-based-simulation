---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-OBS-QUEUE
artifact_type: test_plan
tags: [observability, thread-leak, SIGABRT, test-repair]
---

# Test Plan — TCK-20260623-FIX-OBS-QUEUE

---

## Objective

Verify that:
1. The two identified test files no longer leak `QueueDrainWorker` threads
2. The full test suite completes without SIGABRT (exit code 0 or test failures, not 134)
3. No regression in existing observability tests

---

## Pre-fix Baseline (Expected Current Behavior)

```bash
# Confirm thread leak is present before fix
pytest tests/unit/kernel/test_replay_contract.py -v --tb=short
# After test: one "observability-drain-worker" thread still alive in process

pytest tests/perf/test_concurrency_parity.py -v --tb=short
# After test: multiple "observability-drain-worker" threads still alive
```

Use `count_drain_workers()` from `tests/tools/memory_probe.py` to confirm delta > 0 pre-fix.

---

## Verification Steps

### Step 1 — Unit-level thread leak verification (post-fix)

Run the two fixed files in isolation and confirm zero thread delta:

```bash
pytest tests/unit/kernel/test_replay_contract.py -v --tb=short
pytest tests/perf/test_concurrency_parity.py -v --tb=short
```

Expected: both pass, no SIGABRT, no sentinel warning.

### Step 2 — Observability regression suite

Confirm existing observability tests are unaffected:

```bash
pytest tests/unit/observability/ -v --tb=short
pytest tests/integration/observability/ -v --tb=short
pytest tests/unit/test_queue_worker_singleton.py -v --tb=short
pytest tests/unit/test_memory_probe.py -v --tb=short
```

Expected: all pass, zero worker thread delta per the conftest sentinel.

### Step 3 — Kernel/lifecycle regression

```bash
pytest tests/unit/kernel/ -v --tb=short
pytest tests/unit/core/test_graceful_shutdown.py -v --tb=short
pytest tests/unit/engine/test_lifecycle_supervisor.py -v --tb=short
```

Expected: all pass.

### Step 4 — Conftest sentinel fires cleanly

The session-scoped `_observability_worker_thread_sentinel` fixture in `tests/conftest.py:110`
calls `count_drain_workers()` before and after the session. Run the combined set to exercise it:

```bash
pytest tests/unit/kernel/ tests/unit/observability/ tests/perf/test_concurrency_parity.py -v --tb=short
```

Expected: no sentinel failure message ("QueueDrainWorker thread leak detected").

### Step 5 — Full suite smoke run (primary acceptance criterion)

```bash
pytest tests/ -m "not slow" -q --tb=no -x
```

Expected: completes without exit code 134 (SIGABRT). Exit code 0 or non-zero due to
pre-existing test failures is acceptable — the crash itself must not occur.

If the full suite is too slow for CI verification, run by subdirectory:

```bash
pytest tests/unit/ -q --tb=no
pytest tests/integration/ -q --tb=no
pytest tests/engine/ -q --tb=no
pytest tests/perf/ -q --tb=no -m "not slow"
```

---

## Thread Count Assertion (optional inline check)

To instrument the fix with an explicit thread count assertion, add to each fixed test:

```python
from tests.tools.memory_probe import count_drain_workers

def test_replay_is_non_authoritative(tmp_path):
    before = count_drain_workers()
    kernel = Kernel(...)
    try:
        ...
    finally:
        kernel.shutdown()
    after = count_drain_workers()
    assert after <= before, f"Thread leak: before={before} after={after}"
```

This is optional — the conftest sentinel already catches this session-wide.

---

## Scope of Test Changes

| File | Change Type |
|------|-------------|
| `tests/unit/kernel/test_replay_contract.py` | Add `try/finally` + `kernel.shutdown()` around `test_replay_is_non_authoritative` |
| `tests/perf/test_concurrency_parity.py` | Add `try/finally` + `kernel_loc.shutdown()` / `kernel_con.shutdown()` in `run_parity_check` |

No changes to production code, conftest, or other test files.

---

## Regression Risk

Low. The fix adds teardown calls that already exist in the `Kernel.shutdown()` contract.
The only risk is if a test asserts on post-shutdown state — review both files to confirm
no assertions occur after the `finally` block. The `test_replay_is_non_authoritative` test
makes all assertions before shutdown; `run_parity_check` returns hash values computed before
shutdown, so both are safe.
