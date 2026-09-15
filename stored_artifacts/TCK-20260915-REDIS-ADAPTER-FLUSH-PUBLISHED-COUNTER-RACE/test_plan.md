---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE
phase: open
date: 2026-09-15
tags: [observability, testing, data-quality]
---

# Test Plan — TCK-20260915-REDIS-ADAPTER-FLUSH-PUBLISHED-COUNTER-RACE

## New tests (deterministic, not timing-luck-dependent)

1. `test_flush_waits_for_send_to_redis_to_complete_not_just_queue_drain` — injects a controlled
   delay into the mocked `client.xadd`, so `_send_to_redis()` is guaranteed still running when the
   OLD `flush()` would already have returned. Must be run once against the pre-fix code to confirm
   it fails (proving it's a real regression guard, not a test that only ever passes), then again
   against the fixed code to confirm it passes.
2. `test_flush_also_waits_for_dropped_count_bookkeeping` — same shape, disconnected-client/dropped
   path.

## Regression coverage

- `tests/unit/observability/test_redis_stream_adapter.py` — full file, both pre-existing tests
  unmodified (`test_redis_adapter_async_non_blocking`, the disconnected-client test) plus the 2 new
  ones, run under both `.venv313/bin/python3` (CI-matching, 3.13.14) and `.venv/bin/python3` (3.12.3,
  per this ticket's own hard-won lesson about interpreter parity — verify on both, don't assume one
  implies the other).
- Broader `tests/unit/observability/` directory, to confirm no other test depends on the adapter's
  old (buggy) `flush()` timing.
- Full `Unit · infra / observability` lane's own command (17 paths, CI's markers) under
  `.venv313/bin/python3`, matching how CI actually runs this.

## Verification that the new test is a real regression guard, not vacuous

Before applying the fix, run the new test against the current (pre-fix) `adapters.py` and confirm
it fails with the same shape of assertion error the CI logs showed
(`published_events`/`dropped_count` reading 0 immediately after `flush()`). Record the exact
failure text in Implementation Notes as proof, per this ticket's own AC ("a test exists that fails
against the current implementation if the ordering gap is real, not merely one that passes after a
fix").
