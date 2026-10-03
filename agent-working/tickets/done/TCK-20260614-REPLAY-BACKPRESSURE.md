---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-REPLAY-BACKPRESSURE
phase: done
date: 2026-06-14
tags: [resource-safety, replay, backpressure, memory, performance]
---

# TCK-20260614-REPLAY-BACKPRESSURE

## Title
Add Replay Backpressure Manager — bound pending flush count and expose replay metrics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ReplayManager` uses a single-worker `ThreadPoolExecutor` and submits async persistence tasks
via `_executor.submit()` in `_rotate_chunk()`. If disk is slow, pending futures accumulate with
no cap. Add a `max_pending_flushes` limit with lock-protected tracking and expose replay metrics
for the Governor/dashboard. ReplayManager never autonomously drops — it signals pressure only.

## Scope
- `_inflight_count` tracking with `threading.Lock` (increment before submit, decrement in done callback)
- `max_pending_flushes: int = 2` parameter to `__init__()`
- Threshold warning logged once per crossing (not per chunk)
- `replay_metrics()` returning `pending_flushes`, `chunks_persisted`, `bytes_pending_estimate`
- `pressure_report()` using `_inflight_count` (OK ≤ 80%, WARN 80-100%, DEGRADED ≥ 100%)
- Rolling average `_avg_chunk_size_bytes` for bytes estimate (alpha=0.1 EMA)

## Out of Scope
- Changing replay buffer bounded eviction
- Changing replay chunk format or content
- Cross-run replay orchestration

## Acceptance Criteria
- [x] `_inflight_count` incremented before submit, decremented in callback, protected by Lock
- [x] Warning logged once per threshold crossing (not per chunk)
- [x] ReplayManager does NOT drop chunks or switch to sync write autonomously
- [x] `replay_metrics()` returns correct counts
- [x] `pressure_report()` transitions at correct thresholds
- [x] 13 tests pass

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (provides SubsystemBudget definition)
- TCK-20260614-RESOURCE-DASHBOARD (reads replay_metrics() / pressure_report())

## Related Docs
- `docs/engine/contracts/replay_contract.md` — Governor degradation model
- `docs/parity_ledger/infrastructure.yaml` — INFRA-198

## Related Stored Artifacts
- `stored_artifacts/TCK-20260614-REPLAY-BACKPRESSURE/`

## Related Code Areas
- `src/engine/replay_manager.py`
- `tests/unit/engine/test_replay_backpressure.py`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
- `_inflight_lock` is separate from `_manifest_lock` (added by TCK-20260420-REPLAY-RACE) — never held simultaneously
- `_avg_chunk_size_bytes` is written only in executor thread; lock-free read in `replay_metrics()` is acceptable for an estimate
- `_on_persist_done()` clamps to 0 to guard against any double-decrement edge cases

## Test Summary
13 tests in `tests/unit/engine/test_replay_backpressure.py`. All pass.
Regression: 0 new failures in `tests/unit/kernel/` replay suite.
Pre-existing ERROR: `test_shutdown_performs_rotation_on_ample_budget` thread-leak teardown (QueueDrainWorker) — not caused by this ticket.

## Files Changed
- `src/engine/replay_manager.py` — backpressure tracking, replay_metrics(), updated pressure_report()
- `tests/unit/engine/test_replay_backpressure.py` — new, 13 tests
- `docs/parity_ledger/infrastructure.yaml` — INFRA-197 (CanonicalHashScheduler) + INFRA-198 (ReplayManager backpressure)

## Completion Summary
ReplayManager now tracks inflight async persist tasks with a threading.Lock-protected counter.
Pressure is reported via pressure_report() for the Governor to act on. replay_metrics() exposes
pending_flushes, chunks_persisted, and bytes_pending_estimate. 13 tests verify all thresholds
and the no-drop invariant. INFRA-197 and INFRA-198 added to parity ledger.
