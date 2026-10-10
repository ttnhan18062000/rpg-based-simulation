---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT
artifact_type: plan
tags: [architecture, testing]
---

# Plan
`store/atlas.py` (pure packer, minimal PNG encoder, `verify_atlas`), `contracts/atlas.py` (`runtime_atlas` record), `runtime_export.export_runtime(atlases=False)` and CLI `--atlas`. One sheet per registry family, fixed shelf (1024 wide), 1 px extrude, 1 px gutter, sheets at most `MAX_ATLAS_DIM` = 1024. The per-file export and the manifest are untouched; export verifies each sheet by a full decode before writing.

## Proof Plan
- Every one of rc-0008's 70 keys reads back from its atlas with the artifact's exact pixels (test against the per-file export).
- Export twice: identical bytes. With and without `--atlas`: manifest and PNGs byte-identical.
- Extrude (edges and corners) and gutter proven pixel by pixel on synthetic mixed-size sets; damaged sheets (rect, extrude, gutter, file hash, size) and a consistent sheet holding the wrong picture are refused.
- Mutants killed: extrude clamp, input-order independence, whole-sheet comparison, shelf width, per-rectangle pixel hash (needed an extra test), a corrupted source image. zlib level 6 vs 9 is not observable behaviour (survives by design; determinism holds either way).
