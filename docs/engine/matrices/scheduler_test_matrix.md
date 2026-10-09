---
status: active
layer: engine
authority: P1
audience: developer
---

# Scheduler Verification Surface

Tests that pin the deterministic scheduler and work classification laws. Every behavioral guarantee in the scheduler contract must be covered by at least one regression test.

## 1. Scheduler Contract

Pinned in `tests/unit/kernel/test_scheduler_contract.py` and `tests/integration/kernel/test_work_debt_is_gone.py`.

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_readiness_driven_selection` | Entities at readiness 100, 99.9, 150 | All three selected as `ENTITY_BRAIN` (a brain is never readiness-gated), ordered readiness DESC then id ASC | Early action or missed due work |
| `test_action_readiness_gate` | `ENTITY_ACT` with a payload, readiness 50 vs 100 | Only the ready one is selected | An action running before it is ready |
| `test_deterministic_tiebreak` | 3 entities at 100 readiness | Ordered by ID: 1, 2, 3 | Nondeterministic iteration order |
| `test_the_scheduler_selects_only_entity_work` | One entity | Every item is `CRITICAL` entity work; the dropped count is 0 | Periodic, deferred or opportunistic selection returning |

## 2. Work Classification

Removed in Phase B (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`). The scheduler produces only `CRITICAL` entity work, so the bucket-priority tests (`test_bucket_prioritization`, `test_subordinate_opportunistic`) and the periodic ordering test (`test_stable_periodic_order`) were removed with the periodic, opportunistic and deferred branches. The `WorkClass` members `PERIODIC`, `OPPORTUNISTIC` and `DEFERRED` remain in `src/core/work.py` as unused constants (their `ConcurrencyLaw` priorities are still used by result-ordering tests); removing them is a follow-up.

## 3. Bounded Work Debt

Removed in Phase B. Work debt, the `DRAIN_DEBT` drain and the `max_work_debt` threshold no longer exist (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, owner decision 2026-10-04). The overflow tests below were never written, and the drain tests (`test_deferred_work_debt.py`, `test_milestone_c_desimulation.py`) and the production guard (`test_work_debt_stays_empty_in_production.py`) were deleted. `tests/integration/kernel/test_work_debt_is_gone.py` pins that the names, fields, signal and metric are gone.

## Regression Intent

- **Semantic Drift**: Catching cases where scheduling changes who gets to act first.
- **State Inconsistency**: Catching cases where the scheduler uses non-authoritative data to make decisions.
