---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [resource, persistence, m6]
---

# Replay and Bounded Persistence Contract (Milestone 6)

## Purpose
The Replay System provides a non-authoritative stream of simulation events for diagnostics and forensics. It must operate within strict resource boundaries to ensure that persistence overhead never destabilizes the simulation.

## Replay Scope
- **Non-Authoritative**: Replay is a secondary observer. Failure to persist replay data MUST NOT affect simulation integrity or world state.
- **Streaming Model**: Data is emitted incrementally. Whole-run in-memory accumulation is forbidden.
- **Ordered**: Replay events MUST match the authoritative execution order defined by the Kernel.

## Capture Semantics
- **Events**: Only declared `TraceEvent` objects are eligible for capture.
- **Markers**: Chunks should include periodic "Checkpoint Markers" (State summaries) to allow random access during playback.
- **Minimalism**: By default, only Entity Actions and Kernel Phase transitions are captured. Subsystem internal state is excluded unless explicitly requested by mode.

## Staging and Windowing
- **Bounded Staging**: The in-memory buffer (`ReplayBuffer`) has a hard-coded limit defined by the `RuntimeProfile` (`max_replay_buffer_kb`).
- **Non-Blocking**: Kernel emission is non-blocking. If the buffer is full, events are dropped according to the Waterfall Policy.

## Chunking and Rotation
- **Deterministic Rotation**: Chunks are rotated based on:
    1. Maximum Byte Size (e.g., 5MB).
    2. Maximum Tick Count (e.g., 100 ticks).
- **Immutability**: Once a chunk is closed and written, it is considered immutable.
- **Manifest**: Each run contains a `manifest.json` that tracks the sequence of chunks and the runtime configuration.

## Sink Pressure and Quota
- **Backpressure**: The Persistence Sink reports latency and storage status.
- **Degradation**: Under pressure, the Governor will downgrade replay richness or disable capture entirely.
- **Quota Enforcement**: If the disk budget is exceeded, the oldest chunks are rotated out or new writes are suppressed.

## Safety Guarantees
- **Simulation Protection**: Replay IO pressure will never cause a spike in `tick_compute_ms` beyond the contractually allowed budget.
- **Memory Safety**: The replay subsystem has a verifiable memory floor and ceiling.

## Non-Goals
- Real-time streaming to remote sinks (Milestone 10+).
- Human-readable file formats (Compact binary preferred).
- Replay-driven state restoration (Authoritative state restoration is separate).
