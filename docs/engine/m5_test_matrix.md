---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 5 Test Matrix

## Verification Strategy
The Milestone 5 test suite focuses on the deterministic behavior of the Resource Governor and the strict isolation of the Governance state from the Authoritative simulation.

## 1. Pressure & Mode Transitions (`test_resource_governor_contract.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_escalation` | Signal > threshold | Immediate mode increase | Slow reaction to pressure |
| `test_multi_signal` | Any signal > threshold | Mode increase | Partial signal blindness |
| `test_profile_compliance` | Profile A vs Profile B | Different transition points | Hardcoded limits |

## 2. Stability & Anti-Thrashing (`test_anti_thrashing.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_low_watermark` | Signal at 95% of threshold | No recovery from higher mode | Oscillation near threshold |
| `test_dwell_time` | Signal drops but 1 tick pass | Mode stays high | Rapid recovery instability |
| `test_sequential_pressure` | Alternating hi/lo signals | Stable highest-mode dwell | Hysteresis bypass |

## 3. Degradation & Shedding (`test_degradation_order.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_waterfall_order` | Rising Modes | Opp -> Diag -> Periodic (Non-Auth) | Incorrect shedding order |
| `test_critical_protection` | SURVIVAL mode | 0 critical tasks dropped | Semantic corruption |
| `test_authoritative_periodic` | SURVIVAL mode | Auth periodic tasks survive | Mandatory up-keep loss |

## 4. Architectural Isolation (`test_governance_isolation.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_hash_invariance` | Mode change | Checkpoint Hash identical | State contamination |
| `test_signal_history_bound` | 1000 signals | Max N signals retained | Memory leak in history |
| `test_policy_abstraction` | Mock Mode | Scheduler sees Policy Bools | Scheduler-Governor coupling |

## Regression Intent
Ensure that the safety-control layer protects the engine without ever becoming a source of nondeterminism or simulation divergence.
