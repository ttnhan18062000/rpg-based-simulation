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
