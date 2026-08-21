---
status: active
layer: engine
authority: P1
audience: developer
---

# Signal Truth Verification

Verifies that all surfaced runtime signals represent real, accurate accounting of engine state — not sampled approximations or cached stale values.

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
| `test_signal_history_bounds` | 1000+ ticks | `signal_history` length == 100 | Memory leak (history) |
| `test_rolling_compute_average` | Variable compute times | Average reflects window, not cumulative session | Outdated pressure logic |
| `test_memory_trend_slope` | Sustained growth/leak | `memory_trend` > 0 using windowed slope | Jitter-blindness |

## 3. Governor Transition Tests

Verify deterministic escalation and recovery.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_immediate_escalation` | Spiky pressure in 1 tick | Transition to DEGRADED in same tick | Delayed safety response |
| `test_gated_recovery` | Low pressure < Watermark | Mode change only after `confidence_window` | Flapping / thrashing |
| `test_monotonic_mode_order` | Rising pressure | Mode moves NORMAL → CONSTRAINED → DEGRADED → SURVIVAL without jumps | Logic re-entry bugs |

## 4. Isolation & Policy Tests

Verify separation between control signals and authoritative state.

| Test Name | Input / Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_governance_isolation` | Mode change SURVIVAL → NORMAL | `get_hash()` returns same value for identical state | Hash contamination |
| `test_policy_shed_determinism` | Survival mode policy | Class selection is bit-identical for same inputs | Nondeterministic shedding |

## Documentation Matrix

| Artifact | Link | Purpose |
| :--- | :--- | :--- |
| Signals Contract | [signal_truth_contract.md](../contracts/signal_truth_contract.md) | The Law |
| Closure Proof | `tests/integration/kernel/test_milestone_b_closure.py` | The Gate |
