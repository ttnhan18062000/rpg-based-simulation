---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL
phase: open
date: 2026-10-10
tags: [architecture, testing, mcp]
---

# TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL

## Title
The drawing tool makes slices (name, rect, optional 9-slice centre and pivot) and the handoff declares them

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`. Owner chose store + drawing tool (2026-10-10). The Lua bridge has `newTag` (`ops.lua:282`) and reports tags (`:357-365`) but no slice code; the handoff declares only `frame_count`/`tag_count` (`contracts/handoff.py:65-68`, `drawing/handoff.py:117`).

## Scope
- New drawing operation (through the existing ops path, e.g. an `apply_ops` op kind; implementer's choice, planner approves the shape before code): make or replace one named slice with bounds, optional centre, optional pivot. Lua: `spr:newSlice(Rectangle)`, `.name`, `.center`, `.pivot`. One key per slice (all frames); per-frame keys stay out of scope.
- The tool validates with the SAME rules as the store (names, bounds, centre, pivot) and the same limits: drawing `MAX_SLICES` equals store `MAX_SOURCE_SLICES` (16), with a parity test like the `MAX_FRAMES` one.
- `inspect` (and the handoff package) report slices; the handoff declares `slice_count`; intake refuses a handoff whose declared count differs from what the parser reads (new quarantine code).
- The new revision is immutable and takes `base_revision`, like every other edit.

## Out of Scope
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no gate result moved, no new art, no `.github/` change, no other `frontend/` file.
- No registry (`catalog/registry`), `ArtifactRecord` or runtime-manifest field: slices live per source revision, so the registry budget (90% used, budgets.md standing rule) is not touched.
- Git LFS, raising any existing bound, client use of atlases/animation/slices, a self-hosted runner.
- Deleting slices, per-frame slice keys, slice user data.

## Acceptance Criteria
- [ ] Op shape approved by the planner before code.
- [ ] An agent-drawn sprite with one 9-slice and one pivot slice passes `export_handoff` -> intake -> adoption (in a test store) and the stored `SourceRecord.slices` matches what was requested.
- [ ] Bad requests refused by the tool before Aseprite runs; declared/parsed count mismatch refused at intake.
- [ ] Real-Aseprite drawing test (`needs_aseprite`) passes locally.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`
- Needs: `TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/research_asset_pipeline.md` (section 8, practice row 12, recommendation 5: pivot and 9-slice fields before UI-panel or animated assets)
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/` (the pattern this batch copies)

## Related Code Areas
- `visual_assets/drawing/**` (ops.lua, handoff.py, config.py, MCP server tool table), `visual_assets/store/contracts/handoff.py`, `visual_assets/store/intake/`

## Assumptions / Open Questions
- `drawing/**` is in the proof record's guarded set; child 4 re-runs the record once.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

