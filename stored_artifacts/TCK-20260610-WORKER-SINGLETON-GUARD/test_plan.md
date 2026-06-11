---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-WORKER-SINGLETON-GUARD
artifact_type: test_plan
tags: [worker, singleton, guard]
---

# Test Plan — TCK-20260610-WORKER-SINGLETON-GUARD

## Scoped Test Command

```bash
pytest tests/unit/observability/stream/test_phase21_bounded_observability_queue.py \
       tests/unit/test_queue_worker_singleton.py \
       tests/unit/test_memory_probe.py \
       -v
```

Also run:
```bash
pytest tests/unit/test_memory_probe.py -v
```

---

## New Test File

`tests/unit/test_queue_worker_singleton.py`

---

## Test Cases

### test_global_worker_singleton
- Setup: reset module-level `_global_worker` to None (via module reload or direct assignment with `importlib`).
- Action: call `get_or_start_global_worker(queue)` twice with the same queue.
- Assert: the same `QueueDrainWorker` object is returned both times, and `get_active_global_worker_count() == 1`.
- Teardown: stop the worker.

### test_global_worker_reused_on_second_start
- Setup: fresh queue.
- Action: call `get_or_start_global_worker(queue)` once, capture returned worker; call again.
- Assert: both calls return the same object (`is` identity check).
- Teardown: stop the worker.

### test_global_worker_restarted_when_dead
- Setup: call `get_or_start_global_worker(queue)`, stop the returned worker so it is dead.
- Action: call `get_or_start_global_worker(queue)` again.
- Assert: a new worker is returned (not the dead one), and `get_active_global_worker_count() == 1`.
- Teardown: stop the new worker.

### test_get_active_global_worker_count_zero_when_none
- Setup: ensure `_global_worker` is None (via module-level reset in fixture).
- Assert: `get_active_global_worker_count() == 0`.

### test_get_active_global_worker_count_one_when_alive
- Setup: start a worker via `get_or_start_global_worker(queue)`.
- Assert: `get_active_global_worker_count() == 1`.
- Teardown: stop the worker.

---

## Regression Tests

- `tests/unit/observability/stream/test_phase21_bounded_observability_queue.py` — existing queue push/drop/drain tests must remain green.
- `tests/unit/test_memory_probe.py` — existing memory probe lifecycle test (`test_clean_recorder_no_worker_leak`) must remain green (EventRecorder per-instance path unchanged).

---

## Coverage Requirements

| Path | Coverage |
|---|---|
| `get_or_start_global_worker()` — first call creates worker | test_global_worker_singleton |
| `get_or_start_global_worker()` — second call reuses alive worker | test_global_worker_reused_on_second_start |
| `get_or_start_global_worker()` — dead worker replaced | test_global_worker_restarted_when_dead |
| `get_active_global_worker_count()` — 0 when None | test_get_active_global_worker_count_zero_when_none |
| `get_active_global_worker_count()` — 1 when alive | test_get_active_global_worker_count_one_when_alive |
| Thread safety (Lock) | covered implicitly by reuse tests; explicit concurrent test is optional (no race condition if lock is correct) |
