---
status: active
layer: engine
authority: P1
audience: developer
---

# Resource Governor Verification Surface

Tests that pin the deterministic behavior of the resource governor and enforce strict isolation of governance state from the authoritative simulation.

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
| `test_dwell_time` | Signal drops but 1 tick passes | Mode stays high | Rapid recovery instability |
| `test_sequential_pressure` | Alternating hi/lo signals | Stable highest-mode dwell | Hysteresis bypass |

## 3. Degradation & Shedding (removed in Phase B)

The waterfall (opportunistic, diagnostics, non-authoritative periodic) and its tests (`test_degradation_order.py`: `test_waterfall_order`, `test_authoritative_periodic`) were removed with the never-wired periodic and opportunistic path (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, DEV-019). What remains pinned: CRITICAL work is never shed (`test_the_scheduler_selects_only_entity_work`, `test_a_run_produces_only_critical_entity_work_and_never_drops_work`, including in SURVIVAL), and the mode-dependent levers are covered by the governor and phase-governor tests above.

## 4. Architectural Isolation (`test_governance_isolation.py`)

| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_hash_invariance` | Mode change | Checkpoint hash identical | State contamination |
| `test_signal_history_bound` | 1000 signals | Max N signals retained | Memory leak in history |
| `test_policy_abstraction` | Mock mode | Scheduler sees policy booleans | Scheduler-governor coupling |

## Regression Intent

Ensures the safety-control layer protects the engine without ever becoming a source of nondeterminism or simulation divergence.
