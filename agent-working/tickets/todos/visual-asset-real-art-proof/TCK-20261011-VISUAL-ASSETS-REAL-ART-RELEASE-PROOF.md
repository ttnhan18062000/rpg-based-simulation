---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF
phase: open
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF

## Title
Real-art proof: build, rc-0009 (70 + 3) on the owner's answer, export-runtime --atlas --slices

## Status
OPEN

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


## Test Summary


## Files Changed


## Completion Summary

