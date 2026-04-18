# Investigation: Resource-Safe Engine Milestone 1

## Core Objectives
Establish the "Laws of Simulation" and the "Resource Envelope" boundaries in a clean, isolated environment.

## Current State Observations
- The legacy `src/engine` is heavily contaminated with observational logic (replay, telemetry) mixed into the execution path.
- Snapshotting is expensive because authoritative and derived state are not structurally separated.
- Resource limits are advisory or implicit, leading to instability in long-running simulations.

## Strategic Decisions
1. **Structural Separation**: Use `src_v2/` as the root. This is the single most important decision to ensure a clean break.
2. **Authoritative State Definition**: Defined strictly as data required to determine future simulation outcomes. Derived state (e.g., stats for UI, replay logs) will be kept in separate structs.
3. **Pydantic vs Dataclasses**:
   - `Pydantic`: Best for configuration and runtime profile validation due to its expressive schema definition.
   - `Dataclasses`: Best for hot-path authoritative state due to low overhead (using `__slots__` where possible).

## Technical Risks
- **Dependency Leakage**: Accidental imports from legacy code.
- **Solution**: Use `ruff` or a custom script to enforce no imports from `src/` to `src_v2/`.
- **RNG Determinism**: Python's `random` or `numpy` can be tricky with thread safety and ambient state.
- **Solution**: Create a rigid `DeterministicRNG` wrapper in `src_v2/platform/rng.py`.

## Success Criteria (Operational)
- Rejection of invalid resource profiles.
- Bit-identical state checkpoints for the same seed/input.
- Structural exclusion of non-authoritative data from kernel models.
