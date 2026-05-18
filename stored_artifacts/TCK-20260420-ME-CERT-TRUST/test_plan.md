# Test Plan - Milestone E Certification Hardening

## Scenario Matrix Verification
- [x] Baseline scenarios (IDLE_CLEAN, DET_EQUIV)
- [x] Pressure scenarios (RAM, TICK, QUEUE, DEBT)
- [x] Recovery scenarios (DEGRADED_NORMAL, SURVIVAL_NORMAL)
- [x] Equivalence scenarios (LOCAL_CONCURRENT_EQUIV)
- [x] Lifecycle scenarios (STARTUP, SHUTDOWN, REPLAY)

## Release Gate Verification
- [x] Test `test_final_gate.py` against all generated bundles.
- [x] Verify SHA provenance matching.
- [x] Verify hardware class targets.
