---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
phase: done
date: 2026-08-17
tags: [observability]
---

# TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC

## Title
Redis Stream consumer: differentiate failure handling, add DLQ + PEL reclaim + reconnect backoff

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`src/observability/stream/consumer.py:79-102` ACKs malformed payloads and transient handler
failures identically — no dead-letter stream, no retry budget. A message whose handler succeeds
but whose process dies before the ACK call sits orphaned in the consumer group's PEL forever, with
no `XCLAIM`/`XPENDING` reclaim logic. On a sustained Redis outage the reconnect loop retries
roughly every ~100ms with no backoff or jitter. Blast radius is bounded — this stream is
downstream of, not part of, the authoritative gameplay pipeline (Tier 3, observability/
anomaly-detection only) — but the data loss is real and currently invisible beyond a single
`logger.error` line.

## Scope
Full findings are in `docs/plans/redis_stream_resilience_epic.md`. Concrete scope, all in
`src/observability/stream/consumer.py`:
- Separate malformed-payload handling (ack+drop, already correct) from handler-exception handling
  (bounded retry, then a literal DLQ stream on exhaustion).
- Add `XCLAIM`/`XPENDING`-based PEL reclaim for a message orphaned by a process death between
  handler success and ACK.
- Add backoff+jitter to the ~100ms reconnect loop.

## Out of Scope
- Any change to the authoritative gameplay pipeline.
- Introducing a different message broker or a generic retry framework.

## Acceptance Criteria
- [x] A transient handler failure results in a bounded retry, then a DLQ entry — not silent discard.
      Verified: `tests/unit/observability/test_stream_consumer_resilience.py::test_handler_exception_triggers_bounded_retry_then_dlq`
      (asserts exactly `MAX_DELIVERY_ATTEMPTS` (3) handler invocations, then one DLQ `xadd`) and
      `tests/integration/observability/test_stream_consumer_basic.py::test_handler_exception_triggers_bounded_retry_then_dlq_live`
      (live Redis).
- [x] A malformed payload still results in ack+drop (unchanged, already correct).
      Verified: `tests/unit/observability/test_stream_consumer_resilience.py::test_malformed_payload_still_ack_drop_not_retried`,
      `::test_invalid_json_payload_still_ack_drop_not_retried`, and the existing
      `tests/integration/observability/test_stream_consumer_basic.py::test_live_stream_consumer_group_lifecycle`
      poison-pill assertion (unmodified, still passes).
- [x] A simulated process-death-before-ack scenario results in eventual redelivery via PEL
      reclaim, not permanent loss.
      Verified: `tests/integration/observability/test_stream_consumer_pel_reclaim.py::test_orphaned_pel_message_reclaimed_via_xclaim`
      (live Redis: a message read by one consumer and never acked is reclaimed and delivered
      exactly once by a second consumer's sweep).
- [x] The reconnect loop backs off with jitter under sustained Redis unavailability.
      Verified: `tests/unit/observability/test_stream_consumer_resilience.py::test_reconnect_backoff_increases_with_consecutive_failures`,
      `::test_reconnect_backoff_includes_jitter`, `::test_reconnect_backoff_resets_after_success`,
      `::test_backoff_delay_is_pure_and_deterministic_given_seed`, `::test_first_connect_attempt_never_sleeps`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/redis_stream_resilience_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC/

## Related Code Areas
- src/observability/stream/consumer.py
- src/observability/stream/adapters.py

## Assumptions / Open Questions
- Exact DLQ stream naming/retention convention is an open decision for Plan phase.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; all three scope items touch one file
  (`consumer.py`) under one coherent theme — a textbook standard ticket, not a multi-ticket
  initiative. `staging_artifacts/TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC/` not yet created.

## Implementation Notes
Implemented `plan.md`'s six steps in order, entirely inside `src/observability/stream/consumer.py`:

1. **Backoff + jitter (`connect()`)** — added `BACKOFF_BASE_SECONDS`/`BACKOFF_CAP_SECONDS`/
   `BACKOFF_JITTER_RATIO` class constants, `_consecutive_failures` instance field, and a pure
   `_compute_backoff_delay(attempt, rng=None)` method. `connect()` sleeps before the connection
   attempt only when `_consecutive_failures > 0`; resets the counter to `0` on success; increments
   it on any exception. `read_and_process()`'s outer `except` also increments the counter (a
   read-time disconnect feeds the same backoff state the next `connect()` call will apply).
