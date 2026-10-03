---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
artifact_type: investigation
tags: [observability]
---

# Investigation — TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC

## Current Behavior

**`RedisStreamConsumer`** (`src/observability/stream/consumer.py`, verified directly, 118 lines
total):

- `__init__` (lines 15-27): stores `redis_url`, `stream_name`, `group_name`, `consumer_name`;
  `client=None`, `_connected=False`. No retry/backoff state fields exist at all.
- `connect()` (lines 29-51): builds a `redis.from_url(...)` client (`socket_connect_timeout=2.0`,
  `socket_timeout=2.0`), pings, and `xgroup_create(..., id="0", mkstream=True)` (swallowing
  `BUSYGROUP`). On any exception, logs and sets `_connected=False`, returns `False`. **No sleep, no
  backoff, no jitter, no cooldown between attempts anywhere in this method** — every call is a
  fresh, unthrottled attempt.
- `read_and_process(handler, block_ms=1000)` (lines 53-108):
  - Lines 58-60: if not connected, calls `self.connect()`; if that also fails, **returns `0`
    immediately** — critically, this means a disconnected consumer does **not** block for
    `block_ms`, it returns instantly on failure.
  - Lines 65-71: `xreadgroup(groupname, consumername, streams={stream_name: ">"}, count=50,
    block=block_ms)`.
  - Lines 80-85: **malformed-payload path** — if `payload.get("payload")` is falsy, logs a warning
    and `xack`s immediately (`continue`). This path is already correct per the ticket's AC and is
    untouched scope.
  - Lines 87-94: `json.loads(raw_payload)` → `SimulationEvent(**event_dict)` → `handler(event)` →
    `xack(...)` on success.
  - Lines 96-102 (**the bug, confirmed at the exact lines the ticket/audit cite**): a single
    `except Exception as ex:` catches **everything** that can fail in lines 87-94 — JSON parse
    errors, `SimulationEvent` pydantic validation errors, *and* arbitrary exceptions raised by the
    caller-supplied `handler(event)` itself — and ACKs the message unconditionally in all three
    cases. There is no way today to distinguish "this payload will never parse" from "the handler
    hit a transient error and might succeed on retry." No dead-letter stream exists anywhere in the
    codebase (confirmed: repo-wide grep for `dead.letter|DLQ|dead_letter` across `src/` and
    `tests/` returns zero matches).
  - Lines 104-108: the **outer** `except Exception as e:` around the whole `xreadgroup` call (e.g.
    a connection drop mid-read) sets `_connected = False` and returns `0`. No backoff here either.
  - **No PEL reclaim logic exists.** Repo-wide grep for `xclaim|xpending|XCLAIM|XPENDING` across
    `src/` and `tests/` returns zero matches. If `handler(event)` succeeds (line 91) but the
    process dies before line 94's `xack()` runs, the message stays in the consumer group's PEL
    (pending-entries list) forever — `redis-py`'s `xpending_range()`/`xclaim()` primitives are
    available on the client already in use (`self.client`) but are never called.
- `close()` (lines 110-117): straightforward client teardown, no resilience-relevant logic.

**Where the "~100ms reconnect loop" the ticket/audit describe actually lives — important
correction to the ticket's framing.** `consumer.py` itself contains no loop and no sleep. The
retry cadence is entirely determined by whichever caller repeatedly invokes `read_and_process()`:

- `LiveAnomalyWorker._run_loop` (`src/observability/anomaly/worker.py:244-289`): calls
  `self.redis_consumer.read_and_process(self.process_event, block_ms=500)` each iteration; sleeps
  `time.sleep(0.1)` at the bottom (line 288) **only if nothing was processed this iteration**
  (`processed_any` is `False`). This is the actual source of the audit's "~100ms" figure.
- `BrokerQualityFeed._consume_loop` (`src/simulation_quality/feed.py:102-109`): calls
  `consumer.read_and_process(_callback, block_ms=500)` in a bare `while self._running:` loop with
  **no sleep at all**, on any outcome (success, zero-read, or exception). Because a disconnected
  `read_and_process()` returns `0` near-instantly (per the line 58-60 finding above, it does not
  honor `block_ms` when `connect()` fails), this path can busy-loop **faster than the audited
  ~100ms figure** during a sustained Redis outage — a real, slightly worse variant of the finding
  than what D23 documented for this specific caller.

**Consequence for implementation scope:** because neither caller loop can be relied upon to
provide pacing (one sleeps 100ms flat only on the empty-read branch, the other doesn't sleep at
all), a `connect()`/`read_and_process()`-internal backoff (tracking consecutive-failure count and
self-pacing before attempting the next network call) is the only design that fixes both call sites
without touching `worker.py`/`feed.py`, which are not in this ticket's `Related Code Areas`. This
is a design recommendation for Plan, not a settled decision — flagged as an open question below.

