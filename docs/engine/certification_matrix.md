---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 9 Certification Matrix

| Scenario Name | Runtime Profile | Hardward Binding | Required Proof | Fail Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **IDLE_100** | `prod_light` | Detected | 100 ticks, 0 shedding. | Any `MODE != NORMAL`. |
| **RAM_SATURATE** | `prod_medium`| Detected | Cross `degradation_threshold_ram`. | Crash before shedding. |
| **LATENCY_SPIKE**| `prod_heavy` | Class B+ | Shed actions on budget overrun. | Tick $> budget$ without shedding. |
| **RECOVERY_TEST**| `prod_medium`| Detected | Return to `NORMAL` in $< 50$ ticks. | Persistent shedding after fix. |
| **SEMANTIC_SYNC**| `prod_heavy` | Detected | Hash match vs sequential baseline. | `hash != baseline_hash`. |

## 1. Scenario Expectation Fields
- `expected_governor_modes`: (e.g., `NORMAL` -> `DEGRADED` -> `NORMAL`).
- `requires_recovery`: `True` for recovery-specific tests.
- `requires_semantic_equivalence`: `True` for hash verification.
- `sampling_interval_ticks`: $N$ (Scenario specific).

## 2. Evidence Requirements
- **JSON**: Full series of `MeasurementPoint` snapshots.
- **Trace**: Replay events showing exact governor mode transitions.
- **Audit**: Log entry confirming no unbound performance claims were made.

## 3. Regression Risks
- If **Shedding Order** is violated: System may drop critical work while keeping optional junk.
- If **Recovery** is missed: System stays in "Safe mode" indefinitely, killing UX.
- If **Drift** is missed: Concurrent optimizations may be subtly breaking game logic.
