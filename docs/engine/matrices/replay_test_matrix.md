---
status: active
layer: engine
authority: P1
audience: developer
---

# Replay Verification Surface

Tests that pin the replay persistence layer's boundary laws: bounded staging, deterministic rotation, non-authoritative fallback under pressure, and modal richness enforcement.

## 1. Replay Contract (`test_replay_contract.py`)

| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_non_authoritative` | Sink failure | Tick continues; no stall | Persistence-driven stalling |
| `test_deterministic_order` | Multi-tick run | Replay stream matches kernel order | Out-of-order diagnostics |
| `test_reproducibility` | Same seed/profile | Bit-identical replay chunks | Nondeterministic capture |

## 2. Chunking & Manifest (`test_replay_chunk_rotation.py`)

| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_size_rotation` | 1 MB data | New chunk created at boundary | Oversized persistence files |
| `test_tick_rotation` | 100 ticks | Manifest updated with new chunk | Index-mismatch forensics |
| `test_manifest_integrity` | Close run | Valid JSON manifest exists | Missing metadata in replay package |

## 3. Staging & Overflow (`test_replay_overflow.py`)

| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_staging_bound` | Data > profile cap | Buffer truncated at cap | Unbounded staging memory |
| `test_sink_slowdown` | Slow write | Buffer drops via waterfall policy | Backlog build-up in RAM |
| `test_waterfall_drop` | Buffer full | Non-auth traces dropped first | Loss of critical forensics |

## 4. Modal Richness (`test_replay_modes.py`)

| Test Case | Input | Expected Output | Catchment |
| :--- | :--- | :--- | :--- |
| `test_off_mode` | `REPLAY=OFF` | 0 bytes persisted | Ghost IO in off mode |
| `test_minimal_richness` | `REPLAY=MINIMAL` | Headers only; no payloads | Over-capturing in low modes |
| `test_governor_downgrade` | High pressure | Mode drops DEBUG → MINIMAL | Ignoring safety de-escalation |

## Regression Intent

Ensures the persistence layer is a strictly controlled resource consumer and never becomes a vector for memory instability or execution delays.