**`RedisStreamAdapter`** (`src/observability/stream/adapters.py`, verified directly — the
*publish* side, listed in Related Code Areas but not named in the ticket's own `## Scope`
bullets):
- `_connect()` (lines 132-153): same unthrottled-retry shape as `consumer.connect()` — no backoff.
  Called from `_send_to_redis()` (lines 169-171) whenever `_connected` is `False`, which runs
  inside the dedicated `_publish_worker()` daemon thread (lines 155-167) once per dequeued event.
  Under a sustained outage with a steady publish rate, this reconnect-attempts-per-event pattern
  is bounded by publish cadence rather than a tight loop, but it shares the exact same "no backoff
  primitive exists" gap as the consumer side.
- This class already has real, audited-as-good backpressure (severity-aware queue eviction,
  `health()` diagnostics, `flush()`/`close()`) — confirmed by D23 §E as "deliberately, correctly
  isolated, and matches its own written contract." Nothing here needs to change for this ticket's
  AC; it is listed as a Related Code Area most plausibly because it shares the connect-retry
  pattern a shared backoff helper could serve, not because its publish-side behavior is broken.

**Factory / config** (`src/observability/stream/factory.py`, `src/observability/config.py:318-341`
verified): `get_event_stream_adapter()` is a thread-safe singleton factory keyed off
`ObservabilityConfig.get_stream_backend()`. `ObservabilityConfig` already exposes
`get_redis_url()`, `get_stream_name()`, `get_max_queue_size()` — no existing accessor for a DLQ
stream name, retry-budget count, or backoff parameters; any new tunables this ticket introduces
need equivalent `SIM_*`/`RPG_*` env-var-backed accessors following the existing pattern (or literal
constants, per the ticket's own "literal DLQ stream" phrasing in Scope/AC — an open question, see
below).

**Callers confirmed via repo-wide grep** (`grep -rn "RedisStreamConsumer"`): exactly two
production call sites (`src/observability/anomaly/worker.py`, `src/simulation_quality/feed.py`),
both already covered above. No other module constructs a `RedisStreamConsumer`.

## Mechanics / Engine Constraints

This subsystem is **not** governed by the Mechanics Bible (no gameplay law applies — no
entity/economy/combat formula is touched). The relevant governing document is
`docs/architecture/observability_hot_path_safety_contract.md`.

- **Tier classification independently verified, not just trusted from the ticket:** `grep`
  confirms `RedisStreamConsumer` is only ever instantiated inside
  `LiveAnomalyWorker.start()`/`_run_loop` (its own dedicated daemon `threading.Thread`, per
  `worker.py:224-226`) and `BrokerQualityFeed.start()`/`_consume_loop` (its own dedicated daemon
  `threading.Thread`, per `feed.py:111`). Neither is called from `src/engine/`, `Kernel.tick_once`,
  or any phase module. The ticket's "Tier 3, downstream, not part of the authoritative gameplay
  pipeline" framing is **confirmed correct**.
- Because this code runs exclusively on dedicated background threads (never inside
  `Engine.tick()` or a phase), §3's hot-path prohibition on "Thread sleeps... holding main
  simulation phases" **does not apply** — a sleep-based backoff+jitter implementation here is
  contract-compliant. §4.2's "graceful degradation, drop over block" principle is the one
  transferable requirement: whatever backoff/retry-budget is added must still let the consumer
  give up and move on (or DLQ) rather than block indefinitely.
- No engine contract in `docs/engine/` (`kernel.md`, `authoritative_pipeline.md`,
  `authoritative_mutation_pipeline_contract.md`, `governance_logic.md`, `performance_contract.md`,
  `known_limitations.md`) mentions Redis Streams, DLQ, or this consumer at all — confirmed via
  directory listing of `docs/engine/` and `docs/engine/contracts/`. No existing contract to
  reconcile against; a new architectural convention is being introduced by this ticket, not an
  existing one being brought into compliance.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers this consumer's
  delivery-guarantee behavior (DLQ-on-exhaustion, PEL reclaim, reconnect backoff) — the nearest
  entries (INFRA-015/016/063/165) only cover "safe when Redis absent/optional," and INFRA-239
  only covers `BrokerQualityFeed` wiring, not failure semantics. New entries are required once the
  behavior is implemented (status `verified`, P1, with `test_path` populated — this is a
  P1-priority ticket so P0-mandatory passing-test-path isn't a hard gate, but new entries should
  still carry one per existing convention).
