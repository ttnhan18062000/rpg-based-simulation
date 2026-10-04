---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE
phase: open
date: 2026-10-04
tags: [live-map, testing, architecture]
---

# TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE

## Title
Close the `AM-M5` gaps for the terrain role: crowded-scene criteria and review, supported-client matrix, preserved-information contract and colour-vision check

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The isolated M5 rehearsal (`docs/assets/surface_rehearsal_result.md`) left `AM5-W03` (no predeclared criteria, no
reviewer), `AM5-W05` (no colour-vision check, no reviewer, `AM-U21` undefined) and `AM5-W07` (no predeclared client
matrix) `INCONCLUSIVE`, and `AM-C07` `INCONCLUSIVE`. With a real terrain key (ticket 2) these can be closed for that one
role. Child 3 of `TCK-20261004-EPIC-VISUAL-ASSET-PILOT-READINESS`.

## Scope
- Harness (still isolated, `frontend/src/visualAssets/` + `frontend/rehearsal.html`): mount the real runtime-manifest
  export from ticket 2 alongside the synthetic fixtures; a crowded scene that places the real tile among the other
  terrain fills exactly as the Live Map draws them (copy of the fill colours, asserted equal to `TILE_COLORS`, like `CELL_SIZE`).
- `AM5-W03`: write the reviewer criteria **before** the review (e.g. the forest tile is identifiable as forest and
  distinct from Swamp/Mountain/Desert at 1:1; no seam in a repeat; entity and building markers drawn over it stay
  readable). Then ask the user to review the capture against them (blocking question) and record the answer.
- `AM-U21` for the terrain role: the preserved fact is the terrain type. Fallback = the current flat colour fill plus the
  existing hover text (`TILE_NAMES`). State it and test that every failure case shows the fill.
- `AM5-W05`: an automated colour-vision simulation (protanopia, deuteranopia, tritanopia) of the crowded scene, with a
  predeclared pass rule; note that terrain was already hue-only on the normal map and say whether the tile makes that
  better, the same, or worse. No assistive-technology claim unless one is actually run.
- `AM5-W07`: propose a supported-client matrix (planner suggestion: current Chromium and Firefox desktop, DPR 1 and 2)
  and **ask the user to approve it** before running; then run the local capture on each and record results per client.

## Out of Scope
- The normal Live Map, HUD, `src/`; retention and rollback (ticket 4); the M5 result record rewrite (ticket 5 does it).
- Any new art.

## Acceptance Criteria
- [ ] Criteria for W03 and the W05 pass rule are committed before the review/run that uses them (commit order shows it).
- [ ] The user's W03 review and W07 matrix approval are recorded with date and wording.
- [ ] Each client in the approved matrix has a recorded capture result; none is claimed that was not run.
- [ ] Tests show the terrain fallback (fill + hover text) for missing, corrupt, late and invalid-manifest cases.
- [ ] `isolation.test.ts` still passes: nothing in the normal app imports `visualAssets`; frontend `vitest`, `eslint`, `npm run build` pass.

## Related Tickets
- TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL (done), TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/surface_rehearsal_result.md
- docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (AM-U21, gate table)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL/

## Related Code Areas
- frontend/src/visualAssets/, frontend/rehearsal.html, frontend/playwright.rehearsal.config.ts, frontend/src/constants/

## Assumptions / Open Questions
- Firefox may not be installed for Playwright locally; if so, say so and ask the user to shrink the matrix rather than skip silently.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
