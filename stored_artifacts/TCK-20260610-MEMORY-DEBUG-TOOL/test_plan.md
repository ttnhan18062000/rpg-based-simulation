PHASE_TS: 2026-06-10T17:20:30Z

# Test Plan: TCK-20260610-MEMORY-DEBUG-TOOL

## Regression Surface (existing tests that must still pass)
- `tests/unit/observability/test_event_recorder.py` — EventRecorder behavior unchanged
- `tests/unit/kernel/` — Kernel unchanged
- `pytest tests/unit/observability/test_event_recorder.py tests/unit/kernel/ -v`

## New Tests Required (per AC)

### tests/unit/test_memory_probe.py
1. `test_clean_recorder_no_worker_leak`
   - Create `EventRecorder(enabled=True)` (starts a QueueDrainWorker)
   - Call `shutdown()`
   - Assert `worker_count_delta == 0` using `snapshot_start` / `snapshot_end`
   - Covers AC: smoke test, worker count assertion

2. `test_assert_no_worker_leak_raises`
   - Call `assert_no_worker_leak(before=0, after=1)`
   - Assert `AssertionError` is raised
   - Assert "1" appears in the error message
   - Covers AC: clear error message on leak

3. Import smoke:
   - `from tests.tools.memory_probe import snapshot_start, snapshot_end, assert_no_worker_leak, count_drain_workers`
   - Must not raise ImportError
   - Covers AC: importable without memray

## Scoped Pytest Commands
```
pytest tests/unit/test_memory_probe.py -v
pytest tests/unit/observability/test_event_recorder.py -v
```

## Anti-Drift Test Guards
- `test_memory_probe.py` must NOT import memray (assert ImportError handling is lazy)
- `count_drain_workers()` must count by thread name `"observability-drain-worker"`, not isinstance
- If thread naming in QueueDrainWorker changes, this test will fail fast and surface the drift
