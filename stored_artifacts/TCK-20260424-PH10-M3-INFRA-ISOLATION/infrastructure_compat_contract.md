# V2 Infrastructure & Isolation Compatibility Contract

This document defines the supported infrastructure surface and isolation guarantees for the V2 engine.

## 1. Environment Variable Precedence
The engine follows a strict configuration precedence order:
1. **CLI Arguments** (Highest)
2. **Environment Variables** (Prefix: `RPG_`)
3. **YAML Configuration** (via `--config`)
4. **Hardcoded Defaults** (Lowest)

## 2. Supported Infrastructure Flags
| Flag | Impact | Legacy Parity |
| :--- | :--- | :--- |
| `BROKER_DISABLED=1` | Forces `max_worker_count=0` (Sequential execution). | **FULL**. Matches legacy in-process fallback. |
| `RPG_MAX_WORKER_COUNT` | Sets the maximum number of concurrent workers. | **FULL**. Maps to `num_workers`. |
| `RPG_MAX_RAM_MB` | Resource bound for profile validation. | **NEW**. V2-specific safety guard. |

## 3. Infrastructure Isolation
- **Import-Time Safety**: The core engine (`src_v2.engine.kernel`) is guaranteed to be importable without external infrastructure (RabbitMQ, Kafka, Postgres) present.
- **Runtime Fallback**: V2 uses local `ThreadPoolExecutor` as the primary concurrent substrate, eliminating the mandatory requirement for external brokers in standard operation.
- **Disabled-Mode Branching**: When `BROKER_DISABLED=1` is set, the engine bypasses thread pool initialization and executes all work packets synchronously in the kernel thread.

## 4. Divergences & Exclusions
- **RabbitMQ/Kafka Integration**: External broker support is not included in the Phase 10 baseline. All "Broker" interactions are currently handled via the internal `WorkerManager`.
- **Database Persistence**: State persistence is handled via JSON-L replay chunks and manifest files, not a live SQL database.
