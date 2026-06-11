---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260417-ARENA-PERF-HARDENING
artifact_type: test_plan
tags: [arena, perf, hardening]
---

# Arena Performance Hardening Test Plan

## Objectives
- Verify that memory leaks are resolved (RSS stability).
- Verify that snapshot overhead is reduced (CPU efficiency).
- Verify that simulation determinism is maintained.

## Automated Verification

### 1. Contract Tests
Run the main arena contract test:
```bash
pytest tests/arena/test_arena_harness_contract.py
```
- Expect: PASS.
- Expect: No "Resource Exhaustion" failures in `conftest.py`.

### 2. Resource Delta Logging
Temporarily enable verbose logging in `ArenaRunner` to observe RSS deltas:
- Verify delta < 10MB per iteration for the `Determinism Test` (3 iterations).

### 3. Snapshot Profiling (Manual)
Verify cell size alignment:
- Change `Snapshot._SPATIAL_CELL` to 8.
- Verify that `Snapshot.from_world` does NOT fall back to rebuilding the index.

## Manual Verification
- Execute `test_arena_structural_determinism` with 5 iterations to stress test the memory boundary.
