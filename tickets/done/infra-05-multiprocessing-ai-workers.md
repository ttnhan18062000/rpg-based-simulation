# infra-05: Distributed AI Workers (RabbitMQ)

## Objective
Bypass Python's Global Interpreter Lock (GIL) and scale horizontally by shifting heavy AI evaluations (A* Pathfinding, FOV calculations, Narrative Decision Trees) into a distributed **RabbitMQ** task queue. 

## Rationale
Threads (`ThreadPoolExecutor`) only provide true concurrency for I/O operations in Python. As scale expands to thousands of entities with complex narrative AI decisions (Epic-12), the engine will hit CPU-bound limits under the GIL, throttling the `Collect` phase of the `WorldLoop`. 

By distributing the workloads to independent Docker containers communicating over RabbitMQ, the engine can parallelize computationally expensive actions perfectly.

## Architecture
- **Distributed State Replica**: To prevent massive IPC serialization overhead from sending `WorldSnapshot` data over queues, each AI Worker container will use the `infra-07` Redis `sim:stream` to maintain a local, fully-synchronized replica of the simulation state.
- **Task Dispatch**: The `WorldLoop` uses `pika` (RabbitMQ client) to publish lightweight work payloads (`{"tick": N, "entity_id": X, "action": "decide"}`) to a RabbitMQ `ai_tasks` fanout/direct exchange.
- **Results Queue**: Workers compute `ActionProposal` results locally and push the serialized JSON back to an `ai_results` queue.
- **Wait & Collect**: The main `WorkerPool` drains the `ai_results` queue to collect all proposals before resolving the tick.

## Acceptance Criteria
- `pika` integrated into the backend and robust connections established to a RabbitMQ docker container.
- AI `Collect` phase processing time scales horizontally and reduces main thread CPU load.
- Main engine correctly awaits full AI turnaround per-tick.

**Tier:** standard
**Type:** chore
**Priority:** P1
