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
| **Operational Flags** | `no_replay` flag active | `replay_allowed` is False from construction and after every governor evaluation, the replay sink receives no event, the state hash is unchanged (`test_no_replay_stops_the_replay_sink`) | Flag obedience. |
| **Operational Flags** | `FORCE_REPLAY_OFF`, `SELECT_PROFILE`, `FORCE_DEGRADED` (not implemented) | The run is identical to one without the flag (`test_unimplemented_operational_flags_change_nothing`); implementing one fails this test and the matrix must change with it | A documented control that nothing reads. |
| **Operational Flags** | `SURVIVAL_ONLY` or `REPLAY_ENABLED` alone | No change; together they raise `ConfigValidationError` (`test_validated_but_unread_flags_change_nothing`, `test_contradictory_flags_are_rejected`) | Validated-but-unread flags. |
| **Operational Flags** | `FORCE_NORMAL`, `BYPASS_GOVERNOR`, `DISABLE_RESOURCE_CEILINGS` (illegal flags) | `ConfigValidationError` ("is FORBIDDEN") (`test_each_forbidden_flag_is_rejected`) | Governor bypass attempt. |
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
