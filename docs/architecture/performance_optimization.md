---
status: active
layer: architecture
authority: P1
audience: developer
---

# Simulation Performance Optimization

## Status
**Historical (V1-era design record). Not a statement of current behavior.** Scope clarified under C-16
(`docs/architecture/performance_optimization_decisions.md`, applied by `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT`):

- **Decision 3 (AI Task Batching over RabbitMQ): superseded, historical.** RabbitMQ/Kafka were removed
  entirely from this repo by `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`. The removed transport design is
  not revived by this document.
- **Decisions 1, 2 and 4 (shallow-copy snapshots, grid compression, frontier-scan optimization): not
  verified as current.** An earlier version of this status said they "remain valid and were separately
  implemented". A search of `src/` on 2026-10-03 found no `model_copy(deep=False)`, no `Grid` class
  holding a `bytearray`, and no `find_frontier_target`; the entity type is now the `EntityState`
  dataclass (`src/core/state.py`), not a Pydantic `Entity`. They are kept below as the record of what
  was decided, not as live decisions. If the owner wants one of them confirmed as surviving, it needs
  its own check against the current code.
- **Current performance authority** is `docs/engine/performance_contract.md` (measurement and claims),
  `docs/engine/contracts/certification_contract.md` §3 (hardware classes), and the decision records in
  `docs/architecture/performance_optimization_decisions.md`.

## Context
The RPG simulation is currently throughput-bottlenecked at 0.45 TPS with 100% CPU on the backend. Profiling identified the `collect` phase (worker dispatch and result collection) as the primary bottleneck (2.1s per tick). 

Key issues:
1. **O(N) Serialization**: Pydantic `model_copy(deep=True)` takes 300ms+ for 200 entities.
2. **Sequential Messaging**: 188 individual RabbitMQ tasks/results per tick cause massive I/O wait and IPC overhead.
3. **Sequential Processing**: A single worker process processes tasks one-by-one, leading to a linear delay that blocks the engine.
4. **Grid Overhead**: Pickling a 262k-element list of Enum objects is CPU-intensive.

## Decision
We will implement a multi-layered optimization strategy:

1. **Shallow Copy for Snapshots**: Switch `Entity.copy()` to `model_copy(deep=False)`. Rely on `pickle` for the single deepcopy during serialization.
2. **Grid Compression**: Store `Grid` tiles as a `bytearray`. This reduces serialization time and size by >50%.
3. **AI Task Batching**: Group all ready entities into a single RabbitMQ message (`ai_batch_tasks`). The worker will process the entire batch and return a single `ai_batch_results`.
4. **Frontier Scan Optimization**: Reduce `Perception.find_frontier_target` scan radius and implement basic caching.

## Rationale
- **Batching** is the most significant architectural win, reducing 188 round-trips to 2 per tick.
- **Shallow Copying** removes the 300ms synchronous bottleneck on the engine thread.
- **Grid Compression** ensures that even larger maps (e.g., 1024x1024) remain performant over the wire.

## Trade-offs
- **Complexity**: Batching requires updating `WorkerPool`, `AIWorkerDaemon`, and error handling for failed batches.
- **Granularity**: We lose the ability to load-balance *individual* entities across workers within a single tick. However, scaling can still happen at the batch level (if multiple workers exist).

## Consequences
- **Positive**: Expected TPS increase from 0.4 to >10. Backend CPU usage will transition from spin-waiting to efficient I/O.
- **Negative**: "Everything or nothing" batch results mean a single worker crash loses all actions for that tick (Mitigation: Watchdog and retry logic).

## Revisit Trigger
- If population exceeds 5,000 entities, the batch message size may exceed RabbitMQ's efficient throughput, requiring sub-batching.
- **Superseded note (`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`):** `pika`/`confluent-kafka` were
  removed from `pyproject.toml` entirely; this trigger's premise (RabbitMQ throughput) no longer
  applies. Any future AI-task-batching work must be re-scoped against the current Redis-based
  pipeline (`RedisStreamConsumer`, `src/observability/stream/consumer.py`), not RabbitMQ.
