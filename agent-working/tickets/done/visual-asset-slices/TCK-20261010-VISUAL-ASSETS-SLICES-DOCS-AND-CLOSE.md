---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICES-DOCS-AND-CLOSE
phase: done
date: 2026-10-10
tags: [architecture, documentation]
---

# TCK-20261010-VISUAL-ASSETS-SLICES-DOCS-AND-CLOSE

## Title
Slices batch: docs, parked lists, handoff snapshots, proof-record re-run, close

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 4 of `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`.

## Scope
- `docs/assets/store_contract.md`: slice section (record, export, coordinates); remove slices/9-slice/pivots from the parked list (keep the rest). `budgets.md` rows. ADR D25 as approved.
- Refresh BOTH `docs/assets/session_handoff/asset-implementer.md` and `asset-planner.md` (the merged ones still say "awaiting the user's push/PR decision").
- Re-run `make visual-assets-aseprite-local` ONCE, as its own commit, after the last store/drawing edit (guarded files committed first).
- Close the batch: `record_hand_orchestrated_closure.py --path-reason batch_hand_close` per ticket, `done_checker_static.py --ticket-id` PASS, folder moved to `tickets/done/visual-asset-slices/`, REGISTRY regenerated, `make knowledge-index-update`.

## Out of Scope
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no gate result moved, no new art, no `.github/` change, no other `frontend/` file.
- No registry (`catalog/registry`), `ArtifactRecord` or runtime-manifest field: slices live per source revision, so the registry budget (90% used, budgets.md standing rule) is not touched.
- Git LFS, raising any existing bound, client use of atlases/animation/slices, a self-hosted runner.

## Acceptance Criteria
- [x] Docs match the code; parked lists updated in store_contract.md and the snapshots.
- [x] Proof record fresh at the PR head (CI staleness test green).
- [x] All 5 tickets closed, done_checker PASS.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`
- Needs: `TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`, `TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT`, `TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL`

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`
- `docs/assets/session_handoff/*`, `docs/assets/aseprite_local_proof.json`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/research_asset_pipeline.md` (section 8, practice row 12, recommendation 5: pivot and 9-slice fields before UI-panel or animated assets)
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/` (the pattern this batch copies)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
Docs commit `5270c653b`; the proof re-run is its own commit `e03f08ded` after the last store/drawing edit (condition from asset-planner: rc-0008 must rebuild 70/70 identical with the new Lua pin: it did). origin/main merged before the final pass.

## Test Summary
Final pass on the merged tree (origin/main merged in): `tests/visual_assets` 2439 passed (proof-record tests included); `tests/docs` 69 passed, 2 skipped, 1 xfailed; `tests/static` 83; `tests/architecture` 127; `tests/unit/tools` 674; `tests/tools` 4723 passed, 54 skipped, 1 xfailed, **1 failed: `test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path`**, environmental (two project memory directories from the `~/Work` move), not caused by this batch, nothing deleted.


## Files Changed
`docs/assets/{store_contract,budgets,drawing_tools}.md`, `docs/assets/aseprite_local_proof.json`, `docs/assets/session_handoff/*`, ticket and monitoring bookkeeping.


## Completion Summary
Docs and parked lists updated, both session_handoff snapshots refreshed, the local Aseprite proof record re-run once after the last store/drawing edit (215 passed, rc-0008 rebuilt 70/70 byte-identical), all five tickets closed. Commits `5270c653b`, `e03f08ded`.
