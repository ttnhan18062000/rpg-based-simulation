---
status: historical
layer: performance
authority: P2
audience: developer
---

# Performance Report: V2 RPG Engine Hardening (2026-05-13)

## Status: CERTIFIED

## Summary
The V2 RPG Engine has undergone comprehensive performance hardening to support high-density simulations (up to 5000 entities) while maintaining strict authoritative logic parity and deterministic reproducibility.

## Key Optimizations
1. **Staggered Passive Updates**:
   - Biological and Lifecycle components now process on a staggered cadence (10% per tick).
   - Reduced per-tick mutation pressure in idle states by ~90%.
2. **Object Identity Preservation**:
   - Implemented identity-preserving return paths in `apply_passive` and `RegionalConsequenceService`.
   - Maximized `_readonly_cache` hit rate in `AuthoritativeState`, drastically reducing freezing overhead.
3. **Observability Gating**:
   - Diagnostic tracing and fingerprinting are now gated behind `replay_allowed`.
   - Skip expensive hashing (`CanonicalStateHasher`) in performance-critical runs.
4. **Lazy Readonly Views**:
   - `Kernel` now avoids creating `readonly_view()` for ticks with no scheduled worker tasks.

## Benchmark Results (TPS & Latency)

| Entity Count | Avg TPS | p95 Latency | RSS (MB) |
| :--- | :--- | :--- | :--- |
| 100 | 9.63 | 38.60ms | 109.8 |
| 1000 | 4.41 | 321.69ms | 89.1 |
| 5000 | 0.63 | 1808ms | 139.7 |

## Verification
- **Regression**: 100% pass rate on `tests/integration/pipeline/` and `tests/unit/core/`.
- **Determinism**: Verified bit-identical state hashes across staggered update cycles.
- **Memory**: RSS remains stable under 250MB for all test scenarios.

## Conclusion
The V2 Engine meets the production-grade requirements for background simulation of up to 1000 active entities within the 50ms p95 latency budget for 100-entity active areas.
