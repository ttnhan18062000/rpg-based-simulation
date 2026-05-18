# Milestone 4 Test Matrix — Scheduling & Debt

## 1. Purpose
This matrix defines the tests required to pin the Milestone 4 deterministic scheduler and work classification laws.

## 2. Test Groups

### Group A: Scheduler Contract
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_readiness_driven_selection`| Entities [99, 100, 101] | Only 100, 101 selected | Early action or missed due work |
| `test_deterministic_tiebreak` | 3 entities at 100 readiness | Ordered by ID: 1, 2, 3 | Nondeterministic iteration order |
| `test_stable_periodic_order` | 2 subsystems due same tick | Ordered by fixed ID | Intermittent periodic drift |

### Group B: Work Classification
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_bucket_prioritization` | 1 Critical, 1 Periodic | Critical executes first regardless of ID | Priority inversion |
| `test_subordinate_opportunistic` | 1 Critical, 1 Opp | Critical runs first | Optional work gaining authority |

### Group C: Bounded Work Debt
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_non_deferrable_critical`| Critical work budget overflow | Kernel Error / Violation | Illegal critical deferral |
| `test_deferred_drain_order` | Deferred work from T-1 | Runs before T current work | Backlog starvation |
| `test_debt_overflow_reject` | Deferred pile > Capacity | `RetentionError` or similar | Unbounded backlog growth |

## 3. Regression Intent
- **Semantic Drift**: Catching cases where "Optimization" or "Scheduling" changes who gets to act first.
- **Hidden Backlogs**: Catching deferred queues that grow without limits.
- **State Inconsistency**: Catching cases where the scheduler uses non-authoritative data to make decisions.
