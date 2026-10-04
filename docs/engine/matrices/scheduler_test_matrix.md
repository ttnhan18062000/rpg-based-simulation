---
status: active
layer: engine
authority: P1
audience: developer
---

# Scheduler Verification Surface

Tests that pin the deterministic scheduler and work classification laws. Every behavioral guarantee in the scheduler contract must be covered by at least one regression test.

## 1. Scheduler Contract

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_readiness_driven_selection` | Entities [99, 100, 101] | Only 100, 101 selected | Early action or missed due work |
| `test_deterministic_tiebreak` | 3 entities at 100 readiness | Ordered by ID: 1, 2, 3 | Nondeterministic iteration order |
| `test_stable_periodic_order` | 2 subsystems due same tick | Ordered by fixed ID | Intermittent periodic drift |

## 2. Work Classification

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_bucket_prioritization` | 1 CRITICAL, 1 PERIODIC | CRITICAL executes first regardless of ID | Priority inversion |
| `test_subordinate_opportunistic` | 1 CRITICAL, 1 OPPORTUNISTIC | CRITICAL runs first | Optional work gaining authority |

## 3. Bounded Work Debt

> **Status 2026-10-04:** only the drain half of the debt design exists; nothing produces debt, so the overflow tests below were never written (`test_debt_overflow_reject` is not in `tests/`). The tests that exist seed debt by hand (`tests/unit/core/test_deferred_work_debt.py`), and `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` guards that production debt stays empty. Retirement: `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`.

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_non_deferrable_critical` | CRITICAL work budget overflow | Kernel error / violation | Illegal critical deferral |
| `test_deferred_drain_order` | Deferred work from T-1 | Runs before T current work | Backlog starvation |
| `test_debt_overflow_reject` | Deferred pile > capacity | `RetentionError` or similar | Unbounded backlog growth |

## Regression Intent

- **Semantic Drift**: Catching cases where scheduling changes who gets to act first.
- **Hidden Backlogs**: Catching deferred queues that grow without limits. (No deferred queue exists in production today; see the status note in section 3.)
- **State Inconsistency**: Catching cases where the scheduler uses non-authoritative data to make decisions.
