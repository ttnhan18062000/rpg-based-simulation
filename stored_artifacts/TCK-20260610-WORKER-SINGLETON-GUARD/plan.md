---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-WORKER-SINGLETON-GUARD
artifact_type: plan
tags: [worker, singleton, guard]
---

# Plan — TCK-20260610-WORKER-SINGLETON-GUARD

## Architecture Review Status: APPROVED

Thread-safety: Lock required and will be added. The global worker registry is observability infrastructure, not simulation state — acceptable per Architecture Rule. No raw domain model exposure. No durable simulation-state mutation.

---

## Investigation Summary

`EventRecorder` uses a **per-instance** `BoundedObservabilityQueue`, not the global one. The global queue (`_global_queue`) has no corresponding global worker tracking. The guard must be placed in `src/observability/queue.py` at the module level, alongside the existing `_global_queue` / `_queue_lock` pattern.

The `EventRecorder` per-instance path is unaffected.

---

## Changes

### 1. `src/observability/queue.py`

Add three module-level additions below the existing `_global_queue` / `_queue_lock` declarations:

```python
_global_worker: Optional[QueueDrainWorker] = None
_global_worker_lock = threading.Lock()
```

Add function `get_or_start_global_worker(queue: BoundedObservabilityQueue) -> QueueDrainWorker`:
- Acquire `_global_worker_lock`.
- If `_global_worker is None` or `not _global_worker.is_alive()`: create new `QueueDrainWorker(queue)`, call `.start()`, assign to `_global_worker`, return it.
- Else: return `_global_worker`.
- The check-and-start inside the lock prevents a second thread from slipping through between the None check and the assignment.

Add function `get_active_global_worker_count() -> int`:
- Returns `1` if `_global_worker is not None and _global_worker.is_alive()` else `0`.
- No lock needed (read-only introspection; worst case returns stale 0 during startup, which is fine for tests that synchronize explicitly).

### 2. `src/observability/event_recorder.py`

No changes. `EventRecorder` uses its own per-instance queue and worker. The guard in `queue.py` is for callers that consume the global queue directly.

### 3. New test file `tests/unit/test_queue_worker_singleton.py`

Five test cases (see test_plan.md). Uses a module-level fixture that resets `_global_worker` to `None` before each test to ensure isolation between tests.

---

## Non-Goals

- Do not remove or change the per-instance `QueueDrainWorker` in `EventRecorder`.
- Do not change queue capacity or drain interval.
- Do not add logging to the guard (observability infra should not log to itself on hot paths).
