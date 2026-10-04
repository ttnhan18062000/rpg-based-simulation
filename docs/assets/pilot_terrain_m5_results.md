---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [mcp, live-map, testing]
---

# Pilot terrain role: `AM-M5` gap results (2026-10-04)

Results of `TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE` against the criteria predeclared in `docs/assets/pilot_terrain_m5_criteria.md` (commit `31eaf3f8b`, before
the scene existed). Role: `terrain.forest`, one 16-pixel Live Map terrain cell (`docs/assets/pilot_terrain_key.md`). Isolated, local, nothing activated; the normal
Live Map, HUD and `src/` are untouched. This page records what ran. Ticket 5 re-classifies the `AM5-W*` deliverables and gates in `surface_rehearsal_result.md`.

The scene is the predeclared 12 x 8 layout: 49 of its 96 cells are Forest (the criteria page said "half"; the formula is unchanged), 30 of them have no marker on or next to them.
Evidence is not committed (`stored_artifacts` ignores JSON, captures are gitignored); the numbers below are copied from it, and it is reproducible: W05 with `python -m tests.visual_assets.pilot_colour_vision`, the browser evidence (one `evidence.json` per client) with the Playwright command under W07, into `frontend/e2e-artifacts/pilot/`.

## AM-U21 (terrain role contract): defined and tested

Preserved fact = the terrain type; carried by the flat fill and the hover text; the image is decoration. Fallback = exactly the fill. `frontend/src/visualAssets/__tests__/pilotScene.test.ts`
proves the fill (and no image, glyph or other colour) for: image missing from the build, corrupt image, wrong-size image, image still loading, late image after the view was superseded,
key absent from the manifest, invalid manifest; and that a non-Forest cell never gets the image. The same cases ran in real browsers (failure injection `missing`, `corrupt`, `invalid`).

## AM5-W03: crowded scene review: `PASS` (one reviewer)

Reviewed by the owner on 2026-10-04 against the five predeclared criteria, on the image scene and the flat control at device pixel ratio 1 and 2: C1 identifiable `yes`,
C2 distinct `yes`, C3 seamless `yes`, C4 markers `yes`, C5 quiet `yes` (blocking question, answers recorded verbatim as `yes`). A pass means the owner accepts the tile for this role, not a usability study.

## AM5-W05: colour-vision check: `PASS` by the predeclared rule (result: "better")

CIE76 `dE` after Machado 2009 simulation (severity 1.0); `dmin` = smallest `dE` between the tile's (or the flat fill's) mean colour and Swamp, Mountain, Desert, Jungle, Grassland:

| Vision | `dmin` tile | `dmin` flat fill | P1 (tile >= fill - 2.0) | texture (L\* sd) | P2 (>= 2.0) |
|---|---|---|---|---|---|
| normal | 17.86 (Grassland) | 18.52 (Desert) | yes | 5.25 | yes |
| protan | 5.94 (Desert) | 5.02 (Desert) | yes | 5.38 | yes |
| deutan | 1.17 (Desert) | 1.46 (Desert) | yes | 5.15 | yes |
| tritan | 9.07 (Jungle) | 10.07 (Jungle) | yes | 5.22 | yes |

Read it honestly: P1 and P2 hold, so by the rule the tile is "better" (it adds a luminance texture a flat fill lacks) and no worse in mean colour. But the baseline is weak:
under deuteranopia the **mean** colours of Forest and Desert are nearly indistinguishable (`dE` about 1) with the flat fill too, and terrain on the normal map is already told apart by hue
alone. The tile does not fix that; it only does not make it worse and adds a texture cue. No assistive-technology claim: none was run.

## AM5-W07: client matrix: approved by the owner on 2026-10-04, every client in it ran

Approved matrix (blocking question): Playwright Chromium and the system Google Chrome, each at device pixel ratio 1 and 2. Firefox is **not** in the matrix and was not run (the system
Firefox is a snap build Playwright cannot drive; installing Playwright's Firefox was offered and declined). Per client, the capture test passed all 4 tests (native-scale capture; the 30 clean
forest cells equal the export PNG's pixels with 0 differing pixels and the flat control's equal the fill with 0; failure injection `missing`, `corrupt`, `invalid` leave the fill):

| Client | Version | DPR | Result |
|---|---|---|---|
| Playwright Chromium (headless shell; the build Playwright expects, 1234, is not installed, so the cached older 1223 build ran) | 148.0.7778.96 | 1 | pass |
| same | 148.0.7778.96 | 2 | pass |
| Google Chrome (system, headed channel `chrome`) | 151.0.7922.71 | 1 | pass |
| same | 151.0.7922.71 | 2 | pass |

Not covered: Firefox, Safari/WebKit, mobile, other platforms. Command: `PILOT_CHROMIUM=<chrome-headless-shell path> npx playwright test -c playwright.pilot.config.ts` from `frontend/`.
