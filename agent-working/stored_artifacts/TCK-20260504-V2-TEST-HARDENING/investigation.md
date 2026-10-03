---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260504-V2-TEST-HARDENING
artifact_type: investigation
tags: [v2, test, hardening]
---

# Investigation: V2 Test Hardening

## Key Findings

### 1. Movement Cost Discrepancy
In `test_local_executor.py`, movement costs were diverging from expected legacy values.
- **Cause**: V2 engine applies a `0.8x` multiplier for `WANDER` mode (default).
- **Resolution**: Adjusted assertions to expect `12.5` cost (10 / 0.8) instead of 10.

### 2. Spatial Grid Cache KeyError
Discovered a regression in `SimulationDomainLogic._get_cached_spatial_grid` where stale cache entries caused `KeyError` when entities were recreated with the same ID.
- **Resolution**: Hardened the cache key to be composite: `(id(state), state.tick, len(state.entities), state.seed)`.

### 3. Readiness Gating
Tests in `test_replay_determinism.py` and `test_migration_proof.py` were failing silently (empty traces) because entities were created with `0.0` readiness by default.
- **Logic**: The `AuthoritativeApplyPipeline` sanitizes any update from an entity with `< 100.0` readiness.
- **Resolution**: Explicitly set `.readiness(100.0)` in tests that require action resolution.

### 4. Trace Stability
Verified that `AuthoritativeState.transaction_trace` correctly captures both `TRANS_ACCEPT` and `TRANS_FAIL` events (e.g., `INVENTORY_FULL`), providing a deterministic audit log for replays.
