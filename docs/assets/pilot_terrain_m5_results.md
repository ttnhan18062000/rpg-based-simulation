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

## Result 2026-10-06: the adopted terrain set (`pilot/rc-0005`)

Ticket `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`. Every check below ran on one clean commit, **`2c793286f81c907711a39a3fa84cdc3013ef7ef7`** (tracked tree clean before and after), isolated and local; nothing is activated and the normal Live Map, HUD and `src/` are untouched.
Scope widened from the forest to the whole set the owner adopted on 2026-10-05T18:17:03Z (22 terrain tiles and nine `border.*` masks, set adoption `sa-f4c541f25f112221`). The user approved `build`, the candidate `pilot/rc-0005` (34 slots, same registry as `rc-0004`) and its
fixture export by blocking question on 2026-10-06; the scene is drawn from that export (adopted art -> release -> client), not from the draft export. The rules are the ones predeclared in `pilot_terrain_m5_criteria.md` (`AM5-S`, `AM5-B`, `AM5-W03-SET` with C6) before any art or capture. Evidence: stored artifacts of this ticket
(`captures/<client>/` with the images and an `evidence.json` per client, `final_checks_*.txt`, `am5s_adopted_set.txt`).

### AM5-W03-SET: whole-map review: `PASS` (one reviewer)

The owner reviewed the captures (borders on and off, image and flat canvases, four clients) and answered one blocking question per criterion with the same neutral options in the same order (`Yes for all 23 terrains` / `No for some terrains` / `Unsure for some terrains`, no recommendation).
Verbatim answers: C1 identifiable `Yes for all 23 terrains`; C2 distinct `Yes for all 23 terrains`; C3 seamless `Yes for all 23 terrains`; C4 markers `Yes for all 23 terrains`; C5 quiet `Yes for all 23 terrains`; C6 borders (judged with borders on) `Yes for all 23 terrains`.
Per-terrain expansion: each of Floor, Wall, Water, Town, Camp, Sanctuary, Forest, Desert, Swamp, Mountain, Road, Bridge, Ruins, Dungeon Entrance, Lava, Grassland, Snow, Jungle, Shallow Water, Farmland, Cave, Volcanic, Graveyard is `yes` on C1 to C6 (no exception named). Rule: `PASS` only if all yes. One reviewer: an acceptance of the set for this role, not a usability study.

### AM5-W05: colour vision: gate stays `INCONCLUSIVE`; the predeclared rules `PASS`

- **`AM5-S` on the adopted set: `PASS`, wording "better"**: 23 tiles, 253 pairs, 1012 pair-visions, 0 fail S1, S2 holds for every tile and vision (lowest texture 5.36). **Read it honestly:** the tiles were re-tinted so each tile's mean equals its flat fill, therefore S1 holds
  by construction (`dE_tile` equals `dE_fill` within rounding): the PASS means "no worse than the flat fills" and nothing more; the tiles add only the texture cue. The flat-fill baseline is hue-only and not colour-vision safe. The closest pair-vision is **0.857 dE
  (Jungle / Lava, protanopia; the flat fills themselves are 0.784)**, so some terrains are nearly indistinguishable by mean colour under some vision types: a pass is not "every terrain is told apart". Fringes are outside `AM5-S`.
- **Pilot forest rule, unchanged**, run on each adopted forest slot (explicitly per slot; see the fragility note): plain `PASS`/"better" (normal 17.86 Grassland vs fill 18.52; protan 5.94; deutan 1.17; tritan 9.07: identical to the 2026-10-04 row), bush `PASS`/"better" (17.41, 5.89, 1.12, 9.75), tree `PASS`/"better" (18.29, 5.69, 1.33, 9.44);
  texture 5.15 to 6.18 everywhere. The forest slots of the `rc-0005` export are byte-identical to the pilot fixture's (tested).
- **Informational, not in any verdict:** forest bush/tree under the set rule: minimum `dE` of their mean to another terrain's tile mean is 4.29 / 3.75 (protan) and 1.51 / 1.60 (deutan); plain is the pilot's row above.
- **Why the gate stays `INCONCLUSIVE`, exactly:** the gate `AM5-W05` is not the colour-vision rule. The plan (`docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md`, row `AM5-W05`) says: "No critical distinction is hue-only; non-image and reduced/disabled-animation routes preserve declared information".
  `AM5-S` and the pilot rule check only one narrow thing (the tiles are not less distinguishable by colour than the flat fills), and both pass. The **unmet condition is "no critical distinction is hue-only"**: on the normal map the terrain types are told apart by their flat fill hue (the `TILE_COLORS` fills, which the tiles keep as their mean), and
  the declared non-hue route, the hover text `TILE_NAMES[code]`, belongs to the real Live Map, which this harness does not render, so it is claimed from source only and not shown by a run. In addition, for some pairs the fills are nearly indistinguishable by hue under some vision types (closest 0.857 dE, Jungle / Lava, protanopia; Forest / Desert about 1.5 under deuteranopia),
  nothing was run with assistive technology, and the reviewer is one person. Closing it needs a rendered non-hue route (the Live Map hover text exercised in a run, which is `AM-M6` work) and the owner's decision on the assistive-technology question; the rules were not changed to get there.
