---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
artifact_type: test_plan
tags: [observability]
---

# Test Plan — TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC

## Regression Surface

All of these exist today and exercise `consumer.py`/`adapters.py`/`factory.py` directly or through
a caller; confirmed present via file reads, not assumed.

**Unit (no live Redis required):**
- `tests/unit/observability/test_event_stream_adapters.py` — `test_null_adapter`,
  `test_in_process_adapter`, `test_redis_adapter_resilient_missing_library`,
  `test_redis_adapter_publish_resilience`, `test_factory_resolutions` — must keep passing
  unmodified; these assert the "Redis package/runtime absent → degraded, no crash" property that
  overlaps `INFRA-015/016/063/165`.
- `tests/unit/observability/test_redis_stream_adapter.py` —
  `test_redis_adapter_async_non_blocking`, `test_redis_adapter_backpressure_eviction_and_dropping`,
  `test_redis_adapter_degraded_fallback` — publish-side adapter behavior; must be unaffected since
  this ticket does not change `RedisStreamAdapter.publish()`/backpressure logic.

**Integration (skip-if-no-local-Redis, `redis_available` guard pattern):**
- `tests/integration/observability/test_stream_consumer_basic.py::test_live_stream_consumer_group_lifecycle`
  — **direct regression target.** Asserts: 3 published events all processed exactly once; a
  second read returns 0; a malformed (`invalid-json-payload-string`) injected event is ack'd and
  cleared (`processed_poison == 0`, no exception surfaces). This is the exact behavior AC #2
  ("malformed payload still results in ack+drop, unchanged") must not regress — this test's
  poison-pill assertion is the sharpest existing guard for that.
- `tests/integration/observability/test_stream_backpressure.py::test_live_backpressure_and_eviction_integration`
  — publish-side, unaffected by this ticket's scope but shares the same live-Redis fixture
  pattern; keep passing to confirm no import/collection-level breakage.
- `tests/integration/test_observatory_stream_outage.py` — `test_engine_continues_during_stream_outage`,
  `test_stream_outage_health_shows_degraded`, `test_stream_outage_no_crash` — asserts the *engine*
  (not the consumer) stays unaffected when the stream backend is unreachable; this exercises
  `RedisStreamAdapter` (publish side) via a deliberately-broken adapter, not `RedisStreamConsumer`
  directly, but is the closest existing "outage" integration coverage and must keep passing to
  confirm the engine-isolation guarantee is untouched by this ticket.

**Simulation-quality broker-mode integration (adjacent, shares `RedisStreamConsumer`
construction path via `BrokerQualityFeed`):**
- `tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable`
  (INFRA-239) — must keep passing; the new connect()-retry/backoff logic must still resolve to
  `health="unavailable"` and return cleanly rather than blocking `BrokerQualityFeed.start()`.
- `tests/simulation_quality/test_feed.py::test_broker_stream_name_defaults_to_observability_config`,
  `test_broker_url_defaults_to_observability_config` (INFRA-317) — config resolution, unaffected
  by this ticket but shares the same constructor call site.
- `tests/simulation_quality/test_broker_feed_integration.py` (uses
  `patch("src.observability.stream.consumer.RedisStreamConsumer")`) — mocks the exact class this
  ticket modifies; confirm the mock's patched interface (`connect()` returning bool,
  `read_and_process(handler, block_ms=...)` signature) still matches after the change — a
  new/renamed method here would silently break this mock without a signature-level test failure
  elsewhere.
- `tests/simulation_quality/test_kernel_simq_integration.py` (INFRA-318) — kernel broker-mode
  isolation; unaffected but in the same call graph.

## New Tests Required

Per the ticket's four Acceptance Criteria:

1. **"A transient handler failure results in a bounded retry, then a DLQ entry — not silent
   discard."**
   - Test name: `test_handler_exception_triggers_bounded_retry_then_dlq`
   - Category: unit (mock `self.client`, no live Redis needed to prove the retry-count/DLQ-call
     logic) **plus** an integration counterpart against real Redis.
   - Verifies: a `handler` that raises on every call is retried up to the chosen bound (not once,
     not infinitely), the original message is `xack`'d off the source stream only after the retry
     budget is exhausted, and an `xadd` (or equivalent) lands on the DLQ stream with the original
     payload + failure context preserved.
   - **Exact bound assertion (architecture-review correction, 2026-08-19):** the mocked unit case
     must assert the handler was invoked exactly `MAX_DELIVERY_ATTEMPTS` times (not
     `MAX_DELIVERY_ATTEMPTS + 1`) before the message is routed to DLQ — this pins the strict
     `<`/`>=` `times_delivered` boundary the plan's Step 4 now specifies, so a regression back to
     the `<=`/`>` off-by-one would fail this test rather than silently landing.
   - Location: `tests/unit/observability/test_stream_consumer_resilience.py` (new file) for the
     mocked unit case; `tests/integration/observability/test_stream_consumer_basic.py` (extend
     existing file) for the live-Redis integration case, following its existing
     `redis_available`-skip pattern.

2. **"A malformed payload still results in ack+drop (unchanged, already correct)."**
   - Test name: none new required — `test_live_stream_consumer_group_lifecycle`'s poison-pill
     assertion (see Regression Surface) already covers this; add an explicit **unit-level**
     `test_malformed_payload_still_ack_drop_not_retried` in the new
     `test_stream_consumer_resilience.py` file that asserts a malformed payload does **not**
     trigger the new retry-counting/DLQ code path at all (distinguishing it from a handler
     exception) — this is the regression the "Risks" section of investigation.md flags as easiest
     to accidentally break.
   - Category: unit.
   - Location: `tests/unit/observability/test_stream_consumer_resilience.py`.

