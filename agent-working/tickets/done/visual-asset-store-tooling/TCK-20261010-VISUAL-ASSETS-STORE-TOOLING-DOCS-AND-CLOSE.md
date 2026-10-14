---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE
phase: done
date: 2026-10-10
tags: [planning]
---

# TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE

## Title
Docs drift, handoff snapshots, the hardening epic's stranded staging artifacts, and batch close

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 9 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. Also: the hardening epic's research (`internal_gap_audit.md`, `research_asset_pipeline.md`) is still under `agent-working/staging_artifacts/` on main; it belongs in `agent-working/stored_artifacts/`.

## Scope
- Move the two hardening research files to `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (git mv, status historical).
- store_contract.md "Not built" list and budgets.md updated for what this batch built; parked list re-stated (LFS, slices/9-slice, client use).
- Refresh `docs/assets/session_handoff/` snapshots from the planner's handover; close the epic.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.

## Acceptance Criteria
- [x] No asset doc claims a built item is missing or vice versa (grep proof in the ticket: Implementation Notes).
- [x] Staging folder for the hardening epic gone from main; snapshots refreshed; epic closed.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
- **Moved:** the two hardening research files are in `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (status historical; commit `dedb16d9b`, tickets repointed); the empty staging folder left behind was removed, so nothing of the hardening epic remains in `staging_artifacts/`.
- **Drift fixed in `store_contract.md`:** the "Not built" list no longer says atlases and animation export are missing (they are built as opt-in exports that no client reads) and re-states what stays parked (Git LFS, slices, 9-slice and pivots, client use of atlases and animation, raising any bound, a self-hosted runner); the `export-runtime` row names `--animation`; the handoff-package note says intake now DERIVES animation metadata (the package still declares only `frame_count` and `tag_count`). Budgets: every row this batch added is `APPROVED 2026-10-10`.
- **Grep proof (run on the final tree):** 0 matches for "atlases and animation export", "is not part of the handoff package or checked by intake", "no atlas", "atlases are not built" and "animation export.*not built" across `docs/assets` and the ADR; 0 `| PROPOSED |` rows in `budgets.md`; the built items are stated: `export-runtime --atlas` (3 files), `--animation` (1), `visual-assets-aseprite-local` (5), `visual-assets-bundle-capture` (4), the D10 addendum (1), D24 (6). `m0_discovery_result.md` keeps its dated historical line (atlas "routed ... later") on purpose.
- **Snapshots:** `docs/assets/session_handoff/asset-implementer.md` and `asset-planner.md` refreshed from the live handovers (2026-10-10).
- **Closure:** all nine children and the epic closed by hand (no `Workflow` pipeline) with `--path-reason batch_hand_close`, the asset precedent per asset-planner; `done_checker_static` per ticket and the mechanism-registry advisory run.

## Test Summary
- `tests/visual_assets` 2330 passed (whole suite, proof-record tests included); `tests/docs` 69 passed, 2 skipped, 1 xfailed; `tests/static` 83; `tests/architecture` 127; `tests/unit/tools` 674; `tests/tools` 4755 passed, 54 skipped, 1 xfailed, **1 failed: `test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path`**, environmental and not caused by this batch (it fails identically on the main checkout; two project memory directories from the `~/Work` move; nothing under `tools/` for it changed; not fixed, nothing deleted; the planner raises it with the owner). Frontend `vitest run src/visualAssets` 279 passed; `tsc -p tsconfig.app.json` and ESLint clean on the new files.

## Files Changed
`docs/assets/store_contract.md`, `docs/assets/session_handoff/{asset-implementer,asset-planner}.md`, `docs/REGISTRY.yaml`; the ticket moves and monitoring records of the closure; the research move is in `dedb16d9b`.

## Completion Summary
The asset docs state what the store-tooling batch built and what stays parked, the hardening research lives in `stored_artifacts` as history, both handover snapshots are current, and all ten tickets are closed. One environmental `tests/tools` failure remains, unrelated to this batch. The PR is pending the user's authorization.

