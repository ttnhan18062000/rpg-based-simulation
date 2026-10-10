---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-EPIC-VISUAL-ASSET-SLICES
phase: open
date: 2026-10-10
tags: [architecture, planning]
---

# TCK-20261010-EPIC-VISUAL-ASSET-SLICES

## Title
Visual asset slices: named slices with 9-slice centres and pivots, read from sources, exported at runtime, made by the drawing tool

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner, 2026-10-10 (blocking questions, after PR #487 merged): next asset batch = slices, 9-slice centres and pivots, covering the store AND the agents' drawing tool; bounds approved: at most 16 named slices per source and at most 16 per-frame keys per slice; slice names follow the animation tag rule (1..32 chars, `BoundedText`). Today the store's `.aseprite` reader skips the slice chunk (0x2022) by its declared size (`visual_assets/store/intake/aseprite.py:245`), and the drawing tools cannot make a slice, so no source can carry one.

## Scope
- Child 1 `TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`: read, bound and validate the slice chunk; store it per source revision (`SourceRecord.slices`, absent = byte-identical old records); ADR D25 (owner approves the text); security review.
- Child 2 `TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT`: opt-in `export-runtime --slices` writes `slices.json` in artifact pixels.
- Child 3 `TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL`: a drawing-tool operation that makes a slice (with optional centre and pivot), the handoff declares `slice_count`, intake checks it.
- Child 4 `TCK-20261010-VISUAL-ASSETS-SLICES-DOCS-AND-CLOSE`: docs, parked lists, BOTH `docs/assets/session_handoff/*` snapshots, proof-record re-run, closure.

## Out of Scope
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no gate result moved, no new art, no `.github/` change, no other `frontend/` file.
- No registry (`catalog/registry`), `ArtifactRecord` or runtime-manifest field: slices live per source revision, so the registry budget (90% used, budgets.md standing rule) is not touched.
- Git LFS, raising any existing bound, client use of atlases/animation/slices, a self-hosted runner.

## Acceptance Criteria
- [ ] Children 1-4 DONE, each commit reviewed and approved by `asset-planner`.
- [ ] Owner approved the D25 text.
- [ ] One PR, pushed and merged only on the user's own answer (`--admin` merge run by the user).

## Related Tickets
- Previous batch: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING` (PR #487, `231e35f77`; animation metadata child is the pattern)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/research_asset_pipeline.md` (section 8, practice row 12, recommendation 5: pivot and 9-slice fields before UI-panel or animated assets)
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/` (the pattern this batch copies)

## Related Code Areas
- `visual_assets/store/intake/aseprite.py`, `visual_assets/store/contracts/{source,animation}.py`, `visual_assets/store/{animation,adoption,runtime_export,cli,config}.py`, `visual_assets/drawing/**`

## Assumptions / Open Questions
- Planner decisions recorded in `SEQUENCE.md`.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

