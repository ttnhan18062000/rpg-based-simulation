---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL
phase: done
date: 2026-10-03
tags: [architecture, mcp, testing, live-map]
---

# TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL

## Title
Visual assets after the foundation: licence-bound local Aseprite evidence, budgets, runtime manifest and an isolated AM-M5 surface rehearsal

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The user asked (2026-10-03) to continue on every item the foundation epic left open, in one PR. Decided by the user
the same day, through a blocking question each: deployment **Profile A** (ADR `D8`); **no signing** under Profile A (`D9`);
real Aseprite **local only**, licence review recorded (`D10`, `docs/assets/aseprite_licence_review.md`); budgets are
**measured, proposed, and approved by the owner in PR review**; and an **isolated `AM-M5` surface rehearsal** on synthetic
fixtures is authorized. `AM-M6` (activation) and `AM-M7` (migration) stay dormant: there is no adopted art and no
human-selected role, and each needs its own authorization.

The decisions themselves (D8-D10, the licence review, plan-package status notes) are planner-owned and land in the
planning commit. The children implement what follows from them.

## Scope
Tracks the child tickets in `SEQUENCE.md`. No direct implementation.

## Out of Scope
- `AM-M6` activation and `AM-M7` migration; any change to the normal Live Map (`GameCanvas.tsx`, `useCanvas.ts`), HUD or `src/`.
- Profile B, a bootstrap record, a signing scheme.
- Running Aseprite anywhere but the licence holder's own machine (D10).
- Any art decision or real adopted asset; the committed catalog stays at zero keys.
- More than one scale class, atlases, animation export.

## Acceptance Criteria
- [x] Every child in `SEQUENCE.md` is closed.
- [x] ADR D8-D10 and `docs/assets/aseprite_licence_review.md` match what was built.
- [x] Every bound in `visual_assets/` that was marked "provisional (U-05)" either carries an owner-approved value from `docs/assets/budgets.md` or is listed there as deliberately unset, with the reason. Every row `APPROVED 2026-10-04` by the owner (blocking question on PR #309; `MAX_SOURCE_BYTES` kept at 102400, D2 not reopened); retention is listed as unset with its reason.
- [x] The `AM-M5` rehearsal records a result per gate (`PASS` / `FAIL` / `BLOCKED` / `INCONCLUSIVE`) with its evidence, never a pass by default.
- [x] Boundary tests stay green: no `src/` <-> `visual_assets` import; the normal frontend path does not import the rehearsal code.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (done; PR #286, #299)
- Children: TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE, TCK-20261003-VISUAL-ASSETS-BUDGETS, TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST, TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL, TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK (added after the ticket 2 review)

## Related Docs
- docs/architecture/visual_asset_foundation_adr.md (D8-D10)
- docs/assets/aseprite_licence_review.md, docs/assets/store_contract.md
- docs/plans/visual-asset-management-runtime-integration/README.md, 05_surface_compatibility_rehearsal_plan.md, 06_bounded_activation_pilot_plan.md
- docs/plans/aseprite-mcp-pixel-art/README.md (U-02, U-05, U-14)
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (8.1, 9.1-9.3)

## Related Stored Artifacts
- None (epic).

## Related Code Areas
- visual_assets/, tests/visual_assets/, frontend/src/visualAssets/ (new), .github/workflows/test.yml, Makefile

## Assumptions / Open Questions
- The budget numbers are proposals until the owner approves them in PR review; the PR does not merge with unapproved numbers.
- `.github/workflows/test.yml`, `Makefile` and `tests/static/test_ci_step_summary_reporting.py` are also being changed by another session on branch `python-code-craft-gates`; keep this batch's edits to them small and local so a merge stays easy.

## Implementation Notes
Children, in order, all in `done/`, one commit each on branch `visual-asset-hardening-and-rehearsal` (the last two after planner reviews):
1. `TCK-20261003-VISUAL-ASSETS-LOCAL-ASEPRITE-EVIDENCE`: strict local real-Aseprite run, pin check, CI skip line, D10 guard.
2. `TCK-20261003-VISUAL-ASSETS-BUDGETS`: every bound measured and recorded as `PROPOSED` (`docs/assets/budgets.md`) with a parity test; the review found and fixed a real defect (per-type record size bounds, split PNG file bound).
3. `TCK-20261003-VISUAL-ASSETS-SANDBOX-TIMEOUT-LEAK`: a timed-out sandbox job killed only the outer bwrap; `kill_tree` now freezes and kills the whole tree (two review rounds found a stop race and an interrupt hang).
4. `TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST`: `RuntimeManifest`, `export-runtime`, a committed synthetic three-shape fixture.
5. `TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL`: the isolated `AM-M5` rehearsal; result `docs/assets/surface_rehearsal_result.md`, overall `INCONCLUSIVE`.
Still open and unfiled: owner approval of the budget numbers, `AM-M6`/`M7` (dormant), a predeclared client matrix, an M4 rehearsal for `AM5-W09`/`AM-C09`, rollback/recall authority for `AM-C06`.

## Test Summary
Final state of the branch: `tests/visual_assets` without Aseprite 979 passed, 202 skipped; `make visual-assets-aseprite-local` 202 passed, 0 skipped (run twice in a row after the sandbox fix); `tests/static tests/architecture tests/docs` 240 passed; frontend `npx vitest run` 11 files, 94 tests passed; `npm run build` passes. Details per child ticket.

## Files Changed
See the children. New top-level pieces: `docs/assets/{budgets,surface_rehearsal_result}.md`, `frontend/src/visualAssets/`, `frontend/rehearsal.html`, `tools/visual_assets_*.py`.

## Completion Summary
All five children are done. The batch makes the real-Aseprite evidence strict and local (D10), measures and proposes every bound (owner approval pending in PR review), fixes the record-size and sandbox-timeout defects found along the way, adds the runtime manifest and its export, and records an honest isolated `AM-M5` result (`INCONCLUSIVE`). Nothing is activated.
