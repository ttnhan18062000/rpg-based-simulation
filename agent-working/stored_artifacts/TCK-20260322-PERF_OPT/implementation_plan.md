---
content_type: doc
status: historical
layer: performance
authority: P2
audience: agent
tags: [perf_opt]
---

# Performance Optimization for Sub-1.0 TPS Bottleneck

The simulation is currently experiencing severe performance degradation (approx. 0.4 TPS) with 100% CPU utilization. Investigation revealed that the `collect` phase (worker dispatch and result collection) consumes 96% of the tick time. See [ADR-005](file:///d:/Projects/rpg-based-simulation/docs/architecture/adr-005-performance-optimization.md) for full architectural rationale.

## Proposed Changes

### Core Serialization & Memory Optimization

#### [MODIFY] [grid.py](file:///d:/Projects/rpg-based-simulation/src/core/grid.py)
Convert `self._tiles` from a `list[Material]` to a `bytearray`. 
> [!TIP]
> This reduces pickling time from ~4ms to ~0.1ms and halves the serialized size.

#### [MODIFY] [models.py](file:///d:/Projects/rpg-based-simulation/src/core/models.py)
Update `Entity.copy()` to use `model_copy(deep=False)`.
> [!IMPORTANT]
> A full `deepcopy` is redundant because the `Snapshot` is pickled (effectively deep-copied) before being sent to workers. Removing `deep=True` slashes 300ms+ of per-tick overhead.

### Worker Communication Optimization

#### [MODIFY] [worker_pool.py](file:///d:/Projects/rpg-based-simulation/src/engine/worker_pool.py)
Implement **Task Batching**. Instead of sending N individual RabbitMQ messages (tasks) and receiving N results, the engine will:
1. Send a single `ai_batch_tasks` message containing all entity IDs for the tick.
2. The worker will process the batch and return a single `ai_batch_results` message.
3. Optimize the `basic_get` loop with a more adaptive sleep to prevent 100% CPU spin-waiting.

#### [MODIFY] [ai_worker_daemon.py](file:///d:/Projects/rpg-based-simulation/src/workers/ai_worker_daemon.py)
Update the worker to handle batched task messages.

### AI Logic Optimization

#### [MODIFY] [perception.py](file:///d:/Projects/rpg-based-simulation/src/ai/perception.py)
Optimize `find_frontier_target`:
1. Reduce the `scan_radius` from 40 to 20 for non-hero entities.
2. Cache the frontier result on the entity to avoid re-scanning every tick if a valid target exists.

## Verification Plan

### Automated Benchmarks
1. Run `python bench_copy.py` and `python bench_grid.py` to verify low-level wins.
2. Run the simulation and check Prometheus metrics:
   - `SIM_TICK_DURATION{phase="collect"}` should drop below 100ms.
   - `SIM_TPS` should reach > 10.

### Manual Verification
1. Monitor `docker stats` to ensure `backend` CPU drops significantly below 100%.
2. Verify AI behavior (heroes exploring, combat) still works as expected with batched updates.
