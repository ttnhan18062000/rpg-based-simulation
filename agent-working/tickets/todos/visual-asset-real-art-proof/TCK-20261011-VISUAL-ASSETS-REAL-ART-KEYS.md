---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS
phase: open
date: 2026-10-11
tags: [architecture, documentation]
---

# TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS

## Title
Real-art proof: register three optional keys (ui.panel_frame, fx.selection_ring, fx.campfire) and refresh the session_handoff snapshots

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 1 of `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`. The three proof sources need registered keys before intake can accept them; the merged handoff snapshots are stale.

## Scope
- Add the three keys to `visual_assets/catalog/definitions/visual_keys.yaml` with a header comment naming this ticket. Exactly the fields existing optional keys use (`family`, `description`, `variant_axes: []`, `optional: true`, `safety_class`, `fallback`); no `detail`, no label (labels are icon-only), no new field.
Three new `optional: true` keys (planner decision; the owner may overrule):
  - `ui.panel_frame`: 24x24, 1 frame, one slice `panel` with a 9-slice centre (8x8 at 8,8): a HUD panel border; `safety_class: decorative`, `fallback: {kind: "none"}`.
  - `fx.selection_ring`: 32x32, 8 frames, tag `pulse`, one slice `anchor` with a pivot at the centre: the selected-unit ring; `decorative`, `fallback: {kind: "none"}`.
  - `fx.campfire`: 64x64, 16 frames (= `MAX_ANIMATION_FRAMES`), tag `burn`, one slice `base` with a pivot on the bottom row: the heaviest realistic animated source we would draw; `decorative`, `fallback: {kind: "none"}`.
- Measure the registry before and after (bytes and load time, the method of `budgets.md`'s `MAX_REGISTRY_BYTES` row) and put both numbers in the ticket; child 4 copies them into budgets.md.
- Refresh BOTH `docs/assets/session_handoff/asset-implementer.md` and `asset-planner.md`: PRs #480/#487/#499 merged, current rc rc-0008, this batch in flight.
- **Gate (asset-planner): send the key text for review before committing.**

## Out of Scope
- No store (`visual_assets/store/**`) or drawing-tool (`visual_assets/drawing/**`) code change is planned. If the pipeline cannot carry real art, STOP and report to `asset-planner`: a code change becomes its own ticket on the owner's answer.
- **No bound changes** (lead-planner condition 1, 2026-10-11): if real art exceeds any bound, STOP and raise it as its own owner question; do not shrink the art to fit, and do not edit a bound or a test to pass.
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no client use of animation/slices/atlases, no gate result moved, no `.github/` change, no `frontend/` file.
- No new registry schema field (`MAX_REGISTRY_BYTES` budget review is the first step of the NEXT batch, not this one); keys only.
- Git LFS, raising any bound, a self-hosted runner: this batch only produces the evidence for them.

## Acceptance Criteria
- [ ] The registry loads; the existing registry and definition tests pass; rc-0008 verifies unchanged (optional keys need nothing in a release).
- [ ] Before/after registry bytes and load time recorded.
- [ ] Both snapshots match the current state.

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF`

## Related Docs
- `docs/assets/store_contract.md` (animation, slices, atlas sections; "Not built" parked list), `docs/assets/budgets.md`, `docs/assets/drawing_tools.md`, `docs/assets/pixel_art_technique.md`, `docs/architecture/visual_asset_foundation_adr.md` (D2 no Git LFS, D10 local proof record, D24, D25)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/`, `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS/` (what this batch proves on real art)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/store/contracts/definitions.py` (read), `docs/assets/session_handoff/*`

## Assumptions / Open Questions
- `fx`/`ui` are new family names on optional keys only (no schema change, no client use). If the owner reads this as the parked "other asset kinds", fall back to proof keys under an existing family; ask before committing if unsure.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

