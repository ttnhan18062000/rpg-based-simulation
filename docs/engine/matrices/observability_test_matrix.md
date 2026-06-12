---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 7 Test Matrix

| Test Group | Input Condition | Expected Result | Regression Caught |
| :--- | :--- | :--- | :--- |
| **Startup Validation** | Impossible Budget (e.g. 110% total) | `ConfigValidationError` | Impossible resource allocation. |
| **Startup Validation** | Missing mandatory profile fields | `ConfigValidationError` | Partial/Unsafe profile. |
| **Operational Flags** | `FORCE_REPLAY_OFF` flag active | Sink never called, Replay OFF status | Flag obedience. |
| **Operational Flags** | `FORCE_NORMAL` (Illegal flag) | `SecurityError` or `Rejection` | Governor bypass attempt. |
| **Graceful Shutdown** | Call `shutdown()` under IO stress | Termination within timeout (5s) | Hang during exit. |
| **Graceful Shutdown** | Process exit after final authoritative Hash | Hash emitted, Manifest written | Data loss on exit. |
| **Observability Budgets**| Continuous ticks for 1hr (Mocked) | `deque` size remains exactly 100 | Memory leak in metrics. |
| **Observability Budgets**| High CPU load profile | Sampling cadence drops automatically | Performance distortion. |

## Verification Command
```bash
pytest tests/config/test_startup_validation.py
pytest tests/engine/test_graceful_shutdown.py
pytest tests/engine/test_observability_budgets.py
pytest tests/engine/test_operational_flags.py
```
