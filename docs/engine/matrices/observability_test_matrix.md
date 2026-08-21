---
status: active
layer: engine
authority: P1
audience: developer
---

# Observability Verification Surface

Tests that pin the operational lifecycle controls: startup validation, operational flag enforcement, graceful shutdown, and observability budget constraints.

| Test Group | Input Condition | Expected Result | Regression Caught |
| :--- | :--- | :--- | :--- |
| **Startup Validation** | Impossible budget (e.g. 110% total) | `ConfigValidationError` | Impossible resource allocation. |
| **Startup Validation** | Missing mandatory profile fields | `ConfigValidationError` | Partial/unsafe profile. |
| **Operational Flags** | `FORCE_REPLAY_OFF` flag active | Sink never called, Replay OFF status | Flag obedience. |
| **Operational Flags** | `FORCE_NORMAL` (illegal flag) | `SecurityError` or `Rejection` | Governor bypass attempt. |
| **Graceful Shutdown** | Call `shutdown()` under IO stress | Termination within timeout (5 s) | Hang during exit. |
| **Graceful Shutdown** | Process exit after final authoritative hash | Hash emitted, manifest written | Data loss on exit. |
| **Observability Budgets** | Continuous ticks for 1 hr (mocked) | `deque` size remains exactly 100 | Memory leak in metrics. |
| **Observability Budgets** | High CPU load profile | Sampling cadence drops automatically | Performance distortion. |

## Verification Commands

```bash
pytest tests/unit/core/test_startup_validation.py
pytest tests/unit/core/test_graceful_shutdown.py
pytest tests/unit/core/test_observability_budgets.py
pytest tests/unit/core/test_operational_flags.py
```
