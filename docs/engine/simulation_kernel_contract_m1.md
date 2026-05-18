# Simulation Kernel Contract — Milestone 1

## 1. Purpose
This contract defines the authoritative laws and deterministic semantics of the Resource-Safe Simulation Engine. It serves as the single source of truth for kernel behavior, state classification, and time progression.

## 2. Tick Semantics
- **Definition**: A "Tick" is the smallest indivisible unit of authoritative simulation time.
- **Tick Progression**: Advancement is explicit and occurs exactly once per world-loop iteration.
- **Independence**: Tick advancement is independent of non-authoritative systems (Replay, Observability, Metrics). A failure in a non-authoritative system must not block tick progression.

## 3. Authoritative State
- **Definition**: Minimum state required to determine **future simulation outcomes**.
- **Classification**:
    - **Authoritative**: Entities, Positions, Resources, Time/Tick, RNG State.
    - **Non-Authoritative**: Replay logs, UI/API event streams, telemetry, diagnostic traces.
- **Rule**: Non-authoritative data must never be read by authoritative logic.

## 4. Tick Phase Ordering (The Law)
Every tick must execute the following phases in this exact order:
1. `INIT`: Setup tick context and handle incoming system requests.
2. `SCHEDULING`: Identify entities ready to act based on eligibility timers.
3. `COLLECTION`: Gather action proposals from ready entities.
4. `RESOLUTION`: Validate proposals and apply state changes in deterministic order.
5. `CLEANUP`: Finalize state, remove expired entities, and perform lifecycle maintenance.
6. `ADVANCEMENT`: Increment the world tick count.
7. `PERSISTENCE`: (Non-Authoritative) Stream logs and record snapshots.

## 5. Action Readiness Semantics
- Entities are eligible to act only when their readiness threshold is met.
- Readiness is a property of continuous simulation time, but eligibility is checked only at phase boundaries.
- Empty ticks (where no entity is ready) are valid and must progress time deterministically.

## 6. Deterministic Apply Order
- Updates to authoritative state must be applied in a stable, deterministic order.
- **Tie-Breaking**: If multiple updates occur at the same tick, an explicit tie-break rule (e.g., Entity ID or deterministic priority) must be used.

## 7. Deterministic RNG Contract
- All simulation randomness must flow through a singular `DeterministicRNG` interface.
- No authoritative logic may use:
    - `time.time()`
    - `random.random()`
    - Ambient thread/process state.
    - Unordered collection iteration.

## 8. Determinism Guarantees
**Same Seed + Same Runtime Profile + Same Inputs => Bit-Identical Authoritative State Checkpoints.**

## 9. Kernel Boundaries
- No scheduler optimization.
- No concurrency or parallel execution.
- No adaptive degradation.
- No external event brokers.
