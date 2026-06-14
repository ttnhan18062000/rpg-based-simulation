---
ticket_id: TCK-20260614-REPLAY-BACKPRESSURE
date: 2026-06-14
---

# Plan: TCK-20260614-REPLAY-BACKPRESSURE

## Step 1 — Add fields to ReplayManager.__init__()
- `max_pending_flushes: int = 2` parameter
- `_max_pending_flushes`, `_inflight_count`, `_inflight_lock`, `_threshold_warning_logged`,
  `_avg_chunk_size_bytes` instance fields

## Step 2 — Update _rotate_chunk() async path
- Before `executor.submit()`: acquire `_inflight_lock`, check threshold, log once-per-crossing
  warning, increment `_inflight_count`
- Wire `future.add_done_callback(lambda _f: self._on_persist_done())`

## Step 3 — Add _on_persist_done()
- Acquires `_inflight_lock`, decrements `_inflight_count`, clamps to 0

## Step 4 — Update _execute_persistence()
- Compute `chunk_bytes` after serialisation
- Update `_avg_chunk_size_bytes` (exponential MA, alpha=0.1)

## Step 5 — Add replay_metrics()
- Lock-protected read of `_inflight_count`
- Returns `pending_flushes`, `chunks_persisted`, `bytes_pending_estimate`

## Step 6 — Replace pressure_report()
- Use `_inflight_count` (lock-protected) instead of `_current_chunk_id - _chunks_persisted`
- Thresholds: OK ≤ 80%, WARN 80-100%, DEGRADED ≥ 100%

## Step 7 — Tests (13 tests in test_replay_backpressure.py)
- Inflight count tracking (5 tests)
- Pressure report thresholds (5 tests)
- replay_metrics() accuracy (2 tests)
- No-chunk-drop invariant (1 test)

## Files Changed
- `src/engine/replay_manager.py`
- `tests/unit/engine/test_replay_backpressure.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-198 added)
