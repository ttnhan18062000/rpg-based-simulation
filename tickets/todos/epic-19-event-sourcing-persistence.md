# epic-19: Kafka Event-Sourcing Persistence

**Status**: ✅ Completed (infra-08 / epic-19)

## Epic Summary
Implement durable, long-term world persistence using an Event-Sourcing architecture backed by Apache Kafka. Allows infinite rewinds, crash recovery, and ML data pipelines.

## Rationale
Epic-17 demands worlds running continuously for months ("Long-Story Progression"). An in-memory engine that completely resets if the server restarts is unacceptable. We need robust durability without compromising our strict deterministic tick-loop. Replacing PostgreSQL with Apache Kafka gives us an append-only distributed log perfectly suited for deterministic event-sourcing and message playback at scale.

## Scope & Affected Systems
This epic introduces Kafka into the simulation as the source of truth for the world timeline.

- **Target Files**: `src/api/kafka_client.py` (new), `src/engine/world_loop.py`, `src/core/snapshot.py`.
- [x] **Phase A: The Event Log (Tick Publisher)** 
  - [x] Record the `initial_seed` and every single tick's state-delta directly to a Kafka topic (`sim.events`).
- [x] **Phase B: Milestone Snapshots (State Compaction)** 
  - [x] Periodically (e.g., every 1,000 ticks), asynchronously serialize the immutable `Snapshot` (via MessagePack/Pickle) to a compacted Kafka topic (`sim.snapshots`).
- [x] **Phase C: Replay & Recovery (Consumer)** 
  - [x] On engine server start/recovery, consume the latest valid snapshot from `sim.snapshots`.
  - [x] Rehydrate the engine state.
  - [x] Seek the `sim.events` topic to the snapshot's offset and quickly replay the remaining state deltas to catch up to the crash point.

## Tech Stack
- Apache Kafka
- `confluent-kafka` or `aiokafka` (Python client)
- Docker Compose (Kafka + Zookeeper/Kraft)

## Dependencies
- Precursor feature to **epic-17** Phase 2 (World Evolution). Demands that determinism is strictly maintained.
