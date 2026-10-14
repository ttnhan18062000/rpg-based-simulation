---
status: active
layer: engine
authority: P1
audience: developer
---

# Operational Controls Reference

Defines the engine's startup validation rules, runtime operational flags, graceful shutdown lifecycle, and signal surface policy. These controls govern how the engine is started, operated, and shut down safely.

## 1. Startup Validation Controls

| Control | Purpose | Rejection Rule |
| :--- | :--- | :--- |
| **Schema Check** | Ensure all required profile fields are present. | Reject if missing or malformed. |
| **Logic Consistency** | Ensure budget % totals are sane (< 100%). | Reject if sum > 100%. |
| **Internal Safety** | Match queue depths to memory bounds. | Reject if theoretical max memory > `max_ram_mb`. |
| **Forbidden Flags** | Block mode-override flags that bypass governor. | Reject if `FORCE_NORMAL`, `BYPASS_GOVERNOR` or `DISABLE_RESOURCE_CEILINGS` is present (`ProfileValidator.validate_flags`, `src/config/validator.py`). |

## 2. Dynamic Operational Flags (Runtime)

Flags are the `flags` dict given to `Kernel`. A flag that nothing reads is ignored without an error (`test_flags_cannot_alter_authoritative_semantics` relies on it), so a table row is only a control if the code in the last column reads it. The tests that pin each row are in `tests/unit/core/test_operational_flags.py`.

**Read by the kernel**

| Flag | Purpose | Status | Constraint and where it is read |
| :--- | :--- | :--- | :--- |
| `no_replay` | Stop the replay sink. | Safe | Non-authoritative only: the state hash is the same with and without it. `Kernel.__init__` sets `GovernorPolicy.replay_allowed=False` (`src/engine/kernel.py`) and the kernel re-applies it after every governor evaluation in `_phase_init`, so no mode turns replay back on. This is the real replay switch. |
| `no_frame_pacing` | Skip the frame-pacing sleep at the end of a tick. | Safe | Timing only (`Kernel._tick_once_inner`). |
| `audit_mode` | Audit run: per-phase fingerprint checks and zeroed pressure signals. | Audit and test use | Wins over the profile's `signal_contract`; with it set, the governor never leaves `NORMAL` (`Kernel.__init__`, `select_signal_source`). Not an operator control. |
| `audit_dirty_set`, `force_full_scan` | Dirty-set audit and a forced full candidate scan. | Audit and test use | Passed to the apply path and the refinement pipeline (`Kernel.__init__`). Not operator controls. |
| `perf_tracker` | Accepted and stored by the kernel (`Kernel.__init__`); no code reads it, so it has no effect. | No effect | Do not rely on it. |

**Not implemented: no code in `src/` reads these flags**

| Flag | Purpose | Status | Constraint |
| :--- | :--- | :--- | :--- |
| `FORCE_REPLAY_OFF` | Emergency stop of persistence sink. Not implemented; use `no_replay`. | Not implemented | A kernel given this flag behaves exactly as without it. |
| `SELECT_PROFILE` | Switch active envelope. Not implemented. | Not implemented | The profile is fixed when the kernel is built. |
| `FORCE_DEGRADED` | Manual pressure simulation. Not implemented. | Not implemented | A forced mode would change the mode only (cadence, phase budgets, concurrency, replay); it sheds no work. `ResourceGovernor.force_mode` (`src/engine/governor.py`) has no caller since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`. |

**Forbidden and validated**

| Flag | Purpose | Status | Constraint |
| :--- | :--- | :--- | :--- |
| `FORCE_NORMAL`, `BYPASS_GOVERNOR`, `DISABLE_RESOURCE_CEILINGS` | Bypass the governor or the resource ceilings. | **FORBIDDEN** | Rejected with `ConfigValidationError` by `ProfileValidator.validate_flags` (`src/config/validator.py`), which `Kernel` calls during construction. Violates resource law. |
| `SURVIVAL_ONLY`, `REPLAY_ENABLED` | Intended to select survival-only or replay-on behaviour. | Validated, not read | `validate_flags` rejects the pair together, and `REPLAY_ENABLED` with a 0 KB replay buffer. Nothing else reads either flag, so alone they change nothing. |

## 3. Graceful Shutdown Lifecycle

| Step | Action | Authoritative Status | Failure Mode |
| :--- | :--- | :--- | :--- |
| **1. Suspension** | Block new work and scheduler updates. | Authoritative | Halt simulation. |
| **2. Auth Snapshot** | Emit final authoritative state hash. | Authoritative | Mandatory. |
| **3. Replay Flush** | Attempt final buffer write to disk. | Non-Authoritative | Timeout (5 s) → Truncate |
| **4. Manifest Closing** | Mark run as COMPLETED or TRUNCATED. | Non-Authoritative | Best effort. |

## 4. Signal Surface Policy

- **Authoritative Integrity**: No surfaced signal (metric or trace) shall ever be passed as input to a simulation phase.
- **Privacy**: Surfaced state must not expose raw entity data beyond what is required for operational monitoring.
