# epic-19: Event-Sourcing Persistence (Database Layer)

## Epic Summary
Implement durable, long-term world persistence using an Event-Sourcing-Lite architecture backed by PostgreSQL. 

## Rationale
Epic-17 demands worlds running continuously for months ("Long-Story Progression"). An in-memory engine that completely resets if the server restarts is unacceptable. We need robust durability without compromising our strict deterministic tick-loop or incurring heavy ORM overhead during action resolution.

## Scope
This epic brings a database into the simulation but isolates it from the real-time loop.

## Scope & Affected Systems
This epic brings a database into the simulation but isolates it from the real-time loop.

- **Target Files**: `src/api/app.py`, `src/engine/world_loop.py`, `src/core/snapshot.py`, new directory `src/db/`.
- **Phase A: The Command Log** 
  - Store the initial `world_seed` and record every single ordered deterministic input (API control commands, generated AI intents) to the database grouped by `tick`.
- **Phase B: Milestone Snapshots** 
  - Periodically (e.g., every 10,000 ticks), asynchronously dump a compressed binary serialization (or MessagePack) of the immutable `Snapshot` to DB or object storage.
- **Phase C: Replay & Recovery** 
  - On server start/crash-recovery, pull the latest valid snapshot.
  - Query the database for the subsequent `CommandLog` and deterministically "fast-forward" the `WorldLoop` (using `ReplayRecorder`/playback) to catch up to the crash point without waiting for realtime delays.

## Tech Stack
- PostgreSQL
- SQLAlchemy 2.0 (Async enabled)
- Alembic for migrations

## Dependencies
- Precursor feature to **epic-17** Phase 2 (World Evolution). Demands that determinism is strictly maintained.
- Precursor feature to **epic-17** Phase 2 (World Evolution).
