---
ticket_id: TCK-20260614-REPLAY-BACKPRESSURE
date: 2026-06-14
---

# Investigation: TCK-20260614-REPLAY-BACKPRESSURE

## Existing State

`ReplayManager.__init__()` creates a `ThreadPoolExecutor(max_workers=1)` and submits async
persistence tasks via `_executor.submit()` in `_rotate_chunk()`. There was no inflight cap
and no lock-protected counter — only the advisory `_chunks_persisted` plain int (incremented
on success inside the background thread).

`pressure_report()` existed but derived pressure from `_current_chunk_id - _chunks_persisted`
(a plain int subtraction with no lock). Racy under concurrent persist callbacks.

## Existing Locks

`TCK-20260420-REPLAY-RACE` (DONE) added `_manifest_lock` for manifest writes. No other locks
existed. Adding `_inflight_lock` for `_inflight_count` is safe — it is a separate concern and
the two locks are never held simultaneously.

## Thread-Safety Analysis

The done-callback from `future.add_done_callback()` runs in the executor thread. Decrement must
be lock-protected to prevent races with the main thread reading `_inflight_count` in
`pressure_report()`. Using `threading.Lock` (not `threading.RLock`) is sufficient since
`_on_persist_done()` never calls back into the lock from within.

## Rolling Average

`_avg_chunk_size_bytes` is computed inside `_execute_persistence()` (executor thread only),
so it does not need lock protection. It is read lock-free by `replay_metrics()`; a stale read
is acceptable for an estimate.

## Governor Model Compliance

`docs/engine/contracts/replay_contract.md` §4: "Under pressure, the Governor will downgrade
replay richness." ReplayManager must never autonomously drop chunks. The warning + pressure_report
pattern satisfies this: ReplayManager signals, Governor acts.
