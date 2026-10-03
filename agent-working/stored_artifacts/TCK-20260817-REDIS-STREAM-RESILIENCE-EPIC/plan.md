---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
artifact_type: plan
tags: [observability]
---

# Implementation Plan — TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC

## Summary

All work lands entirely inside `src/observability/stream/consumer.py` (`RedisStreamConsumer`), touching
no caller code. The core design insight: a handler-exception failure (AC #1) and a process-death-before-ack
failure (AC #3) are the *same underlying state* from Redis's point of view — an entry sitting unacked in
the consumer group's PEL — so both are fixed by one unified PEL-reclaim mechanism driven by Redis's own
`XPENDING` per-message delivery counter, rather than two separate code paths. Reconnect backoff+jitter
(AC #4) is a separate, independent change confined to `connect()`. The malformed-payload path (AC #2) is
explicitly preserved byte-for-byte. Six ordered steps: (1) backoff/jitter in `connect()`, (2) a DLQ-write
helper using the same `xadd(..., maxlen=..., approximate=True)` pattern already used by
`RedisStreamAdapter`, (3) stop unconditionally ACKing on handler exceptions (extracting a small
`_handle_message` helper so the same per-message logic is reusable), (4) a PEL-reclaim sweep
(`_reclaim_pending`) wired into `read_and_process()` that claims idle entries via `XCLAIM`, retries them
through `_handle_message` while `XPENDING`'s `times_delivered` stays under a bound, and routes exhausted
entries to the DLQ, (5) new parity ledger entries, (6) a new section in
`observability_hot_path_safety_contract.md`. No unresolved questions remain — both open questions from
investigation.md are decided below with concrete values, verified against the installed `redis-py==7.3.0`
client's actual method signatures and against this codebase's existing stream-naming/retention precedent.

**Decision 1 — DLQ stream naming/retention:** literal, derived name `f"{self.stream_name}:dlq"` (a
second Redis Stream, not a new broker), computed once in `__init__`, no new `ObservabilityConfig`
accessor. Retention: `xadd(dlq_stream_name, fields, maxlen=1000, approximate=True)`, mirroring the only
existing retention precedent in this codebase, `RedisStreamAdapter._send_to_redis`'s
`self.client.xadd(self.stream_name, payload, maxlen=self.max_queue_size, approximate=True)`
(`src/observability/stream/adapters.py:187`). A literal `1000` constant (not a new env-backed accessor)
matches the ticket's own Scope wording ("a literal DLQ stream") and the Out-of-Scope "no generic retry
framework" — a single derived string and one literal retention cap is not durable-state-schema-worthy of
its own env-accessor per `ObservabilityConfig`'s existing pattern (`get_redis_url`/`get_stream_name`/
`get_max_queue_size`, all `src/observability/config.py:330-354`), which exists for values operators need
to tune per-deployment-profile; DLQ name/cap are not that.

**Decision 2 — bounded retry mechanism: XPENDING-driven, not a fixed in-process counter.** Confirmed
usable: `redis-py==7.3.0` is installed (`.venv/bin/python3 -c "import redis; print(redis.__version__)"`
→ `7.3.0`), and its `Redis.xpending_range(name, groupname, min, max, count, consumername=None,
idle=None)` and `Redis.xclaim(name, groupname, consumername, min_idle_time, message_ids, idle=None,
time=None, retrycount=None, force=False, justid=False)` signatures were read directly via
`inspect.signature`/`inspect.getsource` in this environment — both support the `idle`/`min_idle_time`
filtering this design needs, and `xpending_range` returns per-entry `times_delivered`, Redis's own native
per-message delivery counter (this is `XPENDING`'s standard "detail" response shape, which redis-py
parses via `parse_detail=True`, visible in `xpending_range`'s source). The existing consumer group setup
(`xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)`, `consumer.py:43`) already
creates the group needed for this — no setup change required. Using `times_delivered` instead of an
in-process counter is more correct here specifically because retries in this design happen via PEL
reclaim (a *different* `RedisStreamConsumer` instance, potentially in a different process, may perform
the reclaim) — an in-memory dict keyed by message ID would not survive a reconnect or process restart and
would not be visible to a different consumer instance reclaiming the same group's PEL, while Redis's own
counter is authoritative and shared. Bound: `MAX_DELIVERY_ATTEMPTS = 3` (matches the attempt-count shape
already familiar from `WebhookAlertSink.max_retries=3`, `src/observability/alerts/sinks.py:49` — read as
a familiar number to keep operator mental models consistent, not as shared code; no import or call
between the two files).

## Steps

### Step 1 — Backoff + jitter in `connect()`
**Files:** `src/observability/stream/consumer.py`

**Change:** In `__init__` (currently `consumer.py:15-27`, verified: stores `redis_url`, `stream_name`,
`group_name`, `consumer_name`, `client=None`, `_connected=False`, no retry/backoff fields), add:
- Class constants `BACKOFF_BASE_SECONDS = 0.2`, `BACKOFF_CAP_SECONDS = 30.0`, `BACKOFF_JITTER_RATIO = 0.2`.
- Instance field `self._consecutive_failures = 0`.
- A pure method `_compute_backoff_delay(self, attempt: int, rng: Optional["random.Random"] = None) -> float`
  (add `import random` at module top): `capped = min(self.BACKOFF_CAP_SECONDS, self.BACKOFF_BASE_SECONDS *
  (2 ** max(0, attempt - 1)))`; `jitter = capped * self.BACKOFF_JITTER_RATIO`; `r = rng or random`; return
  `max(0.0, capped + r.uniform(-jitter, jitter))`. Deterministic and testable given an injected
  `random.Random(seed)` — satisfies the test_plan's "pure function of attempt-count-plus-injectable-RNG-seed"
  requirement (`test_backoff_delay_is_pure_and_deterministic_given_seed`). The `capped` floor is strictly
  non-decreasing in `attempt` until the cap, satisfying "monotonically bounded-increasing"; the `uniform`
  term satisfies "includes a randomized component."
- In `connect()` (currently `consumer.py:29-51`, verified: builds client, pings, creates group, on any
  exception logs+sets `_connected=False`+returns `False`, **no sleep anywhere**): at the very top, before
  the existing `try:`, add `if self._consecutive_failures > 0: time.sleep(self._compute_backoff_delay(
  self._consecutive_failures))` (add `import time` at module top). On the success path (end of the
  existing `try:` block, right before `return True`), add `self._consecutive_failures = 0`. In the
  existing `except Exception as e:` block (currently lines 48-51), add `self._consecutive_failures += 1`
  before the existing `return False`.
- In `read_and_process()`'s outer `except Exception as e:` (currently `consumer.py:104-108`, verified:
  sets `self._connected = False`, returns `0`, no backoff), also add `self._consecutive_failures += 1` —
  a read-time disconnect must feed the same backoff counter, since the *next* `read_and_process()` call's
  `if not self._connected: self.connect()` (lines 58-60) is what will actually apply the sleep.

**Other writers to this state:** `_consecutive_failures` and the backoff constants are new fields owned
exclusively by this class; no other module reads or writes them. `connect()` itself is called from two
call sites — `LiveAnomalyWorker._run_loop` (`src/observability/anomaly/worker.py:219`, and again inside
`read_and_process`'s lines 58-60) and `BrokerQualityFeed.start()` (`src/simulation_quality/feed.py:84`,
and again inside `read_and_process`). Both are unaffected by this change's *call signature* (still
`connect() -> bool`), and both benefit from the fix uniformly since the sleep lives inside `connect()`
itself, not in either caller's loop — this is why `worker.py`/`feed.py` do not need to change. Critically,
the **first-ever** call to `connect()` (or the first call after a success, when `_consecutive_failures ==
0`) never sleeps — this preserves `BrokerQualityFeed.start()`'s "return promptly with `health=unavailable`"
contract (`INFRA-239`, `tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable`),
since `start()` calls `connect()` exactly once and returns based on its boolean result — it never loops
itself, so the backoff sleep (which only fires on the *second and later* attempt) never blocks it. The
`except Exception as e:` in `connect()` also catches `ImportError` from `import redis` (missing package) —
this path also skips the sleep on its first occurrence and, because there is no internal loop, never spins
waiting for a package that will never appear (guards `INFRA-015/016/063/165` and
`test_redis_adapter_resilient_missing_library`, none of which exercise `connect()`'s sleep since the sleep
only ever runs before a network attempt is *retried*, not on the read of `redis`'s absence itself).

**Do NOT touch:** `worker.py` `_run_loop`'s `time.sleep(0.1)` (line 288) or `feed.py`'s `_consume_loop`
(no sleep) — both stay as-is; the backoff fix is entirely self-contained in `consumer.py`.

**Verify:** `test_reconnect_backoff_increases_with_consecutive_failures`,
`test_reconnect_backoff_includes_jitter`, `test_reconnect_backoff_resets_after_success`,
`test_backoff_delay_is_pure_and_deterministic_given_seed` (new, `tests/unit/observability/test_stream_consumer_resilience.py`);
regression: `tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable`,
`tests/unit/observability/test_event_stream_adapters.py::test_redis_adapter_resilient_missing_library`.

---

### Step 2 — DLQ write helper
**Files:** `src/observability/stream/consumer.py`

**Change:** In `__init__`, add `self.dlq_stream_name = f"{self.stream_name}:dlq"`. Add a new private
method `_send_to_dlq(self, msg_id: str, original_fields: Dict[str, Any], reason: str,
delivery_count: int) -> bool` that builds `dlq_fields = {**original_fields, "dlq_reason": str(reason)[:500],
"dlq_source_id": str(msg_id), "dlq_delivery_count": str(delivery_count), "dlq_failed_at":
datetime.now(timezone.utc).isoformat()}` (add `from datetime import datetime, timezone` at module top) and
calls `self.client.xadd(self.dlq_stream_name, dlq_fields, maxlen=1000, approximate=True)` inside a
try/except that logs and returns `False` on any exception, `True` on success — never raises to the
caller, matching every other method in this file's shape (`close()`, `connect()`,
`read_and_process()` — cited above — all degrade to logging + a safe return rather than raising). Field
naming (`event_type`/`event_category`/`severity`/`tick`/`message`/`payload`) in `original_fields` matches
exactly what `RedisStreamAdapter._send_to_redis` writes to the source stream
(`src/observability/stream/adapters.py:178-187`, verified: `payload = {"event_type": ..., "event_category":
..., "severity": ..., "tick": ..., "message": ..., "payload": event.model_dump_json()}`), because
`original_fields` here is exactly the `payload` dict `xreadgroup` hands back for that same message
(`consumer.py:78`, `for msg_id, payload in messages:`) — passing it through unchanged onto the DLQ
preserves the original payload, and the `dlq_*` keys layer failure context on top, satisfying the test
plan's "original payload + failure context preserved" requirement.

**Other writers to this stream:** none exist today — confirmed via investigation.md's repo-wide grep for
`dead.letter|DLQ|dead_letter` (zero matches) and this step's own `f"{self.stream_name}:dlq"` naming, which
does not collide with any stream name referenced elsewhere in `src/` (checked: only `simulation:events`
default and its env-overridden variants are used anywhere in `factory.py`/`config.py`/`worker.py`/`feed.py`).
This step only adds the helper method; it is not yet called from anywhere (wired in Step 4), so it has no
runtime effect until Step 4 lands.

**Do NOT touch:** `RedisStreamAdapter`'s `xadd` call or `maxlen`/`max_queue_size` semantics
(`adapters.py:187`) — only the *pattern* is reused, the adapter class itself is unmodified.

**Verify:** new unit test asserting `_send_to_dlq` (called directly with a mocked `self.client`) invokes
`xadd` with the DLQ stream name, `maxlen=1000`, `approximate=True`, and a fields dict containing the
original `payload` key plus `dlq_reason`/`dlq_source_id`/`dlq_delivery_count`/`dlq_failed_at` — part of
`test_handler_exception_triggers_bounded_retry_then_dlq`'s setup in
`tests/unit/observability/test_stream_consumer_resilience.py`.

---

### Step 3 — Stop unconditional ACK on handler exceptions; preserve malformed-payload path exactly
**Files:** `src/observability/stream/consumer.py`

**Change:** Extract the per-message body currently inline in `read_and_process()`'s `for msg_id, payload
in messages:` loop (`consumer.py:78-102`, verified) into a new private method
`_handle_message(self, msg_id: str, payload: Dict[str, Any], handler: Callable[[SimulationEvent], None])
-> bool` returning `True` if the message was ACKed (handled — either successfully processed, or correctly
identified as malformed and dropped) and `False` if it was **not** ACKed and must remain in the PEL for
later reclaim. Logic, preserving exact behavior for two of the three branches and changing only the third:
1. **Malformed branch (`consumer.py:80-85`, unchanged verbatim):** `raw_payload = payload.get("payload")`;
   if falsy, log warning, `self.client.xack(...)`, `return True`. This is byte-for-byte the existing
   logic — AC #2 requires it stay unchanged.
2. **Parse/validation branch (currently folded into the single `except Exception` at lines 96-102 today,
   now split out explicitly):** wrap `json.loads(raw_payload)` and `SimulationEvent(**event_dict)` in
   their own `try/except (json.JSONDecodeError, ValueError, TypeError) as ex:` — on failure, log
   (`"Malformed stream event payload {msg_id}: {ex}"`), `xack`, `return True`. This preserves today's
   "JSON-parse/pydantic-validation errors are ack+drop, grouped with malformed" behavior (investigation.md's
   Risks section flags this as the exact regression to avoid) — it is now handled explicitly rather than
   by accident of a shared `except Exception`.
3. **Handler-exception branch (the actual bug, `consumer.py:96-102` today):** call `handler(event)` inside
   its own `try/except Exception as ex:`. On success, `self.client.xack(...)`, `return True`. **On
   exception: log (`"Handler failed for stream event {msg_id} (will remain pending for reclaim): {ex}"`),
   do NOT call `xack`, `return False`.** This is the one substantive behavior change: the message now
   stays in the consumer group's PEL instead of being silently dropped.

Update `read_and_process()`'s loop body (`consumer.py:77-102`) to call `self._handle_message(msg_id,
payload, handler)`; increment `processed_count` only when it returns `True` **and** the message was
actually handler-processed (not malformed/parse-dropped) — to keep `processed_count`'s existing meaning
("events successfully delivered to the handler") intact for callers that rely on its return value as a
"did work happen" signal (`LiveAnomalyWorker._run_loop`'s `processed_any` check, `worker.py:244-289`,
which the investigation confirms drives that loop's own 100ms sleep — not modified by this ticket, but its
input, `read_and_process()`'s return value, must keep meaning what it always meant). Concretely: have
`_handle_message` return a three-way result (e.g. a small enum or a tuple `(acked: bool, handler_ran: bool)`)
rather than a bare `bool`, and have the loop increment `processed_count` only on `handler_ran and acked`.

**Other writers to the PEL:** this is the first code in the repo to ever leave a message unacked
deliberately (confirmed via investigation.md's grep: zero existing `xclaim`/`xpending` usage anywhere).
The PEL is otherwise only ever written to by `xreadgroup` (adds entries) and `xack` (removes entries) —
both already used elsewhere in this same file and unchanged by this step. No other module ever calls
`xack`/`xreadgroup` against this stream+group — confirmed via investigation.md's repo-wide grep for
`RedisStreamConsumer` (exactly two call sites, both already covered).

**Do NOT touch:** the malformed branch's exact ack+drop behavior (see Anti-Drift Notes) — this is the
single easiest way to accidentally regress AC #2 while fixing AC #1.

**Verify:** `test_malformed_payload_still_ack_drop_not_retried` (new,
`tests/unit/observability/test_stream_consumer_resilience.py`); regression:
`tests/integration/observability/test_stream_consumer_basic.py::test_live_stream_consumer_group_lifecycle`
(its poison-pill assertion, `processed_poison == 0`, no exception surfaces, is the sharpest existing guard
for the malformed path).

---

### Step 4 — PEL reclaim sweep, wired into `read_and_process()`
**Files:** `src/observability/stream/consumer.py`

**Change:** Add class constants `RECLAIM_IDLE_MS = 30000` (30s — well above the `block_ms=500`/`1000`
read cadence used by both callers, so a message still legitimately in-flight under normal processing is
never mistaken for orphaned) and `MAX_DELIVERY_ATTEMPTS = 3` (Decision 2, above). Add a new private method
`_reclaim_pending(self, handler: Callable[[SimulationEvent], None]) -> None`, wrapped entirely in a
try/except that logs and returns on any failure (never raises to caller, per file-wide convention):
1. `pending = self.client.xpending_range(self.stream_name, self.group_name, min="-", max="+", count=50,
   idle=self.RECLAIM_IDLE_MS)` — confirmed via `inspect.signature`/`inspect.getsource` on the installed
   `redis-py==7.3.0` client that this signature and its `idle`-filtered "detail" response (containing
   `message_id`/`consumer`/`time_since_delivered`/`times_delivered` per entry) are real and available.
2. Partition `pending` into `retry_ids = [e["message_id"] for e in pending if e["times_delivered"] <
   self.MAX_DELIVERY_ATTEMPTS]` and `exhausted_ids = [e["message_id"] for e in pending if e["times_delivered"]
   >= self.MAX_DELIVERY_ATTEMPTS]`.

   **Boundary correction (architecture-review, 2026-08-19):** the comparison must use the pre-claim
   `times_delivered` value against a **strict** `<`/`>=` split, not `<=`/`>`. `xclaim` (called below,
   without `justid`) increments Redis's native delivery counter as a side effect of the very claim that
   triggers the next handler attempt — so a `<=` retry check lets an entry already at
   `times_delivered == MAX_DELIVERY_ATTEMPTS` (i.e. already attempted `MAX_DELIVERY_ATTEMPTS` times) get
   claimed and handled a `MAX_DELIVERY_ATTEMPTS + 1`-th time before the *next* sweep finally routes it to
   the DLQ. The strict `<`/`>=` split ensures the DLQ path fires as soon as `times_delivered` reaches
   `MAX_DELIVERY_ATTEMPTS`, so at most `MAX_DELIVERY_ATTEMPTS` total handler invocations ever occur —
   matching AC #1's "bounded retry" as literally stated, not `MAX_DELIVERY_ATTEMPTS + 1`.
3. For `retry_ids` (non-empty case only): `claimed = self.client.xclaim(self.stream_name, self.group_name,
   consumername=self.consumer_name, min_idle_time=self.RECLAIM_IDLE_MS, message_ids=retry_ids)` — returns
   `(msg_id, fields)` pairs in the same shape `xreadgroup` uses. For each, call
   `self._handle_message(msg_id, fields, handler)` (reusing Step 3's helper — same malformed/parse/handler
   branching applies to a reclaimed message as to a freshly-read one). A message that fails again simply
   stays unacked; Redis's own delivery counter increments on the `xclaim` call itself (confirmed: `xclaim`'s
   signature exposes an optional `retrycount` override, meaning the counter is tracked and incremented by
   Redis natively when left unset — this is standard `XCLAIM` behavior, not code this ticket implements),
   so the next sweep will see a higher `times_delivered` without this method managing any counter itself.
4. For `exhausted_ids` (non-empty case only): for each id, `entries = self.client.xrange(self.stream_name,
   min=msg_id, max=msg_id, count=1)` to fetch its fields (an entry can be ACKed without first being
   claimed — `XACK` only requires group membership, not consumer ownership — so `xrange` is used here
   instead of `xclaim` to avoid an unnecessary ownership transfer for a message about to be discarded from
   the group's PEL), then `self._send_to_dlq(msg_id, entries[0][1], "max delivery attempts exceeded",
   delivery_count)` (Step 2's helper) followed by `self.client.xack(self.stream_name, self.group_name,
   msg_id)`.

Call `self._reclaim_pending(handler)` once near the end of `read_and_process()` (after the main `">"` loop
completes, inside the same outer `try:` so its own internal exception handling — not the outer
`except Exception as e:` at lines 104-108 — is what governs it, keeping a reclaim-sweep failure from being
misreported as a stream-read/connection failure).

**Other writers to the PEL / this group:** `LiveAnomalyWorker` uses `consumer_group="observatory:consumers"`
(default, `src/observability/anomaly/worker.py:143`) and `BrokerQualityFeed` uses
`consumer_group="quality_scoring"` (default, `src/simulation_quality/feed.py:62`) — **verified distinct**
by reading both constructors directly. Because `xpending_range`/`xclaim` are scoped to
`(self.stream_name, self.group_name)`, each `RedisStreamConsumer` instance's reclaim sweep only ever sees
PEL entries within its own group, even though both groups may consume the same underlying `stream_name`
("simulation:events" default) — there is no cross-contamination between the two features' reclaim logic.
Within a single group, multiple consumer names may coexist (e.g. multiple `LiveAnomalyWorker` instances
with different `worker_id`s) — `_reclaim_pending`'s `xpending_range` call has no `consumername` filter, so
one live consumer's sweep can and will claim orphaned entries originally delivered to a *different*,
now-dead peer in the same group. This is intended Redis Streams consumer-group semantics (the entire
purpose of `XCLAIM`), not a hazard, and the 30s idle floor is what protects a peer that is merely slow
(not dead) from having its in-flight work stolen.

**Do NOT touch:** `xreadgroup`'s `">"` read semantics in the main loop (unaffected — the reclaim sweep
only ever touches already-pending entries, never competes with `">"` for newly-arriving messages).

**Verify:** `test_handler_exception_triggers_bounded_retry_then_dlq` (unit, mocked client, and its
integration counterpart against live Redis — both in the locations test_plan.md specifies:
`tests/unit/observability/test_stream_consumer_resilience.py` and
`tests/integration/observability/test_stream_consumer_basic.py`); `test_orphaned_pel_message_reclaimed_via_xclaim`
(integration, `tests/integration/observability/test_stream_consumer_basic.py` or a new
`tests/integration/observability/test_stream_consumer_pel_reclaim.py`).

---

### Step 5 — Parity ledger entries
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Before appending, re-run `grep -oE 'INFRA-[0-9]+' docs/parity_ledger/infrastructure.yaml |
sort -t- -k2 -n | tail -1` to get the current highest ID — **do not assume it is still `INFRA-358`**
(the value confirmed at plan-writing time via the same command); other tickets may have appended entries
since. Add three new entries (schema per `docs/parity_ledger/schema.json`, verified: `status: verified`
requires both `v2_evidence` and `test_path` as non-null strings; `priority` enum is `P0`/`P1`/`P2` only):
1. Bounded retry + DLQ on handler-exception exhaustion (Steps 2-4): `text`: "RedisStreamConsumer retries a
   transient handler failure up to MAX_DELIVERY_ATTEMPTS via PEL reclaim, then routes the message to a
   DLQ stream instead of silent ack+drop", `status: verified`, `priority: P1`, `v2_evidence:
   src/observability/stream/consumer.py: RedisStreamConsumer._handle_message,
   RedisStreamConsumer._send_to_dlq, RedisStreamConsumer._reclaim_pending`, `test_path:
   tests/unit/observability/test_stream_consumer_resilience.py::test_handler_exception_triggers_bounded_retry_then_dlq`.
2. PEL reclaim via XCLAIM/XPENDING (Step 4): `text`: "Orphaned consumer-group PEL entries (handler
   succeeded but process died before ack) are reclaimed via XPENDING/XCLAIM and redelivered, not lost",
   `status: verified`, `priority: P1`, `v2_evidence: src/observability/stream/consumer.py:
   RedisStreamConsumer._reclaim_pending`, `test_path:
   tests/integration/observability/test_stream_consumer_basic.py::test_orphaned_pel_message_reclaimed_via_xclaim`
   (or the new dedicated file if Step 4 creates one — match whichever path the test actually lands in).
3. Reconnect backoff+jitter (Step 1): `text`: "RedisStreamConsumer.connect() backs off with jitter across
   consecutive failures under sustained Redis unavailability, capped, and resets after a successful
   connect", `status: verified`, `priority: P1`, `v2_evidence: src/observability/stream/consumer.py:
   RedisStreamConsumer.connect, RedisStreamConsumer._compute_backoff_delay`, `test_path:
   tests/unit/observability/test_stream_consumer_resilience.py::test_reconnect_backoff_increases_with_consecutive_failures`.

**Other writers to this file:** `infrastructure.yaml` is a shared, append-only ledger that any ticket
touching the observability/infrastructure subsystem may append to; this is why the highest-ID re-check
above is a hard requirement, not a formality — appending at a stale ID risks a duplicate `id` value if
another ticket landed an entry concurrently. Do not renumber or edit any existing entry (including
`INFRA-015/016/063/165/239/317/318/358` cited in investigation.md) — append only.

**Do NOT touch:** any existing entry's `status`/`v2_evidence`/`test_path` — this ticket only adds new
entries, per investigation.md's confirmation that no existing entry covers this behavior.

**Verify:** entries validate against `docs/parity_ledger/schema.json` (re-run whatever schema-validation
tool/script this repo's Finalize phase uses before considering this step complete); all three `test_path`
values point at tests that actually exist and pass after Steps 1-4.

---

### Step 6 — Document consumer-side resilience behavior
**Files:** `docs/architecture/observability_hot_path_safety_contract.md`

**Change:** This doc currently has six sections (`## 1. Hot Path Definition` through `## 6. Worker
Lifecycle Contract`, confirmed via direct read) and documents only the *publish* side
(`RedisStreamAdapter`/`EventRecorder`) — no section describes consumer-side failure handling, DLQ
semantics, or PEL reclaim (confirmed in investigation.md). Add a new `## 7. Consumer-Side Resilience
(DLQ, PEL Reclaim, Reconnect Backoff)` section, mirroring §5/§6's structure (mode/lifecycle table +
prose), covering: the DLQ stream naming/retention convention (Decision 1 above), the
`MAX_DELIVERY_ATTEMPTS`/`RECLAIM_IDLE_MS` bounds and why they're `XPENDING`-driven (Decision 2 above), and
the backoff/jitter shape from Step 1 — framed as this section's own "graceful degradation, drop over
block" instance of §4.2's transferable principle (the consumer gives up and DLQs rather than blocking
indefinitely).

**Other writers to this file:** none identified — it is a single-owner architecture doc with no other
in-flight ticket in this session touching it.

**Do NOT touch:** sections 1-6 (publish-side content) — unmodified, since D23 already confirms that side
is correct and contract-compliant and this ticket's Scope never touches `RedisStreamAdapter`.

**Verify:** no automated test; reviewed for accuracy against Steps 1-4's actual landed code during
Architecture-Verify.

## Scope Guards

- Do not modify `src/observability/anomaly/worker.py` (`LiveAnomalyWorker._run_loop`'s `time.sleep(0.1)`
  at line 288, or its `processed_any` logic) beyond relying on `read_and_process()`'s return value
  continuing to mean what it always meant (Step 3's explicit note).
- Do not modify `src/simulation_quality/feed.py` (`BrokerQualityFeed._consume_loop`) at all.
- Do not extract or introduce a shared retry/backoff helper with `src/observability/alerts/sinks.py`
  (`WebhookAlertSink._dispatch_with_retry`) — explicitly out of scope per the ticket. `WebhookAlertSink`
  itself is not modified in any step above.
- Do not modify `RedisStreamAdapter`'s publish-side logic in `src/observability/stream/adapters.py`
  (queue eviction, backpressure, `health()`, `flush()`, `close()`) — D23-confirmed correct, untouched.
- Do not add a new `ObservabilityConfig` accessor for the DLQ stream name or retention cap — Decision 1
  above settles this as literal/derived, not configurable.
- Do not introduce RabbitMQ, Kafka, or any new broker dependency — the DLQ is a second Redis Stream.
- Do not change the malformed-payload branch's ack+drop behavior (Step 3) — this is the sharpest
  regression risk in the whole plan.
- Do not edit `docs/audits/D23_architecture_resilience.md`, `docs/plans/redis_stream_resilience_epic.md`,
  or `docs/plans/architecture_resilience_remediation_roadmap.md` — treated as static point-in-time
  records per the sibling ticket's precedent (investigation.md, "Docs Requiring Update").
- Do not manually edit `docs/REGISTRY.yaml` — regenerated automatically at Finalize.

## Dependency Map

- Step 1 (backoff) is fully independent of Steps 2-4 — can be implemented and verified first or last,
  no shared state with the DLQ/reclaim work beyond living in the same file.
- Step 2 (DLQ helper) has no runtime callers until Step 4 wires it in, but must land before Step 4.
- Step 3 (stop-ack-on-handler-exception + `_handle_message` extraction) must land before Step 4, since
  Step 4's reclaim path reuses `_handle_message`.
- Step 4 depends on both Step 2 (`_send_to_dlq`) and Step 3 (`_handle_message`).
- Steps 5 and 6 (docs/parity) depend on Steps 1-4 being landed and their exact method names/behavior
  finalized, since both cite specific method names and test paths.
- Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 (matches the numbering above), but 1 could run
  in parallel with 2-3 if convenient since it touches disjoint parts of `connect()`/`__init__` vs.
  `read_and_process()`'s message loop.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A transient handler failure results in a bounded retry, then a DLQ entry — not silent discard. | Steps 2, 3, 4 | `test_handler_exception_triggers_bounded_retry_then_dlq` (unit + integration) |
| A malformed payload still results in ack+drop (unchanged, already correct). | Step 3 | `test_malformed_payload_still_ack_drop_not_retried` (new); `test_live_stream_consumer_group_lifecycle` (regression) |
| A simulated process-death-before-ack scenario results in eventual redelivery via PEL reclaim, not permanent loss. | Step 4 | `test_orphaned_pel_message_reclaimed_via_xclaim` |
| The reconnect loop backs off with jitter under sustained Redis unavailability. | Step 1 | `test_reconnect_backoff_increases_with_consecutive_failures`, `test_reconnect_backoff_includes_jitter`, `test_reconnect_backoff_resets_after_success` |

## Anti-Drift Notes

- The malformed-payload branch (`consumer.py:80-85` today) and the JSON-parse/pydantic-validation
  sub-case (folded into the generic `except` today, split out explicitly in Step 3) must both remain
  ack+drop — only the *handler-raised* sub-case changes to leave-unacked. Getting this split wrong in
  either direction either regresses AC #2 (if parse errors start retrying) or fails to fix AC #1 (if
  handler exceptions keep getting acked).
- `_reclaim_pending` must never raise into `read_and_process()`'s caller — wrap it in its own try/except,
  consistent with every other method in this file degrading to logging + a safe return.
- `RECLAIM_IDLE_MS = 30000` must stay comfortably above both callers' `block_ms` (500 for
  `BrokerQualityFeed`, 500 for `LiveAnomalyWorker` per investigation.md) so in-flight, still-processing
  messages are never mistaken for orphaned and stolen from a live, slow (not dead) consumer.
  `test_orphaned_pel_message_reclaimed_via_xclaim`'s live-Redis integration test only proves the mechanism
  works, not the specific constant's tuning — treat 30s as a starting point, adjustable later without an AC.
  ok if changed in this same ticket for a well-justified reason, but adjusting it is not itself an AC.
- Do not let Step 4's `xclaim` calls run when `retry_ids` is empty, or `xrange`/`_send_to_dlq`/`xack`
  calls run when `exhausted_ids` is empty — an empty-list guard avoids unnecessary Redis round-trips on
  the (expected-common) case of nothing pending to reclaim.
- `processed_count`'s meaning (successfully handler-processed messages) must not silently change to
  include malformed/parse-dropped or DLQ'd messages — `LiveAnomalyWorker._run_loop`'s `processed_any`
  branch depends on this return value's existing semantics even though that file is not touched by this
  ticket.
- Re-verify the highest `INFRA-*` ID in `infrastructure.yaml` immediately before appending in Step 5 —
  `INFRA-358` was the highest confirmed at plan-writing time, not a guaranteed-still-current value.

## Deviations

- **Step 4 pseudocode gap (flagged in advance by architecture review, resolved during
  implementation, not silent):** the pseudocode above partitions `pending` into `retry_ids =
  [e["message_id"] for e in pending if ...]` and `exhausted_ids = [e["message_id"] for e in
  pending if ...]` — bare ID lists — then calls `self._send_to_dlq(msg_id, entries[0][1], "max
  delivery attempts exceeded", delivery_count)` for an exhausted entry, but `delivery_count` is
  never defined anywhere in that flow once only IDs are carried forward. Implemented instead by
  partitioning `pending` into `retry_entries`/`exhausted_entries` — the **full pending-entry
  dicts** `xpending_range` returns (each already containing `times_delivered`) — rather than just
  their `message_id`s. `retry_ids` (bare IDs, as `xclaim`'s `message_ids` parameter requires) is
  then derived from `retry_entries` only at the point `xclaim` is called. For the exhausted
  branch, `entry["times_delivered"]` is passed directly to `_send_to_dlq` as `delivery_count` —
  it was already in hand from the same `xpending_range` response that decided the entry was
  exhausted, so no re-lookup against Redis is needed. This is a strictly more-information-carrying
  version of the same partition the plan specifies (same two output sets, same strict `</>=`
  `MAX_DELIVERY_ATTEMPTS` boundary, same `xclaim`/`xrange`/`_send_to_dlq`/`xack` call shape) — no
  behavior described elsewhere in Step 4 changes.
- No other deviations from the plan's six steps, decisions, or scope guards.
