---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT
phase: implement
date: 2026-10-10
tags: [architecture, testing]
---

# TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT

## Title
Opt-in runtime export of slices (`export-runtime --slices` writes slices.json in artifact pixels)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 2 of `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`. Mirrors `export-runtime --animation` (`cli.py:87, 238`; `runtime_export.py:60, 128-129`; `store/animation.py:43-61`).

## Scope
- `export-runtime --slices` writes `slices.json`: `{record_type: "runtime_slices", schema_version: 1, catalog_id, release_id, entries: [{visual_key, detail?, slices: [{name, keys: [{frame, x, y, w, h, center?, pivot?}]}]}]}`. Only sources that have slices; sorted by key and detail; newest source revision, as animation does; size bound `MAX_MANIFEST_BYTES`.
- **Coordinates are in the exported artifact's pixels** (planner decision): multiply source pixels by the artifact's build scale (the `scale_class` -> `scale` of `build/exportconfig.py`); refuse with a clear error if the scale cannot be resolved. Coordinates are relative to the image, never to an atlas sheet (say so in store_contract.md next to the atlas section).
- Without `--slices` the export is byte-identical to today; with it, the runtime manifest is unchanged.

## Out of Scope
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no gate result moved, no new art, no `.github/` change, no other `frontend/` file.
- No registry (`catalog/registry`), `ArtifactRecord` or runtime-manifest field: slices live per source revision, so the registry budget (90% used, budgets.md standing rule) is not touched.
- Git LFS, raising any existing bound, client use of atlases/animation/slices, a self-hosted runner.

## Acceptance Criteria
- [ ] A fixture source with two slices (one 9-slice, one pivot) round-trips to `slices.json` with scaled coordinates, checked against hand-computed values.
- [ ] Export without the flag byte-identical; export twice byte-identical.
- [ ] Planted: unresolvable scale refused, output left absent.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`
- Needs: `TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/research_asset_pipeline.md` (section 8, practice row 12, recommendation 5: pivot and 9-slice fields before UI-panel or animated assets)
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/` (the pattern this batch copies)

## Related Code Areas
- `visual_assets/store/{runtime_export,cli,animation}.py`, `visual_assets/store/build/exportconfig.py`, `tests/visual_assets/store/unit/test_runtime_export.py`

## Assumptions / Open Questions


## Implementation Notes
`runtime_slices_bytes` in `store/slices.py` (scale from the export config, cross-checked against the artifact record's size), flat `RuntimeSliceKey` contract, `--slices` flag, `slices_scale_unresolved` refusal, store_contract section.

## Test Summary
8 unit tests in `test_runtime_slices.py`; 6 mutants all caught (width/height checks needed an extra test).

## Files Changed
`visual_assets/store/{slices,runtime_export,cli}.py`, `contracts/slices.py`, `test_boundaries.py`, `store_contract.md`, tests, staging artifacts.


## Completion Summary

