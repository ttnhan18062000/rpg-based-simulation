---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE
phase: open
date: 2026-09-15
tags: [observability, testing, data-quality]
---

# Investigation — TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE

## Root cause, found by reading `src/observability/stream/adapters.py::RedisStreamAdapter` directly

`_publish_worker()` (lines 155-167) and `flush()` (lines 261-267), as they exist before this
ticket's fix:

```python
def _publish_worker(self) -> None:
    while self._running:
        event = None
        with self._queue_lock:
            while len(self._queue) == 0 and self._running:
                self._queue_cond.wait(timeout=0.1)
            if not self._running:
                break
            if len(self._queue) > 0:
                event = self._queue.popleft()      # <-- queue becomes empty HERE, lock still held
        # lock released
        if event:
            self._send_to_redis(event)             # <-- xadd() + published_count/dropped_count
                                                     #     updates happen HERE, outside the lock

def flush(self) -> None:
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < 5.0:
        with self._queue_lock:
            if len(self._queue) == 0:               # <-- only checks queue emptiness
                break
        time.sleep(0.01)
```

**`flush()`'s actual, current contract is "the queue is empty," not "every dequeued event has
finished processing."** The worker pops an event (making `len(self._queue) == 0` true) and then
releases the lock *before* calling `_send_to_redis()`, which is where `client.xadd()` runs and
`self.published_count`/`self.dropped_count` are updated. Nothing prevents `flush()` from acquiring
the lock and seeing an empty queue in the window between the pop and the completion of
`_send_to_redis()` — that window is normally sub-millisecond (a mocked `xadd()` call has no real
I/O latency), which is exactly why this reproduces so rarely locally: `flush()`'s own poll
granularity (10ms) is usually coarser than the race window, so in practice the worker almost always
finishes before `flush()`'s next check. Under CI's likely more contended scheduler (shared runner,
other processes competing for the GIL/CPU), that window can widen enough for `flush()` to win the
race and return before `_send_to_redis()` has run.

This exactly matches the observed CI symptom: `mock_client.xadd.call_count == 1` passed (by the
time that assertion line actually executed, real wall-clock had passed and the worker had likely
caught up and finished the call) while `health()["published_events"] == 1` failed as `0` on a
*prior* read closer to `flush()`'s return — consistent with `flush()` racing ahead of
`_send_to_redis()`'s two side effects (`xadd()` then `published_count += 1`), which execute
sequentially in the worker thread with no lock or yield point between them once started.

## Answering the ticket's own Scope question: which side is wrong?

**The adapter is at fault; `flush()`'s completeness contract is too narrow for what a caller
reasonably expects from a function named `flush()` on an event-publishing adapter**, and for what
the existing test (unmodified by this ticket) already asserts immediately after calling it. This is
the same "the mechanism measures a proxy for the property it actually cares about, not the property
itself" shape recorded across `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` — "queue empty" is
a proxy for "processed," and the two diverge under exactly the wrong page (a race, but a load-bearing
one). Fixing the adapter (make the counter update happen-before `flush()` can return) is the chosen
path, per Scope's own framing of the choice.

## Why "dropped_count" has the identical exposure, found while reading the surrounding code

`test_redis_adapter_async_non_blocking`'s sibling test at line ~166-168
(`adapter.publish(...)`, `adapter.flush()`, `assert adapter.dropped_count == 1`) exercises the
disconnected-client path — `_send_to_redis()` increments `self.dropped_count` (not
`published_count`) in that branch, at the identical point in the same function, outside the same
lock. It is exposed to the same race, just never observed failing (the disconnected path returns
faster, since there's no `xadd()` call to make, so the window is even narrower — but it is not
structurally safe, only less likely to lose the race). The fix below closes this for both counters,
not just `published_count`, since both live in the same `_send_to_redis()` call.

## `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` cross-check

Read the epic's own `Related Code Areas` (`RedisStreamAdapter._send_to_redis`'s retention pattern —
the try/except around `client.xadd()`, never raising to the caller). Confirmed no prior work
touched `flush()`'s own polling loop or introduced any in-flight tracking; the epic's scope was
resilience against Redis being unreachable, not the queue-drain/processing-completion ordering this
ticket addresses. No conflict with the planned fix.

## Fix design

Track an in-flight counter alongside the queue, incremented when the worker pops an item (still
under `_queue_lock`) and decremented only after `_send_to_redis()` returns (also under the lock).
`flush()` waits for both `len(self._queue) == 0` **and** `self._in_flight == 0` before returning —
closing the exact window identified above, since the worker cannot decrement `_in_flight` until
`_send_to_redis()` (and therefore the counter updates) has actually completed.

No other call site depends on `flush()`'s current (narrower, buggy) timing —
`grep -rn "\.flush()"` under `src/`/`tests/` for this adapter returns only the two test call sites
in `tests/unit/observability/test_redis_stream_adapter.py`. The fix is safe to land without a
compatibility shim.

## Regression test design — must fail against the CURRENT code, not just pass after the fix

A test relying on real threading timing to reproduce the race would itself be flaky — exactly the
kind of test this ticket's AC forbids relying on ("not merely one that passes after a fix" implies
a *deterministic* proof, not a hope of catching the same rare window twice). Instead: inject a real,
controlled delay into the mocked `client.xadd()` (e.g. `time.sleep(0.05)` inside a `side_effect`)
so `_send_to_redis()` is guaranteed to still be running well past the moment the OLD `flush()`
implementation would have already returned (which happens as soon as the queue empties, i.e.
almost immediately after `popleft()`, long before a 50ms sleep completes). This makes the test
deterministically fail against the unfixed code (verified directly, see Test Summary) and
deterministically pass against the fixed code, with no dependency on real scheduler timing luck.