2. **DLQ write helper** — `self.dlq_stream_name = f"{stream_name}:dlq"` (derived, no new
   `ObservabilityConfig` accessor). `_send_to_dlq(msg_id, original_fields, reason, delivery_count)`
   merges `original_fields` with `dlq_reason`/`dlq_source_id`/`dlq_delivery_count`/`dlq_failed_at`
   and calls `xadd(dlq_stream_name, fields, maxlen=1000, approximate=True)`, matching
   `RedisStreamAdapter._send_to_redis`'s retention pattern; never raises to the caller.
3. **`_handle_message` extraction** — pulled the per-message body out of `read_and_process()`'s
   loop into `_handle_message(msg_id, payload, handler) -> Tuple[bool, bool]` (`acked`,
   `handler_ran`). Malformed-missing-payload and JSON/pydantic-parse-failure branches are
   byte-for-byte the prior ack+drop behavior (split into their own explicit `except
   (json.JSONDecodeError, ValueError, TypeError)` rather than falling into a catch-all). Only the
   handler-exception branch changed: on `handler(event)` raising, the message is **not** acked and
   stays in the PEL (`return False, True`) instead of being silently dropped.
4. **PEL reclaim sweep** — `_reclaim_pending(handler)`, wrapped in its own try/except (never raises
   into `read_and_process()`), called unconditionally once at the end of every
   `read_and_process()` call, inside the same outer `try`. Reads `xpending_range(..., idle=
   RECLAIM_IDLE_MS=30000)`, partitions entries by the **strict** `times_delivered < / >=
   MAX_DELIVERY_ATTEMPTS` (3) boundary per the architecture-review correction, claims the
   under-bound entries via `xclaim` and retries them through `_handle_message`, and routes
   at-or-over-bound entries to `_send_to_dlq` + `xack`.
5. **Parity ledger** — appended `INFRA-359`/`INFRA-360`/`INFRA-361` to
   `docs/parity_ledger/infrastructure.yaml` (re-verified `INFRA-358` was still the highest ID
   immediately before appending). Each new entry individually validates against
   `docs/parity_ledger/schema.json`'s item schema; a pre-existing, unrelated entry elsewhere in the
   file (index 284, `proof_type: feature`) already fails whole-file schema validation and is out of
   this ticket's scope (Scope Guards: append-only, do not touch existing entries).
6. **Docs** — added `## 7. Consumer-Side Resilience (DLQ, PEL Reclaim, Reconnect Backoff)` to
   `docs/architecture/observability_hot_path_safety_contract.md`, mirroring §5/§6's structure;
   sections 1-6 untouched. Ran `make knowledge-index-update` and `graphify update .` after the doc
   change (no topology change detected by graphify).

