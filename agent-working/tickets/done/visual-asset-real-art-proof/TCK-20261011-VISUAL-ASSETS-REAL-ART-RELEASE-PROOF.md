---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF
phase: done
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF

## Title
Real-art proof: build, rc-0009 (70 + 3) on the owner's answer, export-runtime --atlas --slices

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. Proves the release and runtime-export half of the pipeline on real art.

## Scope
- `build` the three adopted sources; record artifact PNG bytes and dimensions against `MAX_PNG_FILE_BYTES` / `MAX_DECODED_BYTES`.
- **Owner-only step:** ask the owner (blocking question) to approve assembling rc-0009 = rc-0008's 70 entries + the 3 new ones. Assemble only on that answer (rc-0005/0007/0008 precedent).
- rc-0008's 70 entries must be byte-identical in rc-0009 (the agent may build and release; adopt/adopt-set/revoke stay with the owner).
- `export-runtime --atlas --slices` on rc-0009: record the runtime manifest, `slices.json` and each atlas sheet's bytes and dimensions against `MAX_MANIFEST_BYTES` / `MAX_ATLAS_DIM`; check `slices.json` coordinates by hand against the source slices times the build scale; export twice -> byte-identical.
- State the frame-1 fact: the released artifact of each animated source is its first frame; the animation metadata carries the durations and tags.

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] rc-0009 released on the owner's answer; `verify` passes; rc-0008 entries byte-identical.
- [ ] Runtime export with atlas and slices: hand-checked coordinates, two runs byte-identical, sizes recorded.
- [ ] Any bound exceeded -> stopped and reported, not worked around.

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`
- Needs: `TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS` (owner adopted)

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `visual_assets/store/{cli,release,runtime_export,atlas,slices,animation}.py` (used), `visual_assets/store/build/**` (used), `visual_assets/catalog/**`

## Assumptions / Open Questions
- If the owner declines rc-0009, the export proof runs on a local, uncommitted release and the ticket says so.

## Implementation Notes
- `build` of the three sources (own Aseprite run, 4 GB memory cap): `ui_panel_frame--x1` 234 B PNG 24x24, `fx_selection_ring--x1` 294 B 32x32, `fx_campfire--x1` 1,060 B 64x64 (against `MAX_PNG_FILE_BYTES` 4,259,840 and `MAX_DECODED_BYTES` 4,198,400, each is far smaller). FRAME-1 FACT: the build exports frame 1 only (`build/exportconfig.py:53`), so the released artifact of the ring and the campfire is their first frame; the durations and tags travel in the animation metadata (`export-runtime --animation`). Recorded as a fact for activation, not changed (backlog ticket `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY`, not part of this batch).
- Owner answer (2026-10-11, blocking question with the facts: rc-0008's 70 byte-identical + 3 = 73, frame 1 only, this candidate fixes the 12 red tests): "Assemble rc-0009". `release --catalog-id pilot` -> `pilot/rc-0009: 73 entries`, 12,238 B (`MAX_MANIFEST_BYTES` 524,288). rc-0008 untouched (`cmp` against a copy taken before); all 70 rc-0008 entries equal their rc-0009 entry; the new entries are exactly `fx.campfire`, `fx.selection_ring`, `ui.panel_frame`; `store verify` ok. New guard: `tests/visual_assets/test_rc_0009_extends_rc_0008.py`.
- `export-runtime --catalog-id pilot --release-id rc-0009 --atlas --slices` (twice into new directories, `diff -r`: byte-identical): runtime manifest 18,505 B (73 entries; `MAX_MANIFEST_BYTES`), `slices.json` 512 B, five atlas sheets (`MAX_ATLAS_DIM` 1024): border 172x20 (257 B PNG, 1,855 B JSON), fx 103x68 (761 B, 591 B), icon 725x28 (2,884 B, 6,109 B), terrain 476x20 (3,435 B, 4,317 B), ui 28x28 (170 B, 432 B); 85 files, 58,738 B in all. A third export with `--animation` adds `animation.json` 475 B.
- Hand check of `slices.json` against the sources (build scale x1, so source pixels = exported pixels): `fx.campfire` `base` 0,0 64x64 pivot (32,63) = the source slice (pivot on the bottom row); `fx.selection_ring` `anchor` 0,0 32x32 pivot (16,16); `ui.panel_frame` `panel` 0,0 24x24 centre 8,8 8x8. Each has one key at frame 0. Atlas placement checked by hand against `gutter` 1 + `extrude` 1: the margin is 2 and the gap between sprites 3: `fx.campfire` at (2,2), `fx.selection_ring` at (69,2) (2+64+3), sheet 103x68 (2+64+3+32+2 by 64+4); `ui.panel_frame` at (2,2), sheet 28x28. The tests read each atlas rectangle back and compare it with the artifact pixels.
- `animation.json`: `fx.campfire` 16 x 80 ms, tag `burn` 0..15 forward; `fx.selection_ring` 8 x 100 ms, tag `pulse` 0..7 forward; `ui.panel_frame` has none.
- The 12 red tests (`test_atlas.py` 5, `test_release_byte_reproducibility.py` 7) are re-pointed from rc-0008 to rc-0009 (the pin in `test_release_byte_reproducibility.py`, `export_runtime(... "rc-0009")` and the CLI calls in `test_atlas.py`, the atlas families now `border fx icon terrain ui`, 73 entries, 10 atlas files). Nothing weakened. `adopted_facts.py` gains `RC_0009_ENTRIES`, `PROOF_KEYS`, `PROOF_GENERATED`, `rc-0009.json`; the two icon candidate tests accept rc-0009 next to rc-0008. Asset-planner's child-2 nits folded in: the animation and slice guard tests renamed `..._only_the_proof_sources_*`, `adopted_facts` imported at module level, `== af.REVISION_COUNT`, and the exact proof-art metadata pinned (`PROOF_ANIMATION`, `PROOF_SLICES`).
- No bound was exceeded and none was changed; no store or drawing code changed.

## Test Summary
`tests/visual_assets` (project venv): all green after the re-point except `test_the_guarded_files_still_match_the_committed_record`, which is expected until the local Aseprite proof record is re-run once, as its own commit, after the last guarded change (see Completion Summary).

## Files Changed
- `visual_assets/catalog/generated/{ui_panel_frame,fx_selection_ring,fx_campfire}--x1/`, `visual_assets/catalog/manifests/candidates/pilot/rc-0009.json`
- `tests/visual_assets/adopted_facts.py`, `tests/visual_assets/test_rc_0009_extends_rc_0008.py` (new), `tests/visual_assets/store/unit/test_atlas.py`, `tests/visual_assets/test_release_byte_reproducibility.py`, `tests/visual_assets/test_icon_set_adoption.py`, `tests/visual_assets/test_icon_v2_keys.py`, `tests/visual_assets/store/unit/test_animation_metadata.py`, `tests/visual_assets/store/unit/test_slice_metadata.py`

## Completion Summary
Built the three artifacts, assembled `pilot/rc-0009` (73 = rc-0008's 70 byte-identical + 3) on the owner's answer, proved `export-runtime --atlas --slices` (two runs byte-identical, slice coordinates and atlas placement hand-checked), re-pointed the 12 red tests from rc-0008 to rc-0009 without weakening, re-ran the local Aseprite proof record last. Commits `a28282206`, `96ca645f9`.
