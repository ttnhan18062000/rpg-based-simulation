---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE
phase: done
date: 2026-10-04
tags: [live-map, testing, architecture]
---

# TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE

## Title
Close the `AM-M5` gaps for the terrain role: crowded-scene criteria and review, supported-client matrix, preserved-information contract and colour-vision check

## Status
DONE

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
- [x] Criteria for W03 and the W05 pass rule are committed before the review/run that uses them (commit order shows it).
- [x] The user's W03 review and W07 matrix approval are recorded with date and wording.
- [x] Each client in the approved matrix has a recorded capture result; none is claimed that was not run.
- [x] Tests show the terrain fallback (fill + hover text) for missing, corrupt, late and invalid-manifest cases.
- [x] `isolation.test.ts` still passes: nothing in the normal app imports `visualAssets`; frontend `vitest`, `eslint`, `npm run build` pass.

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
Two commits, because the first acceptance criterion needs the criteria committed before the review: `31eaf3f8b` (criteria) then the build and results. The ticket's own wording "terrain/forest" is the real key `terrain.forest`.
Pilot page `rehearsal-pilot.html` + `PilotHarness`/`pilotScene`; the old rehearsal page and harness are unchanged. Real export committed as a fixture with an equality test. Details and traps: `investigation.md`.
Results: `docs/assets/pilot_terrain_m5_results.md`. W03 `PASS` (owner, all five criteria yes), W05 `PASS` by the predeclared rule (with the weak-baseline caveat stated), W07 approved matrix Chromium 148 + Chrome 151 at DPR 1 and 2, all four ran and passed; Firefox not in the matrix and not run.

## Test Summary
frontend vitest 111 passed; `eslint src/visualAssets rehearsal-capture playwright.pilot.config.ts` clean; `npm run build` ok; whole-project `eslint .` has 18 pre-existing errors in files this ticket does not touch. `pytest tests/visual_assets` passed (see below). Browser captures: 4 clients x 4 tests, 16 passed (local).

## Files Changed
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/pilot_terrain_m5_results.md (new), docs/assets/store_contract.md
- frontend/src/visualAssets/{pilotScene,pilotSource,PilotHarness,pilotMain}.ts(x), __fixtures__/pilot/, __tests__/pilotScene.test.ts; frontend/rehearsal-pilot.html, playwright.pilot.config.ts, rehearsal-capture/pilot.capture.ts
- tests/visual_assets/pilot_colour_vision.py, test_pilot_colour_vision.py, test_pilot_fixture.py

## Completion Summary
The terrain role's AM-U21 contract is defined and tested; W03, W05 and W07 have recorded evidence for the one pilot role. Nothing is activated; the normal Live Map is untouched. Ticket 5 re-classifies the M5 deliverables.
