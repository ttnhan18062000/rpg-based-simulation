---
status: active
layer: engine
authority: P1
audience: developer
---

# Certification Verification Surface

The certification matrix defines the scenarios the engine must pass to be considered production-ready. Each scenario exercises a combination of runtime profile, hardware binding, and governor behavior under load.

## Certification Scenarios

| Scenario Name | Runtime Profile | Hardware Binding | Required Proof | Fail Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **IDLE_100** | `prod_light` | Detected | 100 ticks, 0 shedding. | Any `MODE != NORMAL`. |
| **RAM_SATURATE** | `prod_medium` | Detected | Cross `degradation_threshold_ram`. | Crash before shedding. |
| **LATENCY_SPIKE** | `prod_heavy` | Class B+ | Shed actions on budget overrun. | Tick > budget without shedding. |
| **RECOVERY_TEST** | `prod_medium` | Detected | Return to `NORMAL` in < 50 ticks. | Persistent shedding after fix. |
| **SEMANTIC_SYNC** | `prod_heavy` | Detected | Hash match vs sequential baseline. | `hash != baseline_hash`. |

## Scenario Expectation Fields

- `expected_governor_modes`: sequence of expected mode transitions (e.g. `NORMAL -> DEGRADED -> NORMAL`).
- `requires_recovery`: `True` for recovery-specific tests.
- `requires_semantic_equivalence`: `True` for hash verification.
- `sampling_interval_ticks`: scenario-specific sampling cadence.

## Evidence Requirements

- **JSON**: Full series of `MeasurementPoint` snapshots.
- **Trace**: Replay events showing exact governor mode transitions.
- **Audit**: Log entry confirming no unbound performance claims were made.

## Regression Risks

- If **Shedding Order** is violated: system may drop critical work while keeping optional work.
- If **Recovery** is missed: system stays in a degraded mode indefinitely.
- If **Drift** is missed: concurrent optimizations may be breaking game logic silently.
