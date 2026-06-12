---
status: active
layer: engine
authority: P1
audience: developer
---

# Minimal Deterministic Kernel (M2) — Execution Specs

## 1. Purpose
This document defines the executable semantics for Milestone 2. It specifies how the single-thread kernel orchestrates ticks, manages time, and ensures deterministic state transitions.

## 2. Minimal Kernel Scope
- **Single-Threaded**: All authoritative changes occur sequentially in one process.
- **Generation-Based**: `AuthoritativeState` is immutable; every tick produces a new state generation.
- **Deterministic**: Same seed + Same inputs => Same hash.

## 3. Tick Execution Path (The Sequence)
Exactly one tick entry point exists: `Kernel.tick_once()`.
It executes the frozen phase order:
1. `INIT`: Advance `world_time` by 1.
2. `SCHEDULING`: Filter entities where `readiness >= Threshold`.
3. `COLLECTION`: (Skeletal) Gather `StateUpdate` records.
4. `RESOLUTION`: Apply updates to the state using the generation-based `ApplyPath`.
5. `CLEANUP`: Finalize the new state generation.
6. `ADVANCEMENT`: Increment `world_tick`.
7. `PERSISTENCE`: (Non-Authoritative) Checkpoint the hash.

## 4. World-Time Progression Semantics
- **Autonomy**: `world_time` advances every tick regardless of entity activity.
- **Quiet Ticks**: Ticks with zero ready entities are valid and must advance `world_time` and `world_tick` deterministically.

## 5. Readiness-Gated Action Semantics
- **Readiness Accumulation**: Entities gain readiness based on their `readiness_speed` (passive).
- **Eligibility Threshold**: Entities are only eligible to submit updates if `readiness >= 100.0`.
- **Consumption**: Upon submission/resolution, readiness is reset or decremented.

## 6. Authoritative Apply-Path Semantics
- **Singular Path**: All mutation must flow through `apply.py`.
- **Generation Logic**: `prior_state + sorted_updates => next_state`.
- **Explicit Ordering**: Updates must be sorted by `entity_id` before application to ensure deterministic outcomes.

## 7. Deterministic RNG Usage
- Randomness is consumed only through the `DeterministicRNG` established in M1.
- Consumers must not leak randomness through unordered iteration.

## 8. Stable Checkpoint Semantics
- **Canonicalization**: The `CanonicalStateHasher` sorts all keys and excludes non-authoritative data.
- **Isolation**: Checkpointing logic resides entirely outside the core state models.
- **Stability**: Sequential runs with identical inputs produce identical SHA256 hashes.

## 9. Non-Goals (M2)
- Replay system or persistence.
- Concurrency or worker dispatch.
- Resource governor or adaptive degradation.
- Scheduler optimization.
