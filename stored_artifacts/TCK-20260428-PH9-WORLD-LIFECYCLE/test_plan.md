# Phase 9 Test Plan

## Automated Tests
- `tests/engine/test_phase9_stability.py`: 1000-tick run.
    - Assert monster count > 0 in all major regions.
    - Assert resource node count > 0.
    - Assert trauma scores decay over time if no combat happens.
