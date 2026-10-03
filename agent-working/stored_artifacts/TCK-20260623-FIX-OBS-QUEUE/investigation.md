---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-OBS-QUEUE
artifact_type: investigation
tags: [observability, thread-leak, SIGABRT, queue, kernel, test-repair]
---

# Investigation — TCK-20260623-FIX-OBS-QUEUE

PHASE_TS: 2026-06-23T23:03:47Z

---

## Thread Lifecycle — How Workers Start

`QueueDrainWorker` is defined in `src/observability/queue.py`.

**Creation path 1 — per-instance (primary source of leaks):**
`EventRecorder.__init__()` (line 99) creates a private `QueueDrainWorker` tied to its own
`BoundedObservabilityQueue`. The worker is started immediately if `self.enabled` is True (line 104-105).
`Kernel.__init__()` creates an `EventRecorder` internally (line 224 of `src/engine/kernel.py`) and
passes `obs_mode` to determine enablement.

**Creation path 2 — global singleton:**
`get_or_start_global_worker(queue)` in `src/observability/queue.py` (line 165) guards the global
`_global_queue` with a `threading.Lock`. Tests that use this path are clean — the fixture in
`tests/unit/test_queue_worker_singleton.py` resets `_global_worker` properly.

**Thread attributes:**
- `daemon=True` — set at `src/observability/queue.py:112`
- Thread name: `"observability-drain-worker"` — used by `count_drain_workers()` in `tests/tools/memory_probe.py:38`
- `_run()` loop: `while self.running: ... time.sleep(self.interval_sec)` (lines 124-146, default 10ms interval)
- `stop()` method exists: sets `self.running = False` and calls `self._thread.join(timeout=1.0)` (lines 118-122)
- `EventRecorder.shutdown()` calls `self._worker.stop()` then does a synchronous queue drain and file close (lines 299-320)
- `Kernel.shutdown()` calls `self._event_recorder.shutdown()` transitively (line 857)

---

## Root Cause

**daemon=True does NOT prevent accumulation within a pytest session.**

daemon threads are reaped only when the main Python process exits. pytest runs all tests in
a single process. Each leaked worker thread keeps spinning at `queue.py:142` (`time.sleep`)
until the process dies. Across hundreds of tests this causes thread count to grow until Linux
hits its per-process thread ceiling (~32768), triggering `SIGABRT` (exit code 134).

**Two specific culprits identified — neither calls `kernel.shutdown()`:**

### Culprit 1: `tests/unit/kernel/test_replay_contract.py` — `test_replay_is_non_authoritative()`

```
Line 39: kernel = Kernel(profile=profile, state=state, rng=MagicMock(), replay=replay)
Lines 43-44: for i in range(5): kernel.tick_once()
Lines 46-48: assert statements — then test ends, NO kernel.shutdown()
```

One `EventRecorder` worker thread leaked per test run. This test runs once per session.

### Culprit 2: `tests/perf/test_concurrency_parity.py` — `run_parity_check()` helper

```
Line 22: kernel_loc = Kernel(...)
Line 37: kernel_con = Kernel(...)
Line 48: worker_manager.shutdown()  ← stops WorkerManager only, NOT the Kernel EventRecorders
# kernel_loc.shutdown() never called
# kernel_con.shutdown() never called
```

Every call to `run_parity_check()` leaks **2 threads**. The file has:
- 5 `@pytest.mark.perf` scenario tests — each calls `run_parity_check()` once → 10 threads
- 6 parametrized boundary tests (`test_worker_chunk_boundary_determinism`, 6 param values) — each calls `run_parity_check()` once → 12 threads
- **Total: 22 threads leaked from this file alone per full suite run**

Combined with other tests that instantiate `Kernel` or `EventRecorder` across a 500+ test session,
accumulation reaches the OS limit at approximately 68% through the suite.

---

## Why All Other Tests Are Clean

