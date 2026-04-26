# Authoritative Export Contract

This document defines the requirements for exporting the engine's authoritative state and transitions (TraceEvents).

## 1. Overview
The export shape is the "public face" of the authoritative truth. It must be structured, deterministic, and sufficient to recreate or verify any simulation tick.

## 2. Trace Event Shape (REFINED_UPDATE)
Every tick must emit a `REFINED_UPDATE` event with the following payload structure:

```json
{
  "tick": 100,
  "world_time": 1000,
  "seed": 42,
  "update": {
    "entity_updates": { ... },
    "work_debt_updates": { ... },
    "world_updates": { ... }
  },
  "fingerprint": {
    "state_hash": "a1b2c3d4",
    "entity_count": 150,
    "resource_checksum": "f9e8d7"
  }
}
```

## 3. The State Fingerprint
To move beyond simple hashing, the engine will use a **Multi-Domain Fingerprint**:
- **Identity Hash**: A hash of all entity IDs and their positions.
- **Resource Sum**: A checksum of all global and regional resource values.
- **Dynamics Vector**: A hash of all regional hazard and calamity intensity levels.

## 4. Integrity Constraints
- **Ordinal Stability**: All lists and dictionaries in the export must be sorted by a stable key (e.g., Entity ID, Region Name).
- **Redundancy**: The `refined_update` must contain ALL changes applied to the state, such that `apply(state_t, update) == state_t+1`.

## 5. Export Logic Location
- `src/core/state.py`: `AuthoritativeState.fingerprint()` (To be implemented).
- `src/engine/kernel.py`: Integration in `_phase_resolution`.

## 6. Verification
- `tests/replay/test_authoritative_export_shape.py`: Proof of shape consistency.
