---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 6 Test Matrix

## Verification Strategy
Milestone 6 tests focus on the boundary laws of persistence: bounded staging, deterministic rotation, and non-authoritative fallback under pressure.

## 1. Replay Contract (`test_replay_contract.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_non_authoritative`| Sink Failure | Tick continues; no stall | Persistence-driven stalling |
| `test_deterministic_order`| Multi-tick run | Replay stream matches kernel order | Out-of-order diagnostics |
| `test_reproducibility` | Same seed/profile | Bit-identical replay chunks | Nondeterministic capture |

## 2. Chunking & Manifest (`test_replay_chunk_rotation.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_size_rotation` | 1MB data | New chunk created at boundary | Oversized persistence files |
| `test_tick_rotation` | 100 ticks | Manifest updated with new chunk | Index-mismatch forensics |
| `test_manifest_integrity`| Close run | Valid JSON manifest exists | Missing metadata in replay package|

## 3. Staging & Overflow (`test_replay_overflow.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_staging_bound` | Data > Profile Cap | Buffer truncated at cap | Unbounded staging memory |
| `test_sink_slowdown` | Slow write | Buffer drops via Waterfall policy | Backlog build-up in RAM |
| `test_waterfall_drop` | Buffer full | Non-auth traces dropped first | Loss of critical forensics |

## 4. Modal Richness (`test_replay_modes.py`)
| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_off_mode` | REPLAY=OFF | 0 bytes persisted | Ghost IO in off mode |
| `test_minimal_richness`| REPLAY=MINIMAL | Headers only; no payloads | Over-capturing in low-modes |
| `test_governor_downgrade`| High Pressure | Mode drops DEBUG -> MINIMAL | Ignoring safety de-escalation |

## Regression Intent
Ensure that the persistence layer is a strictly controlled resource consumer, preventing the replay system from ever becoming a vector for memory instability or execution delays.
