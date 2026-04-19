# Milestone A: Core Runtime Completion Contract

This document defines the authoritative law for the deterministic single-process engine baseline.

## 1. Authoritative Phase Sequence
Every simulation tick MUST execute the following 6 phases in strict sequential order:

1. **INIT**: Execution context preparation and per-tick Governance (Policy setting).
2. **SCHEDULING**: Budgeted work selection based on the current Policy.
3. **COLLECTION**: Work-packet generation and concurrent dispatch.
4. **RESOLUTION**: Update aggregation and Authoritative State Apply (Generation +1).
5. **CLEANUP**: Internal metric finalization and lifecycle management.
6. **ADVANCEMENT**: Final signal recording and tick seal.

### Observational Boundary
Any logic not listed above (e.g., Persistence, Replay Emission, Telemetry) is **non-authoritative**. These must be executed as **post-tick hooks** and are strictly forbidden from modifying the `AuthoritativeState`.

## 2. Deterministic Checkpointing Law
The integrity of the simulation is verified via a `CanonicalStateHash`.

### Hashing Algorithm
1. The state is converted into a **Canonical Data Structure** (sorted dictionary).
2. The structure is serialized into a **compact JSON string** (no whitespace, sorted keys).
3. The string is hashed using **SHA-256**.

### Canonical Fields
Only the following fields are included in the hash:
- `tick`, `seed`, `world_time`
- `entities` (Sorted by ID, with sorted properties)
- `global_resources` (Sorted by Key)
- `periodic_due_ticks` (Sorted by Key)
- `work_debt` (Sorted by Key)
- `rng_checkpoint`

## 3. Authoritative Apply Path
State transitions are immutable. `ApplyPath.apply_generation` is the singular entry point for state mutation. 
- All collections MUST be sorted before application.
- No direct mutation of the `AuthoritativeState` instance is permitted inside the kernel loop.
