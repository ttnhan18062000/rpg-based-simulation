# TCK-20260402-VALIDATION: Post-Hardening Validation & Performance Benchmarking

## Status: DONE

## Goal
Validate the stability, deterministic integrity, and performance characteristics of the hardened AOA engine.

## Scope
1.  **Full Regression**: Execute the 700+ test suite and resolve any latent regressions.
2.  **Performance Benchmarking**: Profile the simulation loop (specifically `_validate_before` and property shims) under high density (100+ entities).
3.  **Legacy Cleanup**: Deprecate and remove the `Stats` dataclass from `src/core/entities/entity.py`.
4.  **Final Documentation**: Update architecture docs to reflect the new hardened boundaries.

## Acceptance Criteria
- [x] 100% test pass rate for all collected tests (excluding environment-blocked ones).
- [x] Profiling report shows < 1ms overhead for property shim access in simulation hot-loops.
- [x] `Stats` dataclass removed from `entity.py` without breaking external fixtures.

## Related Tickets
- TCK-20260402-HARDENING

**Tier:** standard
**Type:** chore
**Priority:** P1
