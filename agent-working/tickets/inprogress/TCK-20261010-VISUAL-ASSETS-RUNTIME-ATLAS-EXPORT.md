---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT
phase: open
date: 2026-10-10
tags: [architecture, determinism, testing]
---

# TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT

## Title
Optional per-set sprite atlases in the runtime export (deterministic packing, extrude and padding), not wired

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 5 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. store_contract.md:204 lists atlases as not built. The client and harness draw with Canvas 2D (borderRender.ts, GameCanvas.tsx), so atlases are an export option with no consumer yet (owner chose to build it anyway, 2026-10-10).

## Scope
- An opt-in export flag producing one atlas PNG per set (terrain, icons, masks) plus an atlas JSON (key -> rect) next to the unchanged per-file runtime export; the runtime manifest stays as is.
- Deterministic packing (sorted by key, fixed shelf/grid), 1 px extrude + padding against seams; atlas PNG written by one deterministic encoder (no time/text chunks; same input -> same bytes, tested).
- Verify: each atlas rect's pixels equal the source artifact's pixels (pixel-hash check per key).
- store_contract.md section; budgets row for atlas size.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Client loading from atlases (activation). Changing the runtime manifest schema.

## Acceptance Criteria
- [ ] Rect pixel equality for every key of rc-0008; export-twice byte equality.
- [ ] Extrude/padding tested at edges; atlas JSON schema documented.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions
- After child 3 (shares the determinism checks).

## Implementation Notes
See staging plan/investigation. `MAX_ATLAS_DIM` 1024 is a new bound. **Owner decision, 2026-10-10, relayed by asset-planner from its blocking question (the owner's answer, verbatim): "Approve 1024".** The budgets row is now `APPROVED 2026-10-10`.


## Test Summary
17 new tests pass; store, boundaries and budgets parity 1335 passed.


## Files Changed
- `docs/assets/budgets.md`
- `docs/assets/store_contract.md`
- `tests/visual_assets/store/unit/test_atlas.py`
- `tests/visual_assets/store/unit/test_runtime_export.py`
- `tests/visual_assets/test_boundaries.py`
- `visual_assets/store/atlas.py`
- `visual_assets/store/cli.py`
- `visual_assets/store/config.py`
- `visual_assets/store/contracts/atlas.py`
- `visual_assets/store/intake/validator.py`
- `visual_assets/store/runtime_export.py`

## Completion Summary
Opt-in `export-runtime --atlas`: one sheet per registry family beside the unchanged per-file export, with extrude and gutter, deterministic packing and the manifest untouched; every key of `rc-0008` reads back from its atlas with the artifact's pixels, and two exports are byte-identical. `MAX_ATLAS_DIM` 1024 is owner-approved. After the planner's review the default export holds no decoded image and an oversized family refuses before anything is decoded again (the Review fix section below). Not wired: nothing reads the atlases.

## Review fix (asset-planner, 2026-10-10): the default export must not hold decoded images
`export_runtime` kept every decoded artifact image (`images[entry.pixel_hash] = decoded`) on EVERY export, with or without atlases: in the worst case `MAX_VISUAL_KEYS` (1024) x `MAX_DECODED_BYTES` (about 4 MiB) resident, for an opt-in feature. Fixed: the default path keeps no image (only the entry's size is kept). With `--atlas`, every family's sheet size is computed from the entries' own sizes (`atlas.pack`) and an oversized family refuses (`atlas_too_large`) BEFORE any image is decoded again; then one family's images are decoded at a time and dropped after its sheet is built. Proof (`tests/visual_assets/store/unit/test_runtime_export.py`): the default export never has more than one decoded image alive and never calls `build_atlas` or `pack`; the atlas pass holds one family at a time and decodes each entry once more plus each finished sheet once; a mutant with the early check disabled costs extra decodes before refusing. The default-path test, the one-family test and the mutant all fail with the fix reverted; the oversized-family test alone passes on the old code too (the old code never re-decoded before its late check), so the mutant is what proves that property is measurable. `decode_png` keeps its own documented LRU cache of 4 images, which the tests clear on each call so only what the export itself retains is counted.
