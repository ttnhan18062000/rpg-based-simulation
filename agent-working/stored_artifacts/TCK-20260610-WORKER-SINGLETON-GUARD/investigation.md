---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260610-WORKER-SINGLETON-GUARD
artifact_type: investigation
tags: [worker, singleton, guard]
---

# Investigation — TCK-20260610-WORKER-SINGLETON-GUARD

## File: src/observability/queue.py

### Does `get_observability_queue()` currently prevent multiple workers?
No. `get_observability_queue()` is a pure singleton for the *queue object* only. It uses a module-level `_global_queue` and a `_queue_lock`, but there is no corresponding `_global_worker`. Nothing in this function tracks or guards against multiple `QueueDrainWorker` instances being attached to the same queue.

### Is there a module-level `_global_worker`?
No. Only `_global_queue` and `_queue_lock` exist at module level. There is no worker registry at all.

### Thread name set on QueueDrainWorker
`name="observability-drain-worker"` (line 112 in queue.py). This is the name that `tests/tools/memory_probe.py::count_drain_workers()` filters on.

---

## File: src/observability/event_recorder.py

### Does EventRecorder use the global queue?
No. `EventRecorder.__init__` creates its own **per-instance** `BoundedObservabilityQueue` (line 42):
```python
self.queue = BoundedObservabilityQueue(max_size=self.max_events)
```
It does not call `get_observability_queue()` at all.

### Does EventRecorder create its own per-instance worker?
Yes. It creates a `QueueDrainWorker` backed by its own per-instance queue (lines 43–49):
```python
self._worker = QueueDrainWorker(
    queue=self.queue,
    file_write_fn=...,
    stream_publish_fn=...
)
if self.enabled:
    self._worker.start()
```

### Guard location implication
Because `EventRecorder` uses per-instance queues (not the global queue), the multiple-worker-per-global-queue problem cannot currently be triggered via `EventRecorder` alone. However, the module-level `get_observability_queue()` is the public API for the global singleton, and any code that calls it and also creates a `QueueDrainWorker` on it directly would produce the leak.

The correct guard location is therefore in `src/observability/queue.py` at the module level: add `_global_worker` and `get_or_start_global_worker()` alongside the existing `_global_queue` / `_queue_lock` pattern.

The EventRecorder per-instance path is out of scope (it uses its own queue, not the global one).

---

## Summary of Findings

| Question | Answer |
|---|---|
| Does `get_observability_queue()` guard workers? | No — queue singleton only, no worker tracking |
| Does `EventRecorder.__init__` use the global queue? | No — per-instance `BoundedObservabilityQueue` |
| Module-level `_global_worker` exists? | No — must be added |
| Thread name on `QueueDrainWorker` | `"observability-drain-worker"` |
| Cleanest guard location | `src/observability/queue.py` module level — `get_or_start_global_worker()` |
