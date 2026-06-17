---
status: active
layer: engine
authority: P1
audience: developer
---

# Runtime State Retention Reference

Documents every long-lived structure in the engine and its exact resource boundary. Defines the retention policy (REJECT vs EVICT_OLDEST) for each structure and the overflow behavior when bounds are exceeded.

## Retention Bounds

| Structure Name | Owner | Authoritative? | Bound Type | Retention Rule | Overflow Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `entities` | `AuthoritativeState` | YES | Count | 10,000 | `REJECT` |
| `global_resources` | `AuthoritativeState` | YES | KeyCount | 500 | `REJECT` |
| `world_history` | `HistoryManager` | NO | Generation | 1,000 ticks | `EVICT_OLDEST` |
| `event_logs` | `Kernel` | NO | Count | 5,000 events | `EVICT_OLDEST` |
| `action_queue` | `Scheduler` | YES | Count | 2,000 pending | `REJECT` |
| `diagnostic_trace` | `Observability` | NO | Memory | 50 MB | `EVICT_OLDEST` |
| `metric_buffer` | `MetricsSystem` | NO | Time | 3,600 seconds | `COMPACT` |

## Default Rules

- **Authoritative Registries**: Default to `REJECT`. Silent eviction is prohibited as it causes state corruption.
- **Non-Authoritative Windows**: Default to `EVICT_OLDEST`. These are the primary targets for memory reuse.

## Regression Risks

- **Identity Leakage**: If `entities` overflow is handled by `EVICT`, downstream systems may hold dead references.
- **Divergence**: If `REJECT` occurs on one client but not another (due to non-deterministic input), simulations will diverge.