**Delivery-count pseudocode gap (flagged in advance by architecture review) — resolution:**
the plan's Step 4 pseudocode partitioned only `message_id` values into `retry_ids`/`exhausted_ids`,
which would have lost each entry's `times_delivered` before the `_send_to_dlq(...,
delivery_count)` call. Resolved by partitioning on the **full pending-entry dicts** returned by
`xpending_range` (`retry_entries`/`exhausted_entries`, not `retry_ids`/`exhausted_ids`), then
deriving `retry_ids` from `retry_entries` only where the `xclaim` call actually needs bare IDs.
For the exhausted branch, `entry["times_delivered"]` (already present in the same dict pulled
straight from `xpending_range`'s parsed response) is passed directly to `_send_to_dlq` as
`delivery_count` — no re-lookup needed, since the value was already in hand from the same
`xpending_range` call that decided the entry was exhausted.

**Test infrastructure note:** integration tests require live Redis; none was running in this
environment, so a temporary `redis:7-alpine` Docker container was started for the integration
test run and stopped/removed afterward — no persistent infrastructure was added to the repo.

## Test Summary
`.venv/bin/python3 -m pytest` run in two passes (Redis-down, then Redis-up via a temporary Docker
container) covering the full test_plan.md scope:
- Redis down: 40 passed (`test_event_stream_adapters.py`, `test_redis_stream_adapter.py`,
  `test_stream_consumer_resilience.py` [new], `test_feed.py`, `test_kernel_simq_integration.py`).
- Redis up: 7 passed, 3 skipped (env-var-gated, pre-existing) (`test_stream_consumer_basic.py`
  [extended], `test_stream_consumer_pel_reclaim.py` [new], `test_stream_backpressure.py`,
  `test_observatory_stream_outage.py`, `test_broker_feed_integration.py`).
- The one failure seen when both groups were run together in a single Redis-up process
  (`test_redis_adapter_resilient_missing_library`) was confirmed to be a pre-existing environment
  artifact of having a live, reachable Redis during that specific test (it deletes `redis` from
  `sys.modules` to simulate a missing package, then re-imports it successfully since the real
  package is installed; with live Redis reachable, `ping()` then succeeds, producing `healthy`
  instead of the expected `degraded`) — reproduced on unmodified `consumer.py`/`adapters.py` with
  no code changes involved, confirmed to pass standalone both with and without live Redis running
  as expected of the two isolated runs above. Not a regression from this ticket; `adapters.py` is
  untouched.
- Explicitly re-confirmed per task instruction:
  `test_handler_exception_triggers_bounded_retry_then_dlq` asserts `handler.call_count ==
  MAX_DELIVERY_ATTEMPTS == 3` (not 4), pinning the strict `<`/`>=` boundary.

## Files Changed
- `src/observability/stream/consumer.py` — all six plan steps (backoff/jitter, DLQ helper,
  `_handle_message` extraction, PEL reclaim sweep).
- `tests/unit/observability/test_stream_consumer_resilience.py` (new) — unit coverage for all
  four ACs (mocked Redis client).
- `tests/integration/observability/test_stream_consumer_basic.py` — extended with
  `test_handler_exception_triggers_bounded_retry_then_dlq_live` (live Redis).
- `tests/integration/observability/test_stream_consumer_pel_reclaim.py` (new) —
  `test_orphaned_pel_message_reclaimed_via_xclaim` (live Redis).
- `docs/parity_ledger/infrastructure.yaml` — appended `INFRA-359`, `INFRA-360`, `INFRA-361`.
- `docs/architecture/observability_hot_path_safety_contract.md` — added `## 7. Consumer-Side
  Resilience (DLQ, PEL Reclaim, Reconnect Backoff)`.

## Completion Summary
Implemented all four ACs entirely inside `RedisStreamConsumer`
(`src/observability/stream/consumer.py`): handler exceptions now retry via Redis's own
`XPENDING`/`XCLAIM` PEL-reclaim mechanism up to `MAX_DELIVERY_ATTEMPTS = 3` total delivery
attempts before routing to a derived DLQ stream (`{stream_name}:dlq`) and acking off the source
stream; the malformed-payload ack+drop path is preserved byte-for-byte; a process-death-before-ack
orphaned PEL entry is now reclaimed and redelivered rather than lost forever; and `connect()` now
backs off with jitter (base 0.2s, doubling, capped at 30s, ±20% jitter) across consecutive
failures, resetting on success, with the first attempt after any reset never sleeping so
`BrokerQualityFeed.start()`'s prompt-return contract is preserved. New unit tests
(`tests/unit/observability/test_stream_consumer_resilience.py`) and two new/extended integration
tests against live Redis cover all four ACs; the full test_plan.md regression surface was run and
passes (one unrelated, pre-existing, environment-coupled failure was investigated and confirmed
not a regression). Parity ledger entries `INFRA-359`/`INFRA-360`/`INFRA-361` and a new §7 in
`observability_hot_path_safety_contract.md` document the new behavior.
