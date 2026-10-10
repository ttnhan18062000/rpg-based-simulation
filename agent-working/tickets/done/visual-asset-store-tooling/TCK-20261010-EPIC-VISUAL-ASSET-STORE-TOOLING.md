---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING
phase: done
date: 2026-10-10
tags: [architecture, planning]
---

# TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING

## Title
Visual asset store tooling: lock and deletion log, faster decoder, byte-reproducible releases, local Aseprite proof, atlases, palettes, animation metadata, bundle evidence

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner, 2026-10-10 (blocking questions): next asset batch is store tooling only, and ALL four groups: release safety, evidence capture, palette as data, and the previously parked no-consumer items (real-Aseprite CI, atlases, faster decoder, animation fields). Then: reverse D18 (new D24: lock + deletion log), keep D10 with a committed local proof record, decoder stays pure Python.

## Scope
- Children, in order (see SEQUENCE.md):
  1. `TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG`
  2. `TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP`
  3. `TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY`
  4. `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`
  5. `TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT`
  6. `TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA`
  7. `TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`
  8. `TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`
  9. `TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE`

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Parked still: Git LFS, slices/9-slice/pivots, client use of atlases or animation, raising bounds, self-hosted runner.

## Acceptance Criteria
- [x] All nine children DONE and committed on one branch. (The single PR and its merge need the user's authorization and were pending at close; this box is ticked for the nine children, not for the merge.)

## Related Tickets
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
One branch (`visual-asset-store-tooling`, off `origin/main` 312fbd78c), one commit set per child, each reviewed by `asset-planner`; the owner's four decisions (relayed by asset-planner, 2026-10-10): "Approve as written" (D10 addendum), "Approve 1024" (`MAX_ATLAS_DIM`), "Approve 16 / 16" (`MAX_ANIMATION_FRAMES` / `MAX_ANIMATION_TAGS`), "Clear both" (the two frontend config files; the rpg-planner seat was not live); lead-planner cleared the Makefile target with four conditions.
| Child | Commits | What it delivered |
|---|---|---|
| 1 `STORE-LOCK-AND-DELETION-LOG` | `43ef881db` | store-wide write lock, hash-chained deletion log, kill-mid-publish tests, ADR D24 |
| 2 `PNG-DECODER-SPEEDUP` | `11ace7957` | faster pure-Python decoder, bounds unchanged |
| 3 `RELEASE-BYTE-REPRODUCIBILITY` | `835db787e` | rc rebuild byte check (local) and export-twice/chunk test (CI) |
| 4 `ASEPRITE-LOCAL-PROOF-RECORD` | `9a4083372`, `2e608382e`, `a90818a7e` | committed local proof record, runner, CI staleness test, ADR D10 addendum; refreshed once after the last store change |
| 5 `RUNTIME-ATLAS-EXPORT` | `de963439e`, `f2287f94e` | opt-in atlases; review fix: no decoded image held by the default export |
| 6 `PALETTE-AS-DATA` | `17d43c792` | palettes and GPL exports as drift-guarded data, advisory off-palette lint |
| 7 `ANIMATION-METADATA-FIELDS` | `5c4d34ff9`, `43469ba16` | animation metadata derived from the file, carried per revision, opt-in `animation.json`; security review found one real crash, fixed with regression proofs |
| 8 `EVIDENCE-CAPTURE-REAL-BUNDLE` | `507bb4979`, `dd3e46ac0` | capture from the built bundle, TypeScript `pixels-v1` hash proven against Python, planted-asset proof, local-only make target |
| 9 `STORE-TOOLING-DOCS-AND-CLOSE` | `dedb16d9b`, `b0ac744f8` and the closure | docs drift, snapshots, closure |
Decisions record: `7dbe534b6`. Lessons recorded in the tickets: run the whole `tests/visual_assets` suite after any fix (a `MAX_*` name in code needs a budgets row); a review finding is a claim to reproduce first; a test that passes with the fix reverted is weak.

## Test Summary
- `tests/visual_assets` 2330 passed (whole suite, proof-record tests included); `tests/docs` 69 passed, 2 skipped, 1 xfailed; `tests/static` 83; `tests/architecture` 127; `tests/unit/tools` 674; `tests/tools` 4755 passed, 54 skipped, 1 xfailed, **1 failed: `test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path`**, environmental and not caused by this batch (it fails identically on the main checkout; two project memory directories from the `~/Work` move; nothing under `tools/` for it changed; not fixed, nothing deleted; the planner raises it with the owner). Frontend `vitest run src/visualAssets` 279 passed; `tsc -p tsconfig.app.json` and ESLint clean on the new files.

## Files Changed
See the nine child tickets; nothing under `src/`, no registry or manifest change without a flag, no `.github/` change, no gate result moved.

## Completion Summary
All nine children are DONE and committed on one branch with the owner's four decisions recorded. The single PR and its merge are the user's decisions and were pending at close (the PR needs the user's authorization; the merge needs the user's `--admin`). One environmental `tests/tools` failure, unrelated.