- `test_event_recorder.py`: calls `recorder.shutdown()` at line 89
- `test_obs_backpressure.py`: calls `rec._worker.stop()` immediately after construction (line 32)
- `test_cognition_diff_events.py`: calls `event_recorder.shutdown()` at line 140
- `test_phase21_worker_failure_isolation.py`: calls `recorder.shutdown()` at line 39
- `test_phase21_non_blocking_event_emission.py`: calls `recorder.shutdown()` at line 37
- `test_event_recorder_live_publish.py`: calls `recorder.shutdown()` at lines 66 and 96
- `test_memory_probe.py`: calls `recorder.shutdown()` at line 31
- `test_worldbuilding_strategy.py`: calls `recorder.shutdown()` at line 304
- `test_queue_worker_singleton.py`: uses autouse fixture that calls `w.stop()` in teardown

The `conftest.py` sentinel (`_observability_worker_thread_sentinel`) at line 110 correctly detects
the leak pattern — but it fires after the session ends, after the SIGABRT has already occurred.

---

## Fix

**Contract reference:** `docs/architecture/observability_hot_path_safety_contract.md §6` states:
> "Any test that constructs a Kernel or EventRecorder must call .shutdown() in teardown —
> either in a try/finally block or in a yield-fixture cleanup block."

The fix is surgical — add `kernel.shutdown()` in `try/finally` teardown for both culprits.
No changes to `queue.py`, `event_recorder.py`, or `conftest.py` are needed.

### Fix 1: `tests/unit/kernel/test_replay_contract.py`

Wrap the `Kernel` lifecycle in a `try/finally`:

```python
def test_replay_is_non_authoritative(tmp_path):
    ...
    kernel = Kernel(profile=profile, state=state, rng=MagicMock(), replay=replay)
    try:
        for i in range(5):
            kernel.tick_once()
        assert kernel.state.tick == 5
        assert replay._sink.persist_chunk.called
    finally:
        kernel.shutdown()
```

### Fix 2: `tests/perf/test_concurrency_parity.py`

Shutdown both kernel instances in `run_parity_check()`:

```python
def run_parity_check(initial_state, seed=42, ticks=100, workers=4):
    local_executor = LocalSequentialExecutor()
    kernel_loc = Kernel(...)
    try:
        for _ in range(ticks):
            kernel_loc.tick_once()
        hash_loc = StateFingerprinter.get_fingerprint(kernel_loc._state)['state_hash']
    finally:
        kernel_loc.shutdown()

    worker_manager = WorkerManager(max_workers=workers)
    concurrent_executor = ConcurrentExecutionAdapter(worker_manager)
    kernel_con = Kernel(...)
    try:
        for _ in range(ticks):
            kernel_con.tick_once()
        hash_con = StateFingerprinter.get_fingerprint(kernel_con._state)['state_hash']
    finally:
        kernel_con.shutdown()
        worker_manager.shutdown()

    return hash_loc, hash_con
```

---

## Why daemon=True Alone is Insufficient

`daemon=True` prevents interpreter shutdown from hanging on these threads, but within
a running pytest process the threads accumulate indefinitely. The contract in §6 requires
explicit `.shutdown()` — daemon mode is defense-in-depth for clean process exit, not a
substitute for proper teardown in tests.

The `stop()` / `shutdown()` path is preferable to relying on daemon=True because:
1. It flushes remaining queue events to disk before closing (§6 per-instance queue rule)
2. It closes the file handle cleanly (no partial JSONL writes)
3. It satisfies the conftest sentinel without relying on process exit
4. It is already the established contract pattern for all other test files

---

## Files Involved

| File | Role | Action Needed |
|------|------|---------------|
| `src/observability/queue.py` | Worker definition + global singleton | No change — daemon=True already set, stop() exists |
| `src/observability/event_recorder.py` | Per-instance worker owner, shutdown() exists | No change |
| `src/engine/kernel.py` | Creates EventRecorder, shutdown() delegates | No change |
| `tests/unit/kernel/test_replay_contract.py:39` | Creates Kernel, no shutdown | Add try/finally + kernel.shutdown() |
| `tests/perf/test_concurrency_parity.py:22,37` | Creates 2 Kernels, stops WorkerManager only | Add try/finally + kernel.shutdown() for both |
| `tests/conftest.py:110` | Session sentinel — already correct | No change |
| `tests/tools/memory_probe.py` | count_drain_workers() — already correct | No change |
