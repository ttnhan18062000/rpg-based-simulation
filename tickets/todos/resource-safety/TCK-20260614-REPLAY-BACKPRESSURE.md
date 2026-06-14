---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-REPLAY-BACKPRESSURE
phase: open
date: 2026-06-14
tags: [resource-safety, replay, backpressure, memory, performance]
---

# TCK-20260614-REPLAY-BACKPRESSURE

## Title
Add Replay Backpressure Manager — bound pending flush count and expose replay metrics

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ReplayManager` uses a single-worker `ThreadPoolExecutor` (`src/engine/replay_manager.py:62`) and submits async persistence tasks via `_executor.submit()` in `_rotate_chunk()` (line 165). If disk is slow, pending futures accumulate outside the replay buffer's own bound. There is no cap on inflight chunks and no pressure metric exposed. Add a `max_pending_flushes` limit: when exceeded, switch to sync write (FORENSIC mode) or drop non-authoritative chunks (other modes). Expose `replay.pending_flushes`, `replay.oldest_pending_age_ms`, and `replay.bytes_pending` metrics.

## Scope
- Add `_inflight_count: int = 0` to `ReplayManager` — incremented on `executor.submit()`, decremented in the future's completion callback
- Add `max_pending_flushes: int = 2` parameter to `ReplayManager.__init__()` (sourced from `SubsystemBudget.max_pending_flushes` if set)
- In `_rotate_chunk()`: before submitting async task, check `_inflight_count >= max_pending_flushes`:
  - Log a warning (once per threshold crossing, not every chunk) with current inflight count and budget
  - Continue the submit anyway — do NOT autonomously drop or fall back to sync; pressure reporting is the only action here
- Add `replay_metrics() -> dict` method: `{"pending_flushes": int, "chunks_persisted": int, "bytes_pending_estimate": int}`
- `bytes_pending_estimate`: approximate as `pending_flushes * avg_chunk_size_bytes` (track rolling average of chunk sizes)
- Expose `pressure_report() -> SubsystemPressureReport`: `WARN` when `_inflight_count > max_pending_flushes * 0.8`, `DEGRADED` at or above `max_pending_flushes`
- Wire `replay_metrics()` and `pressure_report()` into the dashboard (feeds TCK-20260614-RESOURCE-DASHBOARD); the Governor reads pressure_report() and issues degradation commands — ReplayManager does not decide its own degradation action

## Out of Scope
- Changing the replay buffer bounded eviction (already bounded — not the issue)
- Changing replay chunk format or content
- Cross-run replay orchestration

## Acceptance Criteria
- `ReplayManager` has `_inflight_count` tracking incremented/decremented correctly across thread boundaries
- When `_inflight_count >= max_pending_flushes`: a warning is logged (once per crossing, not per chunk); chunk submit continues unchanged
- `ReplayManager` does NOT autonomously drop chunks or switch to sync write — all degradation decisions are the Governor's
- `replay_metrics()` returns correct counts for `pending_flushes`, `chunks_persisted`, `bytes_pending_estimate`
- `pressure_report()` returns `WARN` when `_inflight_count > max_pending_flushes * 0.8`, `DEGRADED` at or above `max_pending_flushes`
- Tests: inflight count tracks correctly; pressure_report transitions at correct thresholds; no chunk is dropped by ReplayManager itself

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-RESOURCE-BUDGET-GATE (provides SubsystemBudget.max_pending_flushes definition)
- TCK-20260614-RESOURCE-DASHBOARD (reads replay_metrics() / pressure_report())
- TCK-20260420-REPLAY-RACE (DONE — thread safety in ReplayManager already addressed; verify which locks were added before adding a new Lock for _inflight_count to avoid re-entering the same lock)

## Related Docs
- `docs/engine/contracts/replay_contract.md` — CRITICAL: "Under pressure, the Governor will downgrade replay richness" — the degradation decision belongs to the Governor, not to ReplayManager directly; this ticket's drop/sync-fallback logic must be framed as ReplayManager reporting pressure and the Governor deciding action, not autonomous degradation
- `docs/engine/kernel.md`
- `docs/parity_ledger/infrastructure.yaml`
- `memory_features.md` (Feature 6)

## Related Code Areas
- `src/engine/replay_manager.py:20` — `ReplayManager` class
- `src/engine/replay_manager.py:62` — `ThreadPoolExecutor(max_workers=1)`
- `src/engine/replay_manager.py:156` — `_rotate_chunk(async_write=True)`
- `src/engine/replay_manager.py:165` — `self._executor.submit(...)`
- `src/engine/replay_manager.py:113` — `self._executor.shutdown(wait=True)`
- `src/engine/replay_buffer.py:35` — `extract_chunk()` — chunk assembly point

## Assumptions / Open Questions
- Replay mode (FORENSIC vs. standard) — where is the current mode stored on `ReplayManager`? Check `__init__` parameters and `_buffer`/`_sink` config.
- Future completion callback: use `future.add_done_callback(lambda f: self._inflight_count -= 1)` — ensure thread safety with a threading.Lock or atomic integer
- `avg_chunk_size_bytes`: initialize to 0, update as `(prev_avg * 0.9) + (chunk_bytes * 0.1)` rolling average

## Implementation Notes
- The decrement in the done callback runs in the executor thread — use `threading.Lock` to protect `_inflight_count`
- Do NOT use `len(executor._work_queue)` — private API, brittle

## Test Summary
- `tests/unit/engine/test_replay_backpressure.py` (new):
  - `test_inflight_count_increments_on_submit`
  - `test_inflight_count_decrements_on_completion`
  - `test_pressure_report_ok_below_threshold`
  - `test_pressure_report_warn_at_80pct`
  - `test_pressure_report_degraded_at_limit`
  - `test_no_chunk_dropped_by_replay_manager` — assert chunks are always submitted regardless of inflight count
  - `test_replay_metrics_accuracy`
- Run: `pytest tests/unit/engine/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
