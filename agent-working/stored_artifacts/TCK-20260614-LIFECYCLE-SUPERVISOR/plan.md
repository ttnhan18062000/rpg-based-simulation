---
ticket_id: TCK-20260614-LIFECYCLE-SUPERVISOR
date: 2026-06-14
---

# Plan: TCK-20260614-LIFECYCLE-SUPERVISOR

## Step 1 — Add ShutdownReport to src/core/lifecycle.py
- `@dataclass ShutdownReport` with all 7 fields
- Import `field` from dataclasses for default_factory

## Step 2 — Extend Kernel.__slots__
- Add `"_workers_started"` and `"_last_shutdown_report"`

## Step 3 — Add _workers_started tracking in __init__()
- `_workers_started = 1` when obs enabled, else 0
- `_last_shutdown_report = None`

## Step 4 — Update Kernel.shutdown()
- Build `ShutdownReport` before any shutdown work
- Wire BehaviorWorker thread join (by thread name)
- Increment `workers_stopped` when event_recorder is stopped
- Collect `pending_replay_flushes` from `replay_metrics()`
- Collect `survival_event_counts` from `_event_recorder._survival_event_counts`
- Collect `open_file_handles` from psutil (fallback -1)
- Set outcome PARTIAL when workers_stopped < workers_started
- Set outcome FAILED when replay_outcome is FAILED
- Cache as `_last_shutdown_report`
- Return `ShutdownResult` unchanged (backward-compatible)

## Step 5 — Add Kernel.shutdown_report()
- Returns `_last_shutdown_report` (None before shutdown)

## Step 6 — Tests (14 tests in test_lifecycle_supervisor.py)
- ShutdownReport shape (3), clean shutdown (7), pending flushes (2),
  BehaviorWorker thread join (1), survival counts (1)

## Files Changed
- `src/core/lifecycle.py` — ShutdownReport dataclass
- `src/engine/kernel.py` — __slots__, _workers_started, shutdown(), shutdown_report()
- `tests/unit/engine/test_lifecycle_supervisor.py` (new)
- `docs/parity_ledger/infrastructure.yaml` — INFRA-200 added
