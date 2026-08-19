---
status: active
layer: architecture
authority: P1
audience: developer
---

# Simulation Performance Optimization

## Status
Superseded (historical) for the RabbitMQ-specific mechanism (AI Task Batching, item 3 under
Decision below). RabbitMQ/Kafka were removed entirely from this repo by
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`; this ADR's other decisions (shallow-copy snapshots, grid
compression, frontier-scan optimization) remain valid and were separately implemented. This
document remains a valid historical record of a V1-era optimization design.

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
