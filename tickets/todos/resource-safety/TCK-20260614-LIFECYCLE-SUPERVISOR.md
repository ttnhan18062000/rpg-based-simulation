---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-LIFECYCLE-SUPERVISOR
phase: open
date: 2026-06-14
tags: [resource-safety, lifecycle, workers, shutdown, observability]
---

# TCK-20260614-LIFECYCLE-SUPERVISOR

## Title
Add Worker Lifecycle Supervisor — systematic shutdown reporting and orphan detection

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`Kernel.shutdown()` (line 792) already stops `_worker_manager`, `_event_recorder`, `_metric_recorder`, and `_replay`. But there is no consolidated report, no orphan worker detection, and no file handle accounting. Worker and file descriptor leaks are currently only caught in tests (if at all). Promote the existing shutdown path to a first-class lifecycle supervisor that produces a machine-readable `ShutdownReport` and warns on orphans.

## Scope
- Add `ShutdownReport` dataclass in `src/engine/kernel.py` (or `src/engine/lifecycle.py`):
  - `workers_started: int`
  - `workers_stopped: int`
  - `open_file_handles: int`
  - `pending_replay_flushes: int`
  - `survival_event_counts: dict`
  - `outcome: str` (`"SUCCESS"` / `"PARTIAL"` / `"FAILED"`)
  - `warnings: list[str]`
- Update `Kernel.shutdown()` to return `ShutdownReport` (currently returns `ShutdownResult` — reconcile or extend)
- Track worker lifecycle: add `_workers_started: int` counter incremented in `__init__` for each registered worker; decremented on confirmed stop in `shutdown()`
- Add `kernel.shutdown_report() -> ShutdownReport` method callable after `shutdown()` (returns cached last report)
- Detect and warn on: workers still alive after timeout, non-zero `pending_replay_flushes`, non-zero `open_file_handles` (use `psutil.open_files()` if available, else skip gracefully)
- Wire `BehaviorWorker` into shutdown: confirm `stop_queue_worker()` (`src/observability/behavior/worker.py:201`) is called in Kernel shutdown path; if missing, add it
- Add `outcome: "PARTIAL"` when any worker stop timed out; `"FAILED"` if shutdown raised

## Out of Scope
- Changing WorkerManager internals
- Process-wide file handle auditing beyond what `psutil` provides
- Automatic worker restart

## Acceptance Criteria
- `ShutdownReport` dataclass exists with all fields listed above
- `Kernel.shutdown()` returns a `ShutdownReport`
- `workers_started == workers_stopped` in all normal shutdown scenarios
- Non-zero `pending_replay_flushes` generates a warning in `ShutdownReport.warnings`
- `BehaviorWorker.stop_queue_worker()` is called during `Kernel.shutdown()`
- Test: simulate a worker that times out — `ShutdownReport.outcome == "PARTIAL"`, warning present
- Test: clean shutdown — `ShutdownReport.outcome == "SUCCESS"`, warnings empty

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-OBS-BACKPRESSURE (survival_event_counts sourced from EventRecorder)
- TCK-20260614-REPLAY-BACKPRESSURE (pending_replay_flushes sourced from ReplayManager.replay_metrics())
- TCK-20260610-WORKER-SINGLETON-GUARD (DONE — `get_or_start_global_worker()` and `get_active_global_worker_count()` already in `src/observability/queue.py`; use these for worker count tracking instead of reimplementing)
- TCK-20260610-KERNEL-TEST-TEARDOWN (DONE — shutdown calls already added to 11 test files, and `_observability_worker_thread_sentinel` fixture exists in conftest; do not duplicate teardown logic)

## Related Docs
- `docs/architecture/observability_hot_path_safety_contract.md` — section 2: what is allowed in hot path (counter increments OK); section 3: what is forbidden (deep copies, IO, locks); governs which ShutdownReport fields can be populated synchronously
- `docs/engine/kernel.md`
- `memory_features.md` (Feature 8)

## Related Code Areas
- `src/engine/kernel.py:792` — `shutdown()` method
- `src/engine/kernel.py:42` — `__slots__` listing `_worker_manager`, `_executor`
- `src/observability/behavior/worker.py:70` — `BehaviorWorker`, `stop_queue_worker()` at line 201
- `src/engine/replay_manager.py:110` — executor shutdown comment

## Assumptions / Open Questions
- `ShutdownResult` is likely the existing return type of `Kernel.shutdown()` — check if `ShutdownReport` should extend or replace it. If `ShutdownResult` is used by existing callers, add `shutdown_report()` as a separate accessor rather than changing the return type.
- `psutil` availability: wrap in `try/import psutil; open_handles = len(psutil.Process().open_files())` — if import fails, set `open_file_handles = -1` and add note in warnings

## Implementation Notes
- `_workers_started` should be set from `WorkerManager.get_stats()["active_workers"]` at init time or tracked separately — check what `get_stats()` returns at kernel init vs. mid-run
- The report is cached in `_last_shutdown_report` on the kernel instance for post-shutdown inspection

## Test Summary
- `tests/unit/engine/test_lifecycle_supervisor.py` (new):
  - `test_clean_shutdown_produces_success_report`
  - `test_workers_started_equals_stopped_on_clean_shutdown`
  - `test_timeout_worker_produces_partial_outcome`
  - `test_pending_replay_flushes_generates_warning`
  - `test_behavior_worker_stopped_during_shutdown`
- Run: `pytest tests/unit/engine/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
