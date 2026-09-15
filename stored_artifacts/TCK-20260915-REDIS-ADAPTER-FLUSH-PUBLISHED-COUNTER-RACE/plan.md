---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE
phase: open
date: 2026-09-15
tags: [observability, testing, data-quality]
---

# Plan — TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE

## `src/observability/stream/adapters.py` — `RedisStreamAdapter`

1. Add `self._in_flight = 0` to `__init__`, alongside the other queue-state fields.
2. In `_publish_worker()`: increment `_in_flight` (under `_queue_lock`) at the same point the item
   is popped; after `_send_to_redis(event)` returns (success or exception), decrement `_in_flight`
   under the lock in a `finally` block, so a raised exception inside `_send_to_redis()` can never
   leave `_in_flight` stuck non-zero and hang `flush()` forever. (`_send_to_redis()` already
   catches its own exceptions internally — confirmed by reading it — but the `finally` is a second,
   independent safety net, not a reliance on that.)
3. Update `flush()`'s condition to `len(self._queue) == 0 and self._in_flight == 0`.
4. Add a real docstring to `flush()` stating the guarantee explicitly: blocks until every event
   queued before this call has been fully processed (sent to Redis or dropped, whichever applies,
   *and* its bookkeeping/counters updated) — not merely dequeued. Cites this ticket for why the
   distinction matters.

## `tests/unit/observability/test_redis_stream_adapter.py`

- Do not modify the existing `published_events == 1` assertion (AC requirement) or the sibling
  `dropped_count == 1` assertion at line ~168 — both stay as-is; the fix makes them reliably true
  rather than racy.
- New test: `test_flush_waits_for_send_to_redis_to_complete_not_just_queue_drain` — injects a
  `time.sleep(0.05)` into the mocked `client.xadd` via `side_effect`, publishes one event, calls
  `flush()`, and immediately asserts `health()["published_events"] == 1`. Verify this test fails
  against the pre-fix code (confirmed directly, see Test Summary) and passes against the fixed
  code.
- New test: `test_flush_also_waits_for_dropped_count_bookkeeping` — same shape, disconnected-client
  path (mirrors the existing degraded-mode test), confirming the fix also closes the identical
  window for `dropped_count`.

## No other call sites affected

`grep -rn "\.flush()" src/ tests/` (already run in investigation.md) shows only the two existing
test call sites use `RedisStreamAdapter.flush()` — no production code path depends on its current
(narrower) timing, so the fix has no other blast radius to consider.

## Disposition (AC requirement: record even if the conclusion differs)

Concluded the adapter is at fault (ordering bug), not the test over-asserting. Recorded in
investigation.md's "Answering the ticket's own Scope question" section and restated in this
ticket's own Completion Summary once implemented.
