---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST
artifact_type: plan
tags: [architecture, rendering, determinism, testing]
---

# Plan — TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST

1. `contracts/runtime.py`: `RuntimeManifest` + `RuntimeEntry`, `size_bound = "MAX_MANIFEST_BYTES"`; add to `RECORD_TYPES`, a contract fixture, and the generic record tests via `RECORD_FILES`.
2. `store/runtime_export.py`: `export_runtime` (validate ids, check the output first, `verify`, read candidate, registry hash check, re-decode each PNG, canonical manifest, staged `.tmp-*` sibling + rename); `STORE_ALLOWED` row; the drawing server stays unable to import it.
3. CLI `export-runtime --catalog-id --release-id --out` (the existing `release` command spells `--catalog-id/--release-id`; the ticket said `--catalog/--release`).
4. `tests/visual_assets/store/runtime_fixture.py`: three 16 px shapes (diamond, disc, frame), deterministic renderer and ids, level-0 PNG encoding (zlib-independent bytes), `--write`/`--check`; commit the output under `frontend/src/visualAssets/__fixtures__/rehearsal/`.
5. Tests: contract, export (refusals with snapshots, determinism, no provenance), fixture (byte-identical regeneration, alpha masks differ), boundary.
6. Docs: `store_contract.md`. Raise `MAX_MANIFEST_BYTES` if the guard test says the runtime manifest is wider than the candidate manifest.
