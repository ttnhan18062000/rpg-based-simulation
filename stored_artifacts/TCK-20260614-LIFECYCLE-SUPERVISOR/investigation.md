---
ticket_id: TCK-20260614-LIFECYCLE-SUPERVISOR
date: 2026-06-14
---

# Investigation: TCK-20260614-LIFECYCLE-SUPERVISOR

## Existing Kernel.shutdown() State

`Kernel.shutdown()` returns `ShutdownResult` (final_tick, final_hash, replay_outcome,
overall_outcome). Multiple callers consume this return value: `long_run_harness.py`,
`cli/entry.py`, `certification/harness.py`, integration tests. Return type MUST remain
`ShutdownResult` — `ShutdownReport` is an addendum accessible via `shutdown_report()`.

Workers stopped in existing shutdown:
1. `_worker_manager.shutdown()` — ComputeWorkerManager (ThreadPoolExecutor/ProcessPoolExecutor)
2. `_event_recorder.shutdown()` — stops QueueDrainWorker, drains queue, closes file handle
3. `_metric_recorder.shutdown()` — if present

## BehaviorWorker

`BehaviorWorker` (src/observability/behavior/worker.py) is not instantiated in Kernel at all.
It runs as a `daemon=True` thread named `"behavior-normalization-worker"` when in queue-drain mode.
Since there's no kernel reference, the only safe way to wire it in is by thread name lookup in
`threading.enumerate()` at shutdown time. `stop_queue_worker()` sets `_running=False` and
`join(timeout=2.0)`, but we don't have the instance. Direct `join()` on the thread is equivalent.

## Worker Count Tracking

Only the `EventRecorder._worker` (QueueDrainWorker) is a registered, predictable worker started
deterministically by the kernel. `_workers_started = 1` when obs is enabled, else 0.
`WorkerManager` workers are compute-on-demand — not lifecycle workers in the supervisor sense.
`get_active_global_worker_count()` tracks a separate global QueueDrainWorker instance, not the
EventRecorder's worker.

## psutil

`psutil.Process().open_files()` is available in the environment. Returns a list of open file
handles for the current process. Advisory only — wrapped in try/except; `open_file_handles=-1`
on failure.

## __slots__ Extension

Added `_workers_started` and `_last_shutdown_report` to `Kernel.__slots__` to avoid
AttributeError on slot-strict instances.