3. **"A simulated process-death-before-ack scenario results in eventual redelivery via PEL
   reclaim, not permanent loss."**
   - Test name: `test_orphaned_pel_message_reclaimed_via_xclaim`
   - Category: integration (requires real Redis to exercise actual PEL state — a mocked client
     can't meaningfully simulate `XPENDING`/`XCLAIM` semantics).
   - Verifies: publish an event, read it via `xreadgroup` with a *different* consumer name and
     deliberately never `xack` it (simulating "handler succeeded, process died before ack") →
     construct a fresh `RedisStreamConsumer` (or call its reclaim method directly) → confirm the
     orphaned message is claimed (via `XPENDING`/`XCLAIM`) and delivered to the handler exactly
     once more, not lost, and not delivered infinitely.
   - Location: `tests/integration/observability/test_stream_consumer_basic.py` (extend) or a new
     `tests/integration/observability/test_stream_consumer_pel_reclaim.py`, matching the existing
     `redis_available`-skip pattern.

4. **"The reconnect loop backs off with jitter under sustained Redis unavailability."**
   - Test name: `test_reconnect_backoff_increases_with_consecutive_failures`,
     `test_reconnect_backoff_includes_jitter`, `test_reconnect_backoff_resets_after_success`
   - Category: unit (mock `redis.from_url`/`ping` to always raise; assert the computed delay
     sequence is monotonically bounded-increasing across consecutive failures, is capped, includes
     a randomized component so two consecutive delays aren't bit-identical, and resets to the
     floor after a successful `connect()`).
   - Location: `tests/unit/observability/test_stream_consumer_resilience.py`.
   - **Architecture-guard note:** since backoff must not use a real `time.sleep()` in a unit test
     (would make the suite slow/flaky), the delay-computation logic should be exposed as a
     pure/testable function or method (e.g. `_compute_backoff_delay(attempt: int) -> float`) rather
     than inlined directly in a sleep call — this is a testability requirement for Plan to design
     in, not an existing pattern to copy from elsewhere in the codebase (no jitter utility exists
     anywhere in `src/` today, confirmed by investigation.md's grep).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest \
  tests/unit/observability/test_event_stream_adapters.py \
  tests/unit/observability/test_redis_stream_adapter.py \
  tests/unit/observability/test_stream_consumer_resilience.py \
  tests/integration/observability/test_stream_consumer_basic.py \
  tests/integration/observability/test_stream_backpressure.py \
  tests/integration/test_observatory_stream_outage.py \
  tests/simulation_quality/test_feed.py \
  tests/simulation_quality/test_broker_feed_integration.py \
  tests/simulation_quality/test_kernel_simq_integration.py \
  -v
```

Never `pytest tests/`. The integration tests under `tests/integration/observability/` and
`tests/integration/test_observatory_stream_outage.py` self-skip via `redis_available` checks if no
local Redis is reachable on `redis://localhost:6379/0` — per the `ENGINE-LIVENESS-HEALTH-EPIC`
precedent, if that happens during Architecture-Verify, start a real Redis
(`docker run -p 6379:6379 redis:7-alpine`, matching the pattern already used in
`stored_artifacts/TCK-20260702-OBSISO-BROKER-CONFIG/`) rather than accepting a skip as verification
for AC #1/#3, which require real Redis PEL/stream state to prove.

## Anti-Drift Test Guards

- `test_malformed_payload_still_ack_drop_not_retried` (New Tests #2) is the primary guard against
  the single most likely implementation mistake: accidentally routing JSON-parse/pydantic-
  validation failures into the new retry+DLQ path instead of keeping them in the ack+drop path.
- `test_broker_feed_skips_gracefully_when_redis_unavailable` (INFRA-239, existing) guards against
  the new connect()-retry/backoff logic accidentally becoming a *blocking* call — `BrokerQualityFeed.start()`
  must still return promptly with `health="unavailable"` when Redis is down, not hang inside a
  backoff sleep on the calling thread's first attempt.
- `tests/unit/observability/test_event_stream_adapters.py::test_redis_adapter_resilient_missing_library`
  and the `INFRA-015/016/063/165` family guard against the new backoff logic being added in a way
  that assumes the `redis` package is always importable — the "package not installed" path (an
  `ImportError`, not a connection failure) must still degrade immediately, not enter a backoff
  loop waiting for a package that will never appear.
- `tests/integration/test_observatory_stream_outage.py::test_engine_continues_during_stream_outage`
  guards against any scope creep that touches `RedisStreamAdapter`'s publish-side behavior or the
  engine's non-blocking publish guarantee — this ticket must not slow down or block the publish
  path while fixing the consumer/reconnect side.
- A new `test_backoff_delay_is_pure_and_deterministic_given_seed` (or equivalent) should assert the
  backoff computation is a pure function of attempt-count-plus-injectable-RNG-seed — this guards
  against silently breaking determinism elsewhere if the backoff helper is ever imported into a
  determinism-sensitive path by a future change (defense in depth; this ticket's own code runs
  off the authoritative tick path, so this guard is precautionary, not a fix to an existing bug).
