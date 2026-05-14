# Milestone B: Test Matrix (Operational Truth)

## 1. Signal Truth Tests
Verify that surfaced signals represent real accounting.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_worker_utilization_peak` | Saturated pool mid-tick | `worker_utilization` > 0.0 even if read after completion | Idle-sampling drift |
| `test_queue_utilization_peak` | Queue full mid-tick | `queue_utilization` reflecting peak backlog | Empty-queue illusion |
| `test_dropped_work_attribution` | Shedding via Survival mode | `dropped_work_count` > 0 with correct delta | Silent work loss |
| `test_replay_backlog_truth` | Staged events in buffer | `replay_backlog_kb` matches estimated payload | Buffer-blindness |

## 2. Boundedness & Trend Tests
Verify history invariants and mathematical stability.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_signal_history_bounds` | 1000+ ticks | `signal_history` length == 100 | Memory leak (History) |
| `test_rolling_compute_average` | Variable compute times | Average reflects window, not cumulative session | Outdated pressure logic |
| `test_memory_trend_slope` | Sustained growth/leak | `memory_trend` > 0 using windowed slope | Jitter-blindness |

## 3. Governor Transition Tests
Verify deterministic escalation and recovery.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_immediate_escalation` | Spiky pressure in 1 tick | Transition to DEGRADED in same tick | Delayed safety response |
| `test_gated_recovery` | Low pressure < Watermark | Mode change only after `confidence_window` | Flapping / Thrashing |
| `test_monotonic_mode_order` | Rising pressure | Mode moves N -> C -> D -> S without jumps | Logic re-entry bugs |

## 4. Isolation & Policy Tests
Verify separation between Control and Authority.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_governance_isolation` | Mode change S -> NORMAL | `get_hash()` returns same value for identical State | Hash contamination |
| `test_policy_shed_determinism` | Survival Mode policy | Class selection is bit-identical for same inputs | Nondeterministic shedding |

## 5. Documentation Matrix
| Artifact | Link | Purpose |
| :--- | :--- | :--- |
| Signals Contract | [runtime_signals_contract_mb.md](../engine/runtime_signals_contract_mb.md) | The Law |
| Governor Law | [runtime_signals_contract_mb.md](../engine/runtime_signals_contract_mb.md) | The Logic |
| Closure Proof | [test_milestone_b_closure.py](../../tests/governance/test_milestone_b_closure.py) | The Gate |
