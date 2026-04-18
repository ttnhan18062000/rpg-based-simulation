# Milestone 3 Retention Matrix

## 1. Purpose
This document logs every long-lived structure in the engine and its exact resource boundary.

| Structure Name | Owner | Authoritative? | Bound Type | Retention Rule | Overflow Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `entities` | `AuthoritativeState` | YES | Count | 10,000 | `REJECT` |
| `global_resources`| `AuthoritativeState` | YES | KeyCount | 500 | `REJECT` |
| `world_history` | `HistoryManager` | NO | Generation | 1,000 Ticks | `EVICT_OLDEST` |
| `event_logs` | `Kernel` | NO | Count | 5,000 Events | `EVICT_OLDEST` |
| `action_queue` | `Scheduler` | YES | Count | 2,000 Pending | `REJECT` |
| `diagnostic_trace`| `Observability` | NO | Memory | 50 MB | `EVICT_OLDEST` |
| `metric_buffer` | `MetricsSystem` | NO | Time | 3,600 Seconds | `COMPACT` |

## 2. Default Rules
- **Authoritative Registries**: Default to `REJECT`. Silent eviction is prohibited as it causes state corruption.
- **Non-Authoritative Windows**: Default to `EVICT_OLDEST`. These are the primary targets for memory reuse.

## 3. Regression Risks
- **Identity Leakage**: If `entities` overflow is handled by `EVICT`, downstream systems may hold dead references.
- **Divergence**: If `REJECT` occurs on one client but not another (due to non-deterministic input), simulations will diverge.
