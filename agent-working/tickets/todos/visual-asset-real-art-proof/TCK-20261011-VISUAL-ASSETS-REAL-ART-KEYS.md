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
INPROGRESS

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
- Keys added before `aliases: []` with a header comment; descriptions carry size, frame count and role only (slice geometry and names live on the SourceRecord; asset-planner review 2026-10-11). Lead accepted the `ui`/`fx` families.
- Registry measurement (7 in-process `load_registry` loads): before 28241 B, 62 keys, load min 0.042 s, median 0.045 s; after 29525 B, 65 keys, min 0.050 s, median 0.064 s. 29525 B is 6.4 % of `MAX_REGISTRY_BYTES` 458752. It does NOT change the realistic-maximum row in `budgets.md` (the ~90 % figure is the 1024-key worst case, and these keys add no field). The median change is load noise at this size, not a trend.
- FINDING: `runtime_export.py:87` refuses when `registry.file_hash != candidate.registry_hash` and `release.py:120` stamps the registry file hash into every candidate, so ANY registry edit (optional keys included) makes every older candidate unexportable until a new one is assembled. `verify` is unaffected. Not a rollback break (rollback redeploys the previous frontend build, `retention_and_rollback.md:40`). Asset-planner ruling (option B): keep one commit per ticket; the branch is red on the export tests below from this commit until child 3's rc-0009; child 4 records the sentence in `store_contract.md`.
- Registry-content pins moved to exact new values (62 -> 65 keys, key list incl. the three, `Counter` of (family, class)); the label pin stays 35; the three keys are also asserted optional, decorative, `fallback none`, no axis, no detail, no label.

## Test Summary
`tests/visual_assets` (project venv): 2427 passed after the pin updates; EXPECTED RED until rc-0009 (owner-gated), all `BuildError registry_mismatch` on an export of the committed rc-0008:
- `tests/visual_assets/store/unit/test_atlas.py`: `test_the_atlas_options_leave_the_per_file_export_and_the_manifest_unchanged`, `test_two_atlas_exports_are_byte_identical`, `test_every_key_of_rc_0008_reads_back_from_its_atlas_with_the_artifact_pixels`, `test_atlas_pngs_pass_the_chunk_allowlist`, `test_the_cli_flag_is_opt_in` (5; the planner counted 4, the fifth is the CLI test that exits 2 for the same cause).
- `tests/visual_assets/test_release_byte_reproducibility.py`: `test_two_exports_of_the_committed_candidate_are_byte_identical`, `test_no_exported_png_carries_a_chunk_outside_the_allowlist`, `test_the_allowlist_check_fails_on_a_planted_chunk[tIME|tEXt|iTXt|zTXt]` (4), `test_an_export_that_differs_by_one_byte_changes_the_tree_hash` (7).
Nothing else fails. Without the keys `test_atlas.py` passes 17/17.

## Files Changed
- `visual_assets/catalog/definitions/visual_keys.yaml`
- `tests/visual_assets/store/unit/test_registry.py`, `tests/visual_assets/test_key_usage.py`
- `docs/assets/session_handoff/asset-implementer.md`, `docs/assets/session_handoff/asset-planner.md`

## Completion Summary

