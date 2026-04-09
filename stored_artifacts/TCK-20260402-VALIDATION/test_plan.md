# Test Plan: TCK-20260402-VALIDATION

## Automated Tests

### 1. High-Density Benchmarking
*   `python3 scripts/profile_simulation.py --ticks 1000 --entities 100 --seed 42`
*   Compare result with `docs/performance-report-epic16.md`.

### 2. Full Regression
*   `pytest tests/ -v -n auto` (if xdist is installed) or `pytest tests/ -v`.
*   Focus on AI, Combat, and Persistence suites.

### 3. Determinism Check
*   `pytest tests/integration/test_determinism.py`
*   `pytest tests/integration/test_chaos.py`

## Manual Verification
*   Verify that `Stats` can be removed from `entity.py` without breaking snapshots.