- **Known fragility, not fixed here:** `tests/visual_assets/pilot_colour_vision.py::tile_pixels()` takes the first PNG of the pilot export, which on this machine is the tree slot, so `python -m tests.visual_assets.pilot_colour_vision` prints the tree row; the per-slot rows above call `evaluate()` on each slot's pixels. **Update 2026-10-09 (`TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`): fixed.** The module moved to `visual_assets/review/pilot_colour_vision.py` and `tile_pixels()` now selects the slot by key and detail through `runtime_manifest.json` (default: plain), so its command prints the plain row; no row above changed.

### AM5-W07: client matrix: `PASS` within the approved matrix (2026-10-04), every client ran again

Playwright Chromium (headless shell 1223) 148.0.7778.96 and system Google Chrome 151.0.7922.71, each at device pixel ratio 1 and 2: 16 of 16 capture tests passed (per client: the whole-map capture and failure injection `missing`, `corrupt`, `invalid`). Per client the page reported 140 fringed cells; fringes changed 7144 pixels, all within 4 px of a cell edge, and 0 pixels in any cell centre;
the flat control is the fills only. Firefox, Safari/WebKit, mobile and other platforms are not in the matrix and make no claim. Command: `PILOT_CHROMIUM=<chrome-headless-shell path> npx playwright test -c playwright.map.config.ts` from `frontend/`.

### Fallback checks (tests, and failure-injection captures in the four clients)

- Each of the 22 non-forest terrain keys missing from the release: its cells show exactly its flat fill, every other cell its tile (loop over all 22, `mapScene.test.ts`).
- Forest: a missing `bush` (or `tree`) slot shows `plain`; a missing `plain` shows the flat fill (the role fallback) for cells that picked it, tiles for the others.
- Border masks: a missing mask (absent from the build, undecodable, or not in the release) gives today's hard edge: no fringe reported, drawn or counted, every cell still drawn, never a blank or broken cell (test; captures `map-image-missing.png` and `map-image-corrupt.png`, 0 transparent pixels). A missing inner-corner mask alone falls back to its two edges. Found and fixed on the way: the page first counted a fringe for cells whose mask image had failed to load (`borderRender.ts` now treats a variant as available only when its image is loaded).

### Rollback drill (`terrainsetDrill.test.ts`, AM5-W09 / `AM-C06`)

Previous release = the `rc-0004` export (forest only), new = the `rc-0005` export. Run: new client + new release (every cell a tile, fringes drawn); new client + old release (the 22 other keys unknown: flat fills, forest tiles, no fringe); old client (the pilot scene) + new release (reads only the forest key and ignores the other 31 slots);
new client + a recalled release (no entries: every cell its flat fill); no mixed snapshot (a view carries only its manifest's generation). Not run: none left in the set of clients that exist (no real old client build exists). `AM-C06` and `AM5-W09` stay `INCONCLUSIVE` for the reasons recorded on 2026-10-04 (no real deployment, rollback procedure or recall authority exercised).

### Unaffected checks, not rerun (with the reason)

`AM-U21` role contract text and its failure cases for the forest (the forest slots are byte-identical and `pilotScene.test.ts` still passes); `AM5-W06` snapshot consistency (loader unchanged, `loader.test.ts` still passes); `AM5-W01`/`W02`/`W04` for the pilot cell (the pilot scene, fixture and tests are untouched);
`AM5-W08` isolation (not unaffected: `isolation.test.ts` was updated on purpose for the 34 new fixture images and passes; production bundle and Live Map files unchanged); `AM-C05`, `AM-C07`, `AM-C09` (deployment, assistive technology and retention facts this harness does not model).

### Overall M5 classification: `INCONCLUSIVE` (unchanged)

Not `PASS`, for the 2026-10-04 reasons: the plan's prerequisites `AM-M2` and `AM-M4` have no `PASS` record, and `W05`, `W09`, `C05`, `C06`, `C07`, `C09` stay `INCONCLUSIVE`. This result improves the evidence for `W03` (whole set, six criteria) and `W07`, and changes no gate's status. No gate or criterion was reworded to obtain a pass; the charter draft needs no note.

