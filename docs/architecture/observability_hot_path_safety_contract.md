---
status: active
layer: architecture
authority: P1
audience: developer
---

# Observability Hot-Path Safety Contract

This contract establishes strict rules governing code execution inside the simulation loop (the "hot path"). Developers and automated static analysis tools must enforce this contract to prevent observability from causing unacceptable CPU/memory overhead or breaking engine determinism.

---

## 1. Hot Path Definition

The **simulation hot path** refers to any code executing inside or directly called by:
- The main engine tick loop (`Engine.tick()`)
- Any simulation phases (Combat, Movement, Econ, Progression, etc.)
- Entities during their tick update cycle

---

## 2. Allowed Operations in the Hot Path

The following operations are guaranteed to be cheap and are **allowed** inside the hot path:

* **Phase/System Timing**: Invoking cheap nanosecond clock checks at start/end of phases (e.g. `time.perf_counter_ns()`).
* **Raw Event Emission**: Creating lightweight event envelopes (e.g., `SimulationEvent` or `ObservabilityEventEnvelope`) containing primitive/small fields (IDs, types, categories, tiny payloads).
* **Counter/Metric Increments**: Standard thread-safe counter increments (e.g., in-memory integers, lightweight ring buffers).
* **Non-Blocking Queue Appends**: Pushing envelopes into bounded, non-blocking lock-free or ring-buffered queues.
* **Bounded In-Memory Timeline Appends**: Appending events to pre-allocated or strictly size-bounded deques (e.g., max 100 elements) per active entity.
* **Critical Hard-Law Recording**: Low-overhead execution of critical hard-law monitoring rules.

---

## 3. Forbidden Operations in the Hot Path

The following operations are highly resource-intensive or blocking, and are **absolutely forbidden** inside the hot path. They must be executed solely in async workers or post-run analysis phases:

* **Heavy Analytics**:
  - Behavior episode detection
  - Behavior pattern mining or cohort analysis
  - Run comparisons or insight generation
  - Entity behavioral scorecard generation
* **Serialization & Disk I/O**:
  - Direct JSON/YAML/Pickle file writes
  - Log serialization of large tables or complete states
* **Network & Database Operations**:
  - Direct relational/NoSQL database inserts (e.g., SQL, ClickHouse, Redis)
  - Synchronous web dashboard updates or HTTP POST requests
* **Large-Scale Memory Allocations**:
  - Full deep-copies (`copy.deepcopy`) of major components, the engine, or the entire world state
  - Global entity scans or full-world traversals for the sole purpose of monitoring
* **Blocking & Network Calls**:
  - Thread sleeps, locks holding main simulation phases, or waiting on external processes/workers

---

## 4. Isolation and Import Rules

To ensure compile-time and import-time separation:
1. **Zero Imports of Heavy Analyzers in Hot Path**: Hot-path modules (such as `src/engine/` or core `src/observability/` event dispatchers) must never import analytical modules (e.g., `src/observability/anomaly/`, `src/observability/cognition/`, or `src/observability/reporting/`).
2. **Graceful Degradation**: If downstream observability consumers (Redis, workers) crash or saturate the bounded queue, the queue must drop new events gracefully instead of blocking the main thread.

---

## 5. Dynamic Observability Mode (OBS-BACKPRESSURE, INFRA-199)

`EventRecorder` supports four dynamic modes driven by queue fill ratio:

| Mode | Fill ratio | Behavior |
|------|-----------|----------|
| `NORMAL` | < 70% | All events recorded as-is |
| `PRESSURE` | 70–90% | INFO/DEBUG sampled at 1-in-5; WARNING+ always pass |
| `DEGRADED` | 90–100% | INFO/DEBUG dropped entirely; WARNING+ pass |
| `SURVIVAL` | ≥ 100% | Counter-only path — no queue push, no buffer append |

`ObservabilityController.evaluate(queue_fill_ratio)` is a pure function that returns the recommended mode. Mode is evaluated on every `record()` call. Transitions are logged once at INFO level.

**SURVIVAL mode** is explicitly designed to comply with §2: only `dict.get()` + dict assignment — zero IO, no locks, no allocations beyond the dict entry. This is the hot-path ceiling; no IO or lock contention is ever introduced.

**DEGRADED batching**: INFO events are dropped before queue push; file writes continue to happen in the async `QueueDrainWorker` (off hot-path), satisfying §3.

**Accessors**: `observability_status() -> dict` (mode, queue_fill_ratio, events_dropped, survival_counts); `reset_mode()` for test cleanup.

The HTTP layer (`src/api/admission_control.py`) is now also a consumer of this vocabulary and of `ObservabilityController`'s pure `evaluate()` function, extending it to per-client HTTP admission control (`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`, `INFRA-378`). It does so via a **separate instance** (`_controller = ObservabilityController()`), never `EventRecorder`'s own singleton, so this contract's hot-path rules (§1-§4) continue to apply only to the engine's own `EventRecorder` usage and do not newly constrain the HTTP layer's own (non-hot-path) usage. See `docs/architecture/http_admission_control.md` for the full design.

---

## 6. Worker Lifecycle Contract

`QueueDrainWorker` is the background thread that drains the bounded observability queue to disk/downstream consumers. Its lifecycle is governed by these rules:

