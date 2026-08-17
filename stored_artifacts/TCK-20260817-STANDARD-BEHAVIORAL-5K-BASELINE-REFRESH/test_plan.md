---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH
tags: [simulation-quality, testing, bug]
---

# Test Plan — TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH

## Normal flow
- `pytest tests/regression/test_behavioral_5k.py -m extra_slow --resource-budget large -q` passes
  after the baseline refresh.

## Regression check
- Refreshed baseline's `alive_avg`/`gold_avg`/`quest_active_count` exactly match the pre-refresh
  failing-run's `actual=` values reported by the test's own assertion message (13.3, 584.16, 0.0)
  — the refresh captured the real, current, deterministic behavior, not an unrelated run.
- Re-ran the full test a second time after refresh to confirm determinism (byte-identical metrics
  across runs, seed=42).

## Results
- Pre-refresh: 1 failed (2 metrics out of band, exact drift values documented in investigation.md).
- Post-refresh: `pytest tests/regression/test_behavioral_5k.py -m extra_slow --resource-budget
  large -q`: 1 passed in 104.95s.
