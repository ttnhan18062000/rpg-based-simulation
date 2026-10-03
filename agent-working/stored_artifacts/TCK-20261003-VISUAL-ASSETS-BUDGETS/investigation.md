---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-BUDGETS
artifact_type: investigation
tags: [performance, testing, mcp]
---

# Investigation — TCK-20261003-VISUAL-ASSETS-BUDGETS

Machine: the licence holder's, Aseprite 1.3.18.6-x64, 2026-10-03. Script: `python -m tools.visual_assets_measure_budgets --only <name>` (list with `--list`).
Times are best of 3 up to 1024 px, single runs above; peak memory is Python allocations (tracemalloc).

## decode_scaling (pure-Python decode + pixels-v1, RGBA square)

| dim | decoded bytes | Paeth s | Sub s | peak MiB |
|---|---|---|---|---|
| 128 | 65664 | 0.033 | 0.010 | 0.3 |
| 256 | 262400 | 0.156 | 0.045 | 1.1 |
| 512 | 1049088 | 0.545 | 0.189 | 4.3 |
| 768 | 2360064 | 0.969 | 0.389 | 9.6 |
| 1024 | 4195328 | 1.728 | 0.672 | 17.0 |
| 1536 | 9438720 | 5.063 | 1.676 | 38.3 |
| 2048 | 16779264 | 7.867 | 3.138 | 68.0 |

A first, single-run pass gave 1024 px Paeth = 1.794 s and 768 px = 1.811 s (noise: 768 cannot cost more than 1024), which is why the cheap sizes were repeated.

## decode_at_decoded_bytes_bound
Largest square within `MAX_DECODED_BYTES` (25165824): 2508 px, decoded 25162764 B, PNG 228094 B, **13.72 s, 102.0 MiB**.

## record_sizes
Fixtures 341-985 B (largest `candidate_handoff_package.json` 985). Widest legal `CandidateHandoffPackage` (every free-text field widened, 16 x 256-char limitations): 7057 B ASCII, 19345 B four-byte UTF-8. Widest `IntakeResult` (64 x 256-char findings): 19331 B ASCII, **68483 B four-byte UTF-8 (over `MAX_RECORD_BYTES` 65536)**.

## registry_load
| case | file bytes | load |
|---|---|---|
| 4096 keys, 1024 aliases, 2 axes x 4 values | 1371610 (over `MAX_REGISTRY_BYTES`) | not loadable |
| 4096 keys, 1024 aliases, no axes | 728538 | 2.62 s, 36.2 MiB (record bound lifted for the timing) |
| 100 keys, 8 axes x 64 values | 747099 (7471 B/key) | 3.005 s, 36.8 MiB |

Bytes per key: 319.5 (2 axes x 4 values), 162.5 (no axes). **With the real `MAX_RECORD_BYTES` the registry accepts 207 two-axis keys, 373 no-axis keys** (bisected through `load_registry`): `parse_record` bounds the registry too (flag F1).

## aseprite_source_bytes (source `.aseprite` bytes)
| px | 1 frame flat | 1 frame noise | 16 frames flat | 16 frames noise |
|---|---|---|---|---|
| 16 | 312 | 1190 | 1242 | 15764 |
| 32 | 374 | 3784 | 1499 | 57238 |
| 64 | 468 | 14141 | 1788 | 222902 |
| 128 | 759 | 55764 | 2769 | 889025 |

(Re-run twice: identical values.)

## aseprite_timing
`apply_ops`: 256 rect ops on 128 px 0.082 s; 8192 noise pixels per call 0.139 s. 128 px noise source (55795 B, preview 83797 B): render scale 8 0.083 s, scale 16 0.258 s, review 1.293 s, adopt 1.867 s, build 0.063 s. 16 px: 0.034 / 0.041 / 0.084 / 0.077 / 0.044 s (preview 1683 B). One decode + hash of the real 128 px noise preview: 0.543 s (so adopt, about three decodes, is mostly Python).

## Findings for the planner
F1-F6 in `docs/assets/budgets.md`. Not fixed here (out of scope): the registry bound conflict (F1), `MAX_DECODED_BYTES` double role (F4), the decoder cost (F3).
