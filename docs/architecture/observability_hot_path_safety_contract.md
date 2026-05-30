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
