# Test Plan: TCK-20260516-PERF-OPTIMIZATION-FINAL

## 1. Automated Unit Tests
Run the standalone regression test:
```bash
pytest tests/unit/strategic/test_routine_biasing.py
```
Expected output: 2 passed, 0 failed.

Run the full unit test suite:
```bash
pytest tests/unit
```
Expected output: 730 passed (100% success rate).

## 2. Automated Performance Benchmarks
Run the full performance benchmark suite:
```bash
pytest tests/perf -s
```
Expected output: All 47 tests passed. Specifically, verify that `test_perf_combat[500]`, `test_perf_movement[500]`, `test_perf_movement[1000]`, `test_perf_movement[5000]`, `test_perf_resource[500-500]`, `test_perf_resource[1000-1000]`, and `test_perf_strategic[1000]` pass with p95 tick latency within bounds.

## 3. Observability Verification
Verify in pytest standard output that kernel warnings regarding exceeded tick budgets (100.0ms) are eliminated.
