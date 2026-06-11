---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260515-PROD-HARDENING
artifact_type: plan
tags: [prod, hardening]
---

# Implementation Plan: Milestone 10 Production Hardening

## Goal
Finalize the hardening of the V2 Engine for 10k entity production workloads.

## Proposed Changes

### 1. Kernel Optimization
- [x] Integrate `gc.collect(0)` into `Kernel.tick_once`.
- [x] Use frame-pacing idle time for shallow GC to minimize latency spikes.

### 2. Profile Calibration
- [x] Adjust `PROD_LARGE` to 100ms budget (10 FPS).
- [x] Adjust `PROD_STRESS` to 500ms budget (2 FPS).

### 3. Final Certification
- [ ] Run `tests/perf/test_stress_10k.py` to confirm stability over 1,000 ticks.
- [ ] run `BenchHarnessV2` against all PROD profiles.

## Verification Plan
- `scratch/measure_profiles.py` must report PASS for all profiles.
- `src/config/validator.py` must pass on updated profiles.
