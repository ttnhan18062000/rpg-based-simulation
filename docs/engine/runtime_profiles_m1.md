# Runtime Profiles and Resource-Envelope Contract — Milestone 1

## 1. Purpose
This document defines the operational contract for bounded resource usage. Runtime profiles are first-class configuration objects that dictate the maximum resource "envelope" the engine is allowed to consume.

## 2. Profile Semantics
- **Hard Ceilings**: A profile defines absolute limits, not recommendations.
- **Envelope Compliance**: The engine must operate within these limits or trigger controlled degradation/shutdown.
- **Validation**: At startup, profiles must be validated for completeness and consistency.

## 3. Resource-Envelope Fields
Every runtime profile must explicitly define the following fields:

| Field | Description | Constraint |
| :--- | :--- | :--- |
| `max_ram_mb` | Maximum Resident Set Size (RSS) allowed. | Hard limit |
| `max_cpu_percent` | Balanced CPU usage percentage target. | Operational target |
| `max_worker_count` | Maximum concurrent workers allowed. | Hard limit |
| `max_queue_depth` | Limit for action and work queues. | Overflow target |
| `max_replay_buffer_kb`| Memory cap for in-memory replay window. | Hard limit |
| `max_tick_budget_ms` | Maximum milliseconds allowed per authoritative tick. | Latency target |
| `degradation_threshold`| CPU/RAM pressure level to trigger shedding. | Percentage |

## 4. Performance Language Contract
- **Throughput vs. Envelope**: A profile guarantees **Envelope Compliance**, not a fixed throughput.
- **Hardware Classes**:
    - **Class A (Server)**: High throughput within the envelope.
    - **Class B (Dev/Workstation)**: Medium throughput within the envelope.
    - **Class C (Legacy/Edge)**: Low throughput, potential frequent degradation.
- **Rule**: The same profile on different hardware classes must yield **identical semantics** and **identical resource ceilings**, but will result in different throughput.

## 5. Runtime Modes
Profiles define the thresholds for switching between:
- `NORMAL`
- `CONSTRAINED` (Early shedding of non-authoritative metrics)
- `DEGRADED` (Significant shedding of replay and diagnostics)
- `SURVIVAL` (Authoritative only, minimal observability)

## 6. Non-Goals
- Real-time governor logic (Implemented in Milestone 5).
- Auto-scaling of workers.
- Dynamic profile switching based on external load.
