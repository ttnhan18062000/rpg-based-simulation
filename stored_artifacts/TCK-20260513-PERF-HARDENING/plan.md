# Performance Hardening Plan

## Goal
Optimize V2 RPG Engine to support high-density simulations by reducing tick latency and memory churn.

## Proposed Changes
1. **ApplyPath.apply_passive**:
   - Implement staggered biological/lifecycle updates.
   - Implement identity preservation for unchanged entities.
2. **Kernel**:
   - Gate diagnostic fingerprinting/tracing behind `no_replay` or `policy.replay_allowed`.
   - Lazy evaluate `readonly_view()` only when workers are scheduled.
3. **RegionalConsequenceService**:
   - Optimize recovery loop to preserve collection identity.

## Verification
- Run scaling benchmarks for 100, 1000, 5000 entities.
- Verify p95 latency targets (< 50ms for 100 entities).
- Run regression tests to ensure logic parity.
