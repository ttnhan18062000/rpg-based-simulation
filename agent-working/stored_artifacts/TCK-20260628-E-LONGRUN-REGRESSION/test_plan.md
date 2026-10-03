# Test Plan — TCK-20260628-E-LONGRUN-REGRESSION

## Regression Surface (existing tests that must pass)

- `tests/integration/scenarios/test_balance_regression.py` — combat attrition baseline
- `tests/certification/test_cert_long_run_stability.py` — performance stability (cert marks)
- `tests/integration/kernel/test_long_run_determinism.py` — 1000-tick determinism

## New Tests Required

### test_behavioral_5k_regression (tests/regression/test_behavioral_5k.py)
**Marks:** `extra_slow`, `regression`

Verifies:
1. 5000-tick run completes without exception (alive_avg > 0)
2. alive_avg within ±10% of baseline
3. gold_avg within ±20% of baseline (absolute tolerance when baseline=0)
4. quest_active_count within ±20% of baseline
5. Diagnostic error names the drifting metric and drift magnitude on failure
6. Test skips with helpful message when baseline not found (not a test failure)

### Unit tests for harness functions (no new file needed — inline in test module)
- `_check_metric("alive_avg", 15.0, 16.0, 0.10)` → passes (6.25% drift < 10%)
- `_check_metric("alive_avg", 5.0, 16.0, 0.10)` → fails (68.75% drift > 10%)
- `_check_metric("gold_avg", 0.5, 0.0, 0.20)` → fails (absolute: 0.5 > 0.20)
- `_check_metric("quest_active_count", 0.0, 0.0, 0.20)` → passes (both zero)

## Scoped Pytest Commands

```bash
# New test (requires baseline):
pytest tests/regression/ -m extra_slow --tb=short -v

# Full slow path (CI equivalent):
pytest tests/ -m "slow or extra_slow" --tb=short -q

# Quick sanity — just non-slow tests to verify imports:
pytest tests/regression/ --collect-only
```

## Anti-Drift Test Guards

- Baseline is committed JSON — any PR that changes behavioral dynamics MUST regenerate it.
- `_check_metric` uses relative drift, not absolute delta — tolerates world size changes.
- Test is gated behind `extra_slow` mark — never runs in fast CI paths.
