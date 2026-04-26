# Substrate Truth Standard

This document defines the authoritative truth levels and verification standards for the `src` substrate closure (Phase 7).

## Truth Levels

| Level | Name | Enforcement Requirement | Typical Use Cases |
| :--- | :--- | :--- | :--- |
| **Level 1** | **Bit-Identical** | Every bit of the resulting state or stream must match the reference/legacy output exactly. | World Gen, Replay Reconstruction, Conflict Resolution outcomes. |
| **Level 2** | **Structural Integrity** | The shape and data invariants of the state must be identical, even if internal memory addresses or non-semantic metadata differ. | Snapshots, Serialization, Entity State composition. |
| **Level 3** | **Contract Safety** | Behavior must satisfy defined formal contracts and invariants, allowing for semantic improvements or intentional divergence from legacy. | Regional Hazards, Calamity Scaling, Social Betrayal logic. |

## Verification Protocols

### CERTIFICATION Proof
- Requires a `data/runs/` manifest certifying 100% pass rate on bit-identical or structural-parity test suites.
- Must be reproducible on the **Class B (Standard)** hardware profile.

### CONTRACT Proof
- Requires formal verification of boundary conditions, invariant clamping, and state purity.
- Must include "Mutation Tripwire" tests to ensure no hidden leaks.

### DIFFERENTIAL Proof
- Requires a side-by-side comparison between legacy `src` and `src` using the **Parity Oracle**.
- Divergences must be explicitly logged in the [Divergence Log](divergence_log.md).

## Substrate Invariants (The "Golden Rules")

1. **Pure Decision**: AI/Worker logic must never mutate world state during the decision phase.
2. **Atomic Apply**: Updates must be applied atomically per domain.
3. **Deterministic Seed**: Given the same seed and tick number, the engine must produce the same authoritative update bucket.
