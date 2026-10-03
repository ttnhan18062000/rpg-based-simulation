---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [prod, hardening]
---

# TCK-20260515-PROD-HARDENING

## Title
Milestone 10: Production Tuning & Stress-Testing

## Status
INPROGRESS

## Request Summary
Harden the V2 Engine for production-grade workloads (10,000+ entities) and certify performance profiles.

## Scope
- Validate 10k entity stability.
- Tune GC behavior in the Kernel to smooth out latency spikes.
- Calibrate PROD_SMALL, PROD_DEFAULT, PROD_LARGE, and PROD_STRESS profiles.
- Final certification of performance contracts.

## Out of Scope
- Architectural refactors of the 17-phase apply sequence (reserved for Milestone 11).
- Persistence/DB layer optimizations.

## Acceptance Criteria
- [x] Engine stable at 10,000 entities with >2 FPS (500ms budget).
- [x] Engine sustains 10 FPS (100ms budget) at 5,000 entities with <10% dirty volatility.
- [x] Kernel implements incremental GC during frame-pacing windows.
- [x] Performance profiles (PROD_*) calibrated against measured p95/p99 data.
- [ ] BenchHarnessV2 certification run complete.

## Related Tickets
- None

## Related Docs
- `docs/engine/performance_contract.md`
- `docs/engine/kernel.md`

## Related Stored Artifacts
- `performance_hardening_plan.md`
- `performance_hardening_plan_milestones/performance_hardening_plan_milestone10.md`

## Related Code Areas
- `src/engine/kernel.py`
- `src/config/profiles.py`
- `src/engine/apply.py`

## Implementation Notes
- Initial measurements showed large P95 spikes (up to 400ms) due to GC behavior at 10k scale.
- Incremental GC (`gc.collect(0)`) added to `Kernel.tick_once` significantly improved average and P95 for 1k-5k scales.
- Profile budgets adjusted: PROD_LARGE (50ms -> 100ms), PROD_STRESS (250ms -> 500ms).

## Test Summary
- `scratch/measure_profiles.py` validated all 4 PROD profiles.

## Files Changed
- `src/engine/kernel.py`
- `src/config/profiles.py`

## Completion Summary
- [PENDING]
