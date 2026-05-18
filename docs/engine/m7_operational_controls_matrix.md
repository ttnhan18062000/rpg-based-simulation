# Operational Controls Matrix (Milestone 7)

## 1. Startup Validation Controls
| Control | Purpose | Rejection Rule |
| :--- | :--- | :--- |
| **Schema Check** | Ensure all required profile fields are present. | Reject if missing or malformed. |
| **Logic Consistency** | ensure budget % totals are sane (<100%). | Reject if sum > 100%. |
| **Internal Safety** | Match queue depths to memory bounds. | Reject if theoretical max memory > `max_ram_mb`. |
| **Forbidden Flags** | Block mode-override flags that bypass governor. | Reject if "FORCE_NORMAL" exists. |

## 2. Dynamic Operational Flags (Runtime)
| Flag | Purpose | Status | Constraint |
| :--- | :--- | :--- | :--- |
| `FORCE_REPLAY_OFF` | Emergency stop of persistence sink. | Safe | Non-Authoritative only. |
| `SELECT_PROFILE` | Switch active envelope. | Safe | Only allowed at startup/reset. |
| `FORCE_DEGRADED` | Manual pressure simulation. | Safe | Accelerates shedding. |
| `FORCE_NORMAL` | Bypass governor. | **FORBIDDEN** | Violates resource law. |

## 3. Graceful Shutdown Lifecycle
| Sequence | Action | Authoritative Status | Failure Mode |
| :--- | :--- | :--- | :--- |
| **1. Suspension** | Block new work and scheduler updates. | Authoritative | Halt simulation. |
| **2. Auth Snapshot** | Emit final authoritative state hash. | Authoritative | Mandatory. |
| **3. Replay Flush** | Attempt final buffer write to disk. | Non-Authoritative | **Timeout (5s) -> Truncate** |
| **4. Manifest Closing**| Mark run as COMPLETED or TRUNCATED. | Non-Authoritative | Best effort. |

## 4. Signal Surface Policy
- **Authoritative Integrity**: No surfaced signal (Metric/Trace) shall ever be passed as input to a simulation phase.
- **Privacy**: Surfaced state must not expose raw entity data beyond what is required for operational monitoring.