- `docs/architecture/observability_hot_path_safety_contract.md`: this is the doc-of-record for
  this exact subsystem's queue/degradation/backpressure semantics (§5 dynamic modes, §6 worker
  lifecycle) but currently documents only the *publish* side (`RedisStreamAdapter`/
  `EventRecorder`). It has no section describing consumer-side failure handling, DLQ semantics, or
  PEL reclaim — this is a brand-new behavior, not a modification of documented behavior, so per the
  "new features need a doc too" rule a new section here (mirroring §5/§6's structure) is the most
  natural home rather than inventing a new doc file.

None of `docs/mechanics/`, `docs/engine/`, or `docs/guidelines/intentional_divergences.md` apply —
confirmed above, no gameplay law or existing engine contract touches this code path, so this is
not a Mechanics Bible divergence.

Per the completed sibling ticket's precedent (`TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`, which
left `docs/audits/D23_architecture_resilience.md` and
`docs/plans/architecture_resilience_remediation_roadmap.md` untouched despite being the direct
source of its finding), `D23_architecture_resilience.md` and
`docs/plans/redis_stream_resilience_epic.md`/`architecture_resilience_remediation_roadmap.md` are
treated as static point-in-time records, not living documentation, and are **not** listed above.

## Parity Ledger Overlap

No existing entry directly covers this ticket's scope (DLQ, PEL reclaim, reconnect backoff) — new
entries are required, not updates to existing ones. Adjacent entries that overlap the same code
paths but are **not** modified by this ticket's scope, and should be re-verified as regression
guards:

| ID | Status | Priority | Text | test_path |
|---|---|---|---|---|
| INFRA-015 | verified | P0 | Redis client behavior remains safe when Redis package/runtime unavailable | (none) |
| INFRA-016 | verified | P0 | Redis accessors fail safely without crashing simulation bootstrap when Redis optional | (none) |
| INFRA-063 | verified | P0 | Missing Redis package does not crash safe initialization paths where optional | (none) |
| INFRA-165 | verified | P0 | Redis disabled/missing mode does not crash RPG core if optional | (none) |
| INFRA-239 | verified | P1 | `BrokerQualityFeed.start()` creates `RedisStreamConsumer`, wraps events, calls `hub.on_envelope()` from a daemon thread; skips gracefully when Redis unreachable | `tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable` |
| INFRA-317/318 | verified | P1/P0 | `BrokerQualityFeed`/`QualityWorker` config resolution and kernel broker-mode isolation | `tests/simulation_quality/test_feed.py`, `tests/simulation_quality/test_kernel_simq_integration.py` |

**Four P0 entries touch code this ticket modifies indirectly** (INFRA-015/016/063/165 all assert
"safe when Redis unavailable/missing" — a property the new backoff/DLQ logic must preserve, not
just avoid regressing). None of them have a `test_path` recorded in the ledger itself, but the
underlying behavior is exercised by `tests/unit/observability/test_event_stream_adapters.py` and
`tests/unit/observability/test_redis_stream_adapter.py` (see test_plan.md). None are P0-blocking
for *this* ticket since this ticket doesn't touch the "Redis package missing" code path directly,
but the new connect()-retry logic must not break the "missing redis package → degraded, no crash"
behavior these entries assert.

## Prior Work

- `stored_artifacts/TCK-20260702-OBSISO-BROKER-CONFIG/` — prior work on `BrokerQualityFeed`
  config resolution (`INFRA-317/318`); relevant because it's the same consumer construction path
  (`RedisStreamConsumer(...)` inside `BrokerQualityFeed.start()`) this ticket's backoff change will
  run through, but that ticket's scope was config-default resolution only, not failure handling.
- `tickets/done/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC.md` — direct sibling under the same
  parent epic (`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`), same D23 audit source, same
  epic→standard downgrade rationale on 2026-08-18. Useful precedent for structure: added a new
  `INFRA-358` parity entry (single new entry, validated against `schema.json` directly before
  appending), updated exactly the docs whose described behavior actually changed
  (`simulation_watchdog.md`, `api_protocol_contract.md`), and left the audit/roadmap docs
  untouched. This investigation follows the same pattern for "Docs Requiring Update" above.
  Current highest parity ledger ID in `infrastructure.yaml` is `INFRA-358` (re-verify immediately
  before appending at implementation time — do not assume it is still current).
- `tickets/done/TCK-20260817-DEAD-INFRA-REMOVAL-EPIC.md` — another sibling under the same parent
  epic (RabbitMQ/Kafka removal, R1 from the same D23 audit). Not code-adjacent to this ticket, but
  confirms the parent epic's overall pattern of downgrading each D23 sub-finding into its own
  standard-tier repair ticket.
