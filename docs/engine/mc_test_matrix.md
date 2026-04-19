# Milestone C Test Matrix: Operational Integrity

## Replay lifecycle tests
| Test Name | Input Condition | Exact Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_replay_mode_retention` | `DEBUG_WINDOWED` mode with buffer saturation. | Must preserve the **most recent** events (`EVICT_OLDEST`). | Loss of recent failure context. |
| `test_replay_saturation_rotation` | Buffer utilization reaches 90%. | Triggers an immediate "Early Rotation" at next tick start. | Overflow data loss due to late rotation. |
| `test_atomic_manifest_integrity` | System "crash" during manifest write (simulated). | `manifest.json` must remain uncorrupted (old version or new complete version). | Corrupted/Empty manifest file. |
| `test_sink_pressure_shedding` | Sink write speed falls behind emission rate. | ReplayManager must increase shedding or truncate oldest events without stalling kernel. | Unbounded memory growth or kernel stall. |

## Startup validation tests
| Test Name | Input Condition | Exact Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_contradictory_flag_rejection` | `REPLAY_ENABLED=True` with buffer budget of 0. | Raise `ConfigValidationError`. | Starts in inconsistent state. |
| `test_incomplete_envelope_rejection` | Missing required field `max_tick_budget_ms`. | Raise `ConfigValidationError`. | Crash later due to missing config. |
| `test_hardware_realism_warning` | Class C hardware with 2.0ms tick budget. | Log `WARNING`, but allow startup. | Hard rejection of valid (but tight) configs. |

## Operational flag tests
| Test Name | Input Condition | Exact Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_forbidden_flag_rejection` | Flag `BYPASS_GOVERNOR=True`. | Raise `ConfigValidationError`. | Authoritative contract bypass. |
| `test_safe_flag_acceptance` | Flag `LOG_LEVEL=DEBUG`. | Allow startup and apply flag. | Over-strict blocking of diagnostic tools. |

## Shutdown timeout tests
| Test Name | Input Condition | Exact Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_graceful_shutdown_flush` | Active events in sink buffer during shutdown. | All events should be flushed if within 5.0s budget. | Lost data on happy-path exit. |
| `test_shutdown_timeout_abort` | Sink intentionally hangs/stalls. | Kernel exits after 5.0s, aborting the flush but finishing clean exit. | Hanging process preventing container restart. |
| `test_final_checkpoint_emission` | Final tick of shutdown. | Authoritative hash and final status snapshot emitted. | Untraceable final state. |

## Runtime snapshot integrity tests
| Test Name | Input Condition | Exact Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_snapshot_truth_audit` | Periodic status poll. | All fields must match `get_stats()` from respective subsystems. | Placeholder/Decorative metrics. |
| `test_non_authoritative_isolation` | Replay/Observability work failure. | Authoritative hash MUST NOT change. | Observational logic leaking into game state. |

## Regression intent
The primary intent of this matrix is to prove that the **operational lifecycle** is a robust, bounded, and deterministic contract. These tests ensure that the engine remains safe even when external components (disk, IO, config) behave incorrectly.
