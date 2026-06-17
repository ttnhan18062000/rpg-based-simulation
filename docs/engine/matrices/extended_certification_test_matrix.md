---
status: active
layer: engine
authority: P1
audience: developer
---

# End-to-End Certification Verification

Full engine certification surface: clean baselines, pressure and degradation paths, recovery sequences, lifecycle and fault tolerance, and equivalence proofs between local and concurrent execution.

## 1. Clean Baselines

| Scenario | Input Condition | Expected Law | Status |
| :--- | :--- | :--- | :--- |
| `IDLE_CLEAN` | Empty state, 0 debt | NORMAL mode, bit-identical hashes | **CERTIFIED** |
| `STEADY_STATE_NORMAL` | Low entity load | NORMAL mode throughout | **CERTIFIED** |
| `QUIET_TICK_STABILITY` | No actions pending | Zero work debt, 0% worker utilization | **CERTIFIED** |

## 2. Pressure & Degradation

| Scenario | Input Condition | Expected Law | Status |
| :--- | :--- | :--- | :--- |
| `RAM_PRESSURE` | 1000 entities | Escalation to CONSTRAINED/DEGRADED | **CERTIFIED** (Allowed Timeout) |
| `TICK_BUDGET_PRESSURE` | Massive entity load | Escalation to DEGRADED/SURVIVAL | **CERTIFIED** (Allowed Timeout) |
| `QUEUE_INFLIGHT_PRESSURE` | 500 entities | Shedding observed, conformance pass | **CERTIFIED** |
| `WORK_DEBT_BUILDUP` | Injected debt (30) | Escalation to DEGRADED | **CERTIFIED** |
| `REPLAY_PRESSURE` | 1000 entities | `REPLAY_ALLOWED=False` in SURVIVAL | **CERTIFIED** |

## 3. Recovery Paths

| Scenario | Input Condition | Expected Law | Status |
| :--- | :--- | :--- | :--- |
| `DEGRADED_NORMAL_RECOVERY` | 30 debt → Drain | Monotonic recovery to NORMAL | **CERTIFIED** |
| `SURVIVAL_NORMAL_RECOVERY` | 50 debt → Drain | Step recovery: SURVIVAL → DEGRADED → NORMAL | **CERTIFIED** |

## 4. Lifecycle & Faults

| Scenario | Input Condition | Expected Law | Status |
| :--- | :--- | :--- | :--- |
| `STARTUP_VALIDATION` | Boot sequence | Mode == NORMAL at tick 1 | **CERTIFIED** |
| `REPLAY_OVERFLOW_SURVIVAL` | Replay stress | No replay data loss in survival window | **CERTIFIED** |
| `SHUTDOWN_TIMEOUT_SURVIVAL` | Delayed exit | Lifecycle outcome == TIMEOUT | **CERTIFIED** |
| `WORKER_FAILURE_FALLBACK` | Worker crash simulation | Deterministic fallback hash | **CERTIFIED** |

## 5. Equivalence & Release

| Scenario | Input Condition | Expected Law | Status |
| :--- | :--- | :--- | :--- |
| `DET_EQUIV` | Seeded run | Bit-identical output (baseline vs concurrent) | **CERTIFIED** |
| `LOCAL_CONCURRENT_EQUIV` | Mixed execution | Hash parity (single vs partitioned) | **CERTIFIED** |
| `MISSING_SCENARIO_BLOCK` | Manual removal | FAIL release gate | **VERIFIED** |

## 6. Failure Taxonomy Verification

| Test Case | Expectation | Result |
| :--- | :--- | :--- |
| `FAILED_RECOVERY_TIMEOUT` | Correctly identified when recovery window missed | Verified in pre-60-tick runs |
| `FAILED_DEGRADATION_SEQUENCE` | Invalid mode jumps caught | Verified by ConformanceEvaluator |
| `FAILED_ENVELOPE` | RSS/CPU leaks caught | Verified by ConformanceEvaluator |
| `FAILED_LIFECYCLE` | Timeout/Success mismatch caught | Verified by ConformanceEvaluator |