**Singleton guarantee**: Only one `QueueDrainWorker` may drain the module-level `_global_queue` at a time. Use `get_or_start_global_worker(queue)` (in `src/observability/queue.py`) to obtain or reuse the running global worker. Never call `QueueDrainWorker.start()` directly on the global queue — doing so bypasses the guard and creates a second concurrent drain loop.

**Per-instance queues**: `EventRecorder` uses its own private `BoundedObservabilityQueue`, not the global queue. Its worker is created and owned by the recorder instance. Callers must invoke `EventRecorder.shutdown()` (or `Kernel.shutdown()`, which calls it transitively) to stop the worker and drain remaining events before the instance is discarded.

**Test teardown rule**: Any test that constructs a `Kernel` or `EventRecorder` must call `.shutdown()` in teardown — either in a `try/finally` block or in a `yield`-fixture cleanup block. The session-scoped conftest sentinel (`_observability_worker_thread_sentinel` in `tests/conftest.py`) will fail the test suite if worker thread count grows across the session, catching regressions automatically.

**Relevant code**:
- `src/observability/queue.py` — `get_or_start_global_worker()`, `get_active_global_worker_count()`
- `src/observability/event_recorder.py` — `EventRecorder.shutdown()`
- `src/engine/kernel.py` — `Kernel.shutdown()` (calls `EventRecorder.shutdown()` transitively)
- `tests/conftest.py` — `_observability_worker_thread_sentinel` (CI regression guard)
- `tests/tools/memory_probe.py` — `count_drain_workers()`, `snapshot_start/end` (diagnostic helpers)

---

## 7. Consumer-Side Resilience (DLQ, PEL Reclaim, Reconnect Backoff)

`RedisStreamConsumer` (`src/observability/stream/consumer.py`) runs exclusively on
dedicated background threads (`LiveAnomalyWorker`, `BrokerQualityFeed`) — never inside
`Engine.tick()` or a phase — so this section's sleep-based backoff and bounded-retry
logic is contract-compliant with §3's hot-path prohibition on thread sleeps. It is this
section's own "graceful degradation, drop over block" instance of §4.2's transferable
principle: the consumer gives up on an unrecoverable message and DLQs it rather than
blocking or looping indefinitely.

**Failure-handling modes**:

| Failure | Handling |
|---|---|
| Malformed payload (missing/unparseable `payload`, or invalid `SimulationEvent`) | ACK + drop immediately — unchanged, never retried. |
| Handler raises an exception | Left un-ACKed (stays in the consumer group's PEL) for reclaim, up to `MAX_DELIVERY_ATTEMPTS = 3` total delivery attempts (first delivery + reclaim retries), then routed to the DLQ stream and ACKed off the source stream. |
| Process dies after a successful handler call but before ACK | Message stays in the PEL; a later reclaim sweep (by this or another live consumer in the same group) claims and redelivers it via `XCLAIM`. |
| Redis connection failure (`connect()`) | Reconnect attempts back off with jitter, capped, reset after a successful connect. |

**DLQ stream convention**: a derived name, `f"{stream_name}:dlq"` — a second Redis
Stream, not a new broker or message queue technology. Written via
`xadd(dlq_stream_name, fields, maxlen=1000, approximate=True)`, mirroring
`RedisStreamAdapter`'s existing `maxlen`/`approximate` retention pattern
(`src/observability/stream/adapters.py`). DLQ entries carry the original stream fields
plus `dlq_reason`, `dlq_source_id`, `dlq_delivery_count`, and `dlq_failed_at`. The name
and retention cap are literal constants, not `ObservabilityConfig`-tunable — this is a
fixed internal convention, not an operator-facing knob.

**Bounded retry via `XPENDING`, not an in-process counter**: `_reclaim_pending()` reads
each pending entry's `times_delivered` from `XPENDING`'s detail response
(`RECLAIM_IDLE_MS = 30000` idle floor, comfortably above both callers' `block_ms`
so an in-flight, still-processing message on a live-but-slow consumer is never mistaken
for orphaned). Entries with `times_delivered < MAX_DELIVERY_ATTEMPTS` are claimed via
`XCLAIM` and retried through the same `_handle_message` path used for freshly-read
messages; entries at `times_delivered >= MAX_DELIVERY_ATTEMPTS` are routed to the DLQ
and ACKed. Redis's own delivery counter (not an in-memory dict) is authoritative here
because a reclaim can be performed by a different `RedisStreamConsumer` instance,
possibly in a different process, than the one that first read the message — an
in-process counter would not be visible to that peer.

**Reconnect backoff**: `connect()` sleeps `_compute_backoff_delay(attempt)` before any
attempt after the first consecutive failure — `BACKOFF_BASE_SECONDS = 0.2`, doubling
per attempt, capped at `BACKOFF_CAP_SECONDS = 30.0`, with `±20%` jitter
(`BACKOFF_JITTER_RATIO = 0.2`). The failure counter resets to zero on a successful
connect. The very first attempt (or the first after a reset) never sleeps, so
`BrokerQualityFeed.start()`'s "return promptly with `health=unavailable`" contract is
preserved — it calls `connect()` once and never loops itself.

**Relevant code**: `src/observability/stream/consumer.py` —
`RedisStreamConsumer._handle_message`, `RedisStreamConsumer._send_to_dlq`,
`RedisStreamConsumer._reclaim_pending`, `RedisStreamConsumer.connect`,
`RedisStreamConsumer._compute_backoff_delay`.