- No prior ticket has implemented a Redis Stream DLQ, XCLAIM/XPENDING reclaim, or a
  backoff/jitter utility anywhere in this codebase (confirmed by the greps above) — this is
  genuinely new engineering, not a pattern to copy. The closest analog for a *retry with backoff*
  shape is `WebhookAlertSink._dispatch_with_retry` (`src/observability/alerts/sinks.py:61-92`,
  flagged by D23 R7 as "linear despite a comment claiming exponential, no jitter") — worth reading
  as a **counter-example** (bounded attempts in a dedicated executor is the right shape; the linear
  `time.sleep(0.5 * attempt)` with no jitter and the stale "exponential" comment are exactly the
  mistakes this ticket's AC ("backs off with jitter") should not repeat). Reusing or extracting a
  shared backoff/jitter helper between this ticket's fix and `WebhookAlertSink` is explicitly
  **out of scope** per the ticket's own "no generic retry framework" exclusion — but Plan should be
  aware the sibling bug (R7, P3 in the audit) exists so it isn't accidentally fixed as scope creep.

## Risks and Open Questions

- **Open question, blocks a design decision, not the investigation itself:** DLQ stream naming
  and retention convention is explicitly still open per the ticket's own Assumptions section. No
  existing convention exists anywhere in the codebase to infer it from (confirmed: no DLQ stream
  exists today). Plan must decide: literal fixed name (e.g. `f"{stream_name}:dlq"`) vs. a new
  `ObservabilityConfig` accessor, and whether `maxlen`/retention trimming applies (the existing
  `RedisStreamAdapter.xadd(..., maxlen=..., approximate=True)` pattern is the only retention
  precedent in the codebase).
- **Open question:** what counts as "bounded retry" before DLQ — a fixed attempt count (mirroring
  `WebhookAlertSink.max_retries=3`), or a redelivery-count read from the stream message's
  delivery metadata (`XPENDING` exposes a per-message delivery counter that could drive this more
  natively)? Both are defensible; Plan should pick one and state why.
- **Risk:** the two caller loops (`LiveAnomalyWorker`, `BrokerQualityFeed`) have different pacing
  behavior today (100ms floor vs. no floor at all). If backoff is implemented purely inside
  `connect()`/`read_and_process()` (recommended above), both callers inherit the fix uniformly
  without their own changes — but this must be verified against both call sites at test time, not
  assumed from one.
- **Risk:** `read_and_process()`'s malformed-payload branch (lines 80-85) and the generic except
  (lines 96-102) both currently do `xack` — any refactor separating "malformed" from "handler
  exception" must preserve the exact malformed-payload behavior unchanged per AC #2, while only
  changing the generic-except branch's *handler-raised* sub-case. A naive refactor risks
  accidentally changing JSON-parse-error or pydantic-validation-error handling (which today is
  correctly ack+drop, grouped with "malformed") into retry+DLQ handling, which would be a
  regression against AC #2, not a fix.
- **Risk, needs confirmation at implementation time:** does `redis-py`'s `xclaim()` signature (as
  vendored/available in this environment) match what the fix assumes (`min_idle_time`, message ID
  list, justify claim ownership)? Not verified in this pass — grep found zero existing usage
  anywhere in the codebase to cross-check the exact call signature/version compatibility against.

## Anti-Drift Hazards

- **Do not touch `worker.py`/`feed.py` caller loops** unless Plan explicitly decides the backoff
  must live there instead of in `consumer.py` — they are not in this ticket's `Related Code
  Areas`, and the ticket's own `## Scope` says "all in `src/observability/stream/consumer.py`."
- **Do not introduce a generic/reusable retry framework** or a circuit breaker — both explicitly
  out of scope (ticket's `## Out of Scope`, and D23 R7's `WebhookAlertSink` circuit-breaker gap is
  a separate, P3, un-ticketed finding — do not fix it here as a "nice to have while I'm in the
  area").
- **Do not change `RedisStreamAdapter`'s publish-side backpressure/eviction logic** — D23 already
  confirms it as correct and contract-compliant; the only reason `adapters.py` is a Related Code
  Area is the shared connect-retry pattern, not a bug in its severity-aware queue behavior.
- **Do not weaken the malformed-payload ack+drop path** while adding retry/DLQ for handler
  exceptions — see the Risks section above; this is the single easiest way to accidentally violate
  AC #2 while fixing AC #1.
- **Do not add RabbitMQ/Kafka or any new broker dependency** — D23 already flags those as
  dead/removed-track infrastructure (`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`); this ticket's DLQ
  must be a second Redis Stream, not a new broker.
- **Preserve the "never raise into the caller" contract** — every existing method in
  `consumer.py` degrades to logging + a safe return value rather than raising; the new
  backoff/DLQ/reclaim logic must follow the same never-throws-to-caller shape, consistent with
  `observability_hot_path_safety_contract.md` §4.2's graceful-degradation principle.
