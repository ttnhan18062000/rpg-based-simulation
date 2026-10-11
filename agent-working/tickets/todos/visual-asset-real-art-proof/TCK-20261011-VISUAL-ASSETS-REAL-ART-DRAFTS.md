---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS
phase: open
date: 2026-10-11
tags: [architecture, testing, mcp]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS

## Title
Real-art proof: draw the three sources with the drawing tool, hand off, intake PASS, owner adopts

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. Real art, made through the same agent path every future sprite will use.

## Scope
- Draw the three sources with the `aseprite-pixel-art` MCP tools, following `docs/assets/pixel_art_technique.md` (palette discipline, outline, readable at 1x). Frames via the tools' frame support; tags; slices via the `set_slice` op (#499). Real art, not noise or fills: the point is a realistic size.
- `lint_sprite` clean (or each remaining finding justified), `export_handoff` (declares frame and slice counts), `submit_candidate`, store intake **PASS** for all three. Keep the review exports.
- Record per source: `.aseprite` bytes, dimensions, frames, tags, slices/keys, record sizes (`SourceRecord` JSON bytes, `IntakeResult` bytes), preview bytes and dimensions. Each against its bound (`MAX_SOURCE_BYTES`, `MAX_DIM`, `MAX_ANIMATION_FRAMES`, `MAX_ANIMATION_TAGS`, `MAX_SOURCE_SLICES`, `MAX_SLICE_KEYS`, `MAX_RECORD_BYTES`, `MAX_PREVIEW_BYTES`, `MAX_PREVIEW_DIM`).
- **Any bound exceeded -> STOP** (no shrinking the art to fit): report to asset-planner, who raises it as its own owner question.
- **Owner-only step:** ask the owner (blocking question, with the review exports) to `adopt` the three candidates. Record the answer and the adoption ids. The agent never runs `adopt`.

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] Three intake PASS results; the measurement table filled.
- [ ] The owner's adopt answer recorded (adopted, or what the owner asked to redraw).
- [ ] Planted: a handoff whose declared slice count disagrees fails intake (the existing check, run on this real art once).

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`
- Needs: `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `visual_assets/drawing/**` (used), `visual_assets/store/intake/**` (used), `visual_assets/drafts/`, `visual_assets/catalog/**`

## Assumptions / Open Questions
- A redraw the owner asks for is in scope (same keys); a different set of keys is not.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

