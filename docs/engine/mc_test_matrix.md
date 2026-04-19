# Milestone C Test Matrix: Operational Integrity

## Replay Lifecycle Tests

| Test Name | Input Condition | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_replay_is_non_authoritative` | Sink raises `IOError` | Kernel continues normally; manifest marked failed. | Disk full causing engine crash. |
| `test_replay_order_preservation` | Out-of-order emission | Chunks on disk preserve emission sequence. | Sequential trace corruption. |
| `test_replay_overflow` | Buffer exceeding `capacity_kb` | Oldest events evicted first (Default). | Memory exhaustion from trace sprawl. |
| `test_on_tick_end_is_non_blocking` | Sink latency (500ms) | Kernel heart-beat returns <100ms. | Disk IO jitter stalling simulation. |
| `test_manifest_integrity` | Simulated process crash | Manifest preserved via atomic rename. | Corrupted manifest during power loss. |

## Startup Validation Tests

| Test Name | Input Condition | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_too_low_budget_rejection` | Budget < 1.0ms | `ConfigValidationError` raised. | Unstable sub-ms scheduling attempts. |
| `test_contradictory_flags` | SURVIVAL + REPLAY flags | Mutual exclusivity error raised. | Resource theft from core by trace in survival. |
| `test_forbidden_flag` | `BYPASS_GOVERNOR` flag | Hard rejection at startup. | Unauthorized contract bypassing. |
| `test_insufficient_ram_for_replay` | RAM < 32MB + Replay | Rejection of unsafe memory config. | Out-of-memory crashes on small hardware. |

## Shutdown Timeout Tests

| Test Name | Input Condition | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_shutdown_skips_rotation` | Budget remaining < 0.5s | Abort rotation; prioritize manifest write. | Shutdown hang on slow disk. |
| `test_shutdown_performs_rotation` | Budget remaining > 0.6s | Perform final flush then exit. | Data loss on healthy shutdown. |
| `test_graceful_shutdown` | `Kernel.shutdown()` | Stop work arrival -> Stop workers -> Finalize. | Zombie threads or leaked work results. |

## Runtime Snapshot Integrity Tests

| Test Name | Input Condition | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_snapshot_accuracy` | High pressure signals | All fields wired to real sensors (no placeholders). | Mislabeled or decorative metrics. |
| `test_signal_trending` | 5 consecutive ticks | `tick_compute_ms_avg` reflects real history. | Broken pressure accumulation logic. |

## Verification Intent
This matrix ensures that the engine's operational lifecycle is pinned by evidence. Every "Law" in the MC contract is verified through at least one deterministic test case.
