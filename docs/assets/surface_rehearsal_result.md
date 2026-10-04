---
status: active
layer: frontend
authority: P2
audience: agent
date: 2026-10-04
tags: [live-map, rendering, testing, architecture]
---

# AM-M5 surface compatibility rehearsal: result record

Two dated results: **2026-10-04** (the terrain pilot role, `terrain.forest`; this section) and, below it as history, the unchanged **2026-10-03** synthetic-fixture result.
Plan: `docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md`; gates: the proposal's gate table.

## Result 2026-10-04: terrain pilot role

Ticket `TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER`. Every check below was run on one clean commit, **`401921bdd165722712a63a2dc5be3204ca2d73e4`** (tree clean before and after), isolated and local: the
normal Live Map, HUD and simulation are untouched, `AM-M6` execution and `AM-M7` stay dormant, nothing is activated. Role: one 16-pixel Live Map terrain cell (Forest, `terrain.forest`,
`docs/assets/pilot_terrain_key.md`); criteria were predeclared before the scene existed (`docs/assets/pilot_terrain_m5_criteria.md`); details: `docs/assets/pilot_terrain_m5_results.md`,
`docs/assets/retention_and_rollback.md`.

**Overall M5 classification: `INCONCLUSIVE`.** Not `PASS`, for two reasons. (1) The plan's own prerequisites are unmet: it requires `AM-M2` `PASS` and `AM-M4` `PASS`, and no result record for either exists.
(2) Six deliverables and gates are not `PASS` (`W05`, `W09`, `C05`, `C06`, `C07`, `C09`, all `INCONCLUSIVE`, reasons below). No gate was reworded to obtain a pass.

### Per deliverable (terrain role)

| ID | Result | Evidence and reason |
|---|---|---|
| `AM5-W01` | `PASS` | Map-only role (terrain cell); the HUD does not participate and is recorded as out of scope, not passed. Unchanged from 2026-10-03. |
| `AM5-W02` | `PASS` (map role only) | The pilot cell is drawn native 16 x 16, 1:1, smoothing off (`pilotScene.test.ts`: 49 forest cells draw the tile). In 4 browser runs the 30 clean forest cells hold exactly the export PNG's pixels (0 differing pixels) and the flat control equals the fill. |
| `AM5-W03` | `PASS` | Criteria C1-C5 committed first (`31eaf3f8b`); the owner reviewed captures at DPR 1 and 2 on 2026-10-04: all five `yes`. A single reviewer: an acceptance for this role, not a usability study. |
| `AM5-W04` | `PASS` for what exists | AM-U21 fallback = exactly the flat fill, tested for missing image, corrupt image, wrong-size image, still loading, late image, key absent from the manifest and invalid manifest, and shown in 4 browsers by failure injection. A non-Forest cell never gets the image. Animation and cache cases do not exist and are not claimed. |
| `AM5-W05` | `INCONCLUSIVE` | Colour-vision rule (predeclared) passes with the wording "better" (tile adds a luminance texture and is not less distinguishable than the flat fill beyond 2.0 dE). But the plan requires that no critical distinction is hue-only, and on the normal map terrain types **are** told apart by flat hue; the non-hue route is the hover text (`TILE_NAMES`), the real Live Map's, which this harness does not render, so it is claimed from source only. Under deuteranopia Forest and Desert mean colours are nearly identical (dE about 1) with the fill as well. No assistive technology was run. |
| `AM5-W06` | `PASS` | One immutable snapshot per mounted view; mid-load release switch drops the superseded release's late images (`rollbackDrill.test.ts`, `loader.test.ts`). Mutants "keep late completions" fail. |
| `AM5-W07` | `PASS` within the approved matrix | Matrix approved by the owner on 2026-10-04: Playwright Chromium and system Chrome, each at DPR 1 and 2. All four ran and passed (below). Firefox, Safari/WebKit, mobile and other platforms were not in the matrix and make no claim. |
| `AM5-W08` | `PASS` | `isolation.test.ts` now checks every fixture PNG (rehearsal and pilot) by name and by its own bytes in the production bundle (Vite inlines small images as data: URIs); a mutant importing the pilot PNG fails it. `git diff` against the base of this batch (`54ce9db4c`) is empty over `src/`, the Live Map app files, `vite.config.ts`, `index.html` and `package*.json`. Simulation truth and the mutation pipeline are untouched. |
| `AM5-W09` | `INCONCLUSIVE` | Satisfied by construction for the store: `gc` never deletes tracked state, so previous-release artifacts are protected (tested by the retained-release guard and mutants, `test_gc.py`; real catalog dry run on this commit lists only a local review export of the adopted intake and no tracked artifact). Supported-client roots are a deployment fact under Profile A, not modelled. Gate wording unchanged. Reclassify to `PASS` only if the owner explicitly accepts the narrowed definition (asked at charter signing). |

### Per gate

| Gate | Result | Evidence and reason |
|---|---|---|
| `AM-C05` Release consistency | `INCONCLUSIVE` | One immutable snapshot per view and no mixing across a release switch (W06). Not exercised: the client bootstrap/build binding of a real deployment (that is `AM-M6`), caches, tabs, workers, offline states. |
| `AM-C06` Compatibility/rollback and recall | `INCONCLUSIVE` (was `BLOCKED`) | Now exists: a previous-release fixture (the rehearsal export), a named rollback/recall owner (nhan, to be confirmed at charter signing) and a harness drill of new/old client and release, a recall and a mid-load switch. Still absent: a real old client build, a real rollback or recall procedure, an exercised recall authority. The old-client + new-release case is defence in depth against a mis-deploy, not a normal path. |
| `AM-C07` Accessibility/failure preservation | `INCONCLUSIVE` | `AM-U21` is now defined and tested: the preserved fact (terrain type) survives every injected failure as the flat fill. Assistive-information equivalence is not established (see W05: hover text not exercised, no assistive technology, one reviewer). |
| `AM-C09` Retention/garbage collection | `INCONCLUSIVE` (was `BLOCKED`) | Same as W09. Retention bound approved (30 days, local intakes only). |

### Checks run on `401921bdd` (all pass)

- `pytest tests/visual_assets tests/docs tests/architecture tests/static`: 1457 passed, 2 skipped, 1 xfailed (2 GB cap). `visual_assets.store audit`: chain ok; `verify`: store ok; `export-runtime --catalog-id pilot --release-id rc-0001` reproduces candidate hash `sha256:4f5eb10f...2e42` and registry hash `sha256:07f5d265...1133`, and the committed frontend fixture equals it.
- Frontend: `vitest run` 117 passed (13 files, including isolation and the rollback drill); scoped `eslint` and `tsc` clean; `npm run build` passes. Whole-project `eslint .` still has 18 errors in existing app files this batch does not touch.
- Local captures (not committed, gitignored): pilot page, 16 tests passed: Playwright Chromium headless shell 148.0.7778.96 (a cached older build; the build Playwright expects is not installed) at DPR 1 and 2, and system Google Chrome 151.0.7922.71 at DPR 1 and 2; each: 30 clean forest cells, 0 tile differing pixels, 0 flat differing pixels. The 2026-10-03 rehearsal page also re-passed (8 tests, Chromium 148, DPR 1, three fixture cells identical).
- Not run: Firefox and any other client; an assistive technology; a real deployment, old client build or recall.

### Known gaps stated

- Everything above is a harness result for one role on one machine; it is not an `AM-M6` pilot and authorizes nothing. `AM-M6` execution stays `NO-GO` until the owner signs a charter (`docs/assets/pilot_charter_am6.md`, DRAFT) and gives a new explicit authorization.
- M1 contract items remain open as the runtime README lists them, and no M2 or M4 result record exists.


## History: the 2026-10-03 result record (text unchanged apart from heading levels)

Ticket `TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL`; plan `docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md`;
gate definitions: the proposal's gate table (`docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md`).
Authorized by the user on 2026-10-03: an isolated rehearsal on synthetic fixtures, normal Live Map, HUD and simulation untouched, `AM-M6`/`AM-M7` dormant.

**Overall M5 classification: `INCONCLUSIVE`.** Not `PASS`: two gates are `BLOCKED` (no inputs exist to run them) and two are `INCONCLUSIVE`
(partial evidence). The rehearsal passes neither `AM-C10` nor any renderer-selection gate, and it makes **no art claim**: the three images are
synthetic shapes (a diamond, a disc, a hollow frame) chosen to be told apart by shape.

### What was built and where

`frontend/src/visualAssets/` (nothing in the normal app imports it): `manifest.ts` (strict parser, JSON with duplicate-key detection), `resolver.ts`
(pure `resolveVisual`), `fallback.ts` (typed per-family glyph + letter), `loader.ts` (single-generation loading), `scene.ts` and `RehearsalHarness.tsx`
(one native 16 x 16 cell per key plus a predeclared crowded 12 x 8 scene, 1:1, smoothing off), `rehearsalMain.tsx` with the dev-only page
`frontend/rehearsal.html` (`?inject=missing|corrupt|invalid`), and the committed synthetic export `__fixtures__/rehearsal/` (ticket 3). Tests are in
`frontend/src/visualAssets/__tests__/`. The local-only capture is `frontend/playwright.rehearsal.config.ts` + `rehearsal-capture/rehearsal.capture.ts`
(never in CI). Under Profile A (ADR D8) the resolver is client code bound to the manifest of its own build; there is no asset-only active pointer.

### Per deliverable

| ID | Deliverable | Result | Evidence and reason |
|---|---|---|---|
| `AM5-W01` | Participating-surface matrix | `PASS` | The rehearsed role is **map-only**: one 16-pixel cell (`CELL_SIZE`). The **HUD does not participate and is recorded as out of scope, not passed**; no HUD fallback, resolution or read-model alternative was built or tested. |
| `AM5-W02` | Applicable surface fixtures | `PASS` (map role only) | Three fixture keys drawn as native 16 x 16 cells (`harness.test.tsx`, `scene.test.ts`); in Chromium the three drawn cells are pixel-identical to the fixture PNGs (see W07 evidence). HUD-role fixtures: not applicable (HUD out of scope). |
| `AM5-W03` | Crowded composition | `INCONCLUSIVE` | The predeclared 12 x 8 scene (all three keys, two keys the release does not contain) is drawn, tested for layout and native-scale drawing, and captured (`crowded-scene*.png`, local). No human-readable criteria were applied and no reviewer outcome or budget exists, so "identifiable according to the existing criteria and budgets" cannot be claimed. A person looking at the capture could see the three shapes and the two `?` fallbacks; that is an observation, not a result. |
| `AM5-W04` | Fallback matrix | `PASS` for what exists | Missing image, corrupt/undecodable image (and an image of the wrong size), late image (superseded view) and invalid manifest each have a test and a typed fallback with the role glyph and letter (`resolver.test.ts`, `loader.test.ts`, `fallback.test.ts`, `scene.test.ts`, `harness.test.tsx`; shown on screen with `?inject=`). **Animation and cache cases do not exist in this rehearsal** (no animation, no persistent cache by design); they are not claimed. |
| `AM5-W05` | Accessibility checks | `INCONCLUSIVE` | Automated: no critical distinction is hue-only (the three images differ in alpha mask by 20+ pixels pairwise; the four fallback glyphs differ by shape, share two colours, and carry distinct letters; the letter has at least 3:1 contrast with what is under it, which a Chromium capture exposed as a defect for the hollow frame and which is fixed and tested); every cell has a text alternative (`aria-label` plus a visible text list) naming the role and the reason. **Not run:** an assistive technology, a colour-vision check, a reviewer, reduced/disabled-animation routes (no animation exists). |
| `AM5-W06` | Snapshot consistency | `PASS` | `loader.test.ts`: two snapshots with a different generation (`candidate_manifest_hash`) and completions in the opposite order; the older view's late completions are closed, recorded in `loader.dropped` and never reach the newer view (it holds only its own bitmaps; the older view resolves `late_result_dropped`). Mutant "keep late completions" fails. |
| `AM5-W07` | Supported-client evidence | `INCONCLUSIVE` | Two environments ran: **jsdom** (`vitest run`, runs in CI) and **Chromium 148.0.7778.96 headless on Linux, device pixel ratio 1** (one local capture run, evidence below). **No supported-client matrix was predeclared**, so no client can be called "passes" or "explicitly unsupported" beyond these two observations; no other browser, version or device was run. |
| `AM5-W08` | Isolation proof | `PASS` | `isolation.test.ts`: no file of the normal app imports from `src/visualAssets`; `index.html`, `vite.config.ts` and `package.json` do not mention it and the config has no `rollupOptions` (Vite builds only `index.html`); the module imports nothing from outside itself but React (its `CELL_SIZE` is a copy, asserted equal to the app's); a real production Vite build into a temp directory contains no fixture PNG, no `visualAssets`/rehearsal/`runtime_manifest` text and no rehearsal page; `npm run build` output (`dist/`) checked the same way. Mutants (the app imports and uses the parser; the config also builds `rehearsal.html`) fail the test. `git diff 2cfa8ab1 --stat` over `src/`, `frontend/src/{App.tsx,hooks,components,constants,contexts,lib,types,main.tsx}`, `vite.config.ts`, `index.html`, `package*.json` is empty. No Python or simulation file changed: simulation truth and the authoritative mutation pipeline are untouched. |
| `AM5-W09` | Retention integration | `BLOCKED` | Needs M2's GC dry run repeated with M4 records, supported-client and rollback roots, in-flight work and evidence pins. None of those inputs exist (no M4 rehearsal records, no client roots, no rollback roots); `gc` is reachability-only and retention numbers are unset (`docs/assets/budgets.md`). Nothing was run. |

### Per gate

| Gate | Result | Evidence and reason |
|---|---|---|
| `AM-C05` Release consistency | `INCONCLUSIVE` | Passing parts: one immutable snapshot per mounted view; stale and out-of-order completions cannot contaminate it (W06). Not exercised: the client bootstrap/build binding of a real deployment (that is `AM-M6`, dormant), caches, tabs, workers and offline states (none exist here), and a predeclared client matrix. |
| `AM-C06` Compatibility/rollback and recall | `BLOCKED` | Not run. Rollback under Profile A is the normal reviewed deployment of a whole frontend release; no rollback/recall authority, supported-client range or retained release fixture exists, and there is no old client build to test against. |
| `AM-C07` Accessibility/failure preservation | `INCONCLUSIVE` | The declared critical fact (which role a cell shows) survives every failure the rehearsal injects (missing, corrupt, late, invalid manifest) without hue-only dependence, shown by automated tests and a Chromium capture. It cannot be established for assistive-information equivalence: no reviewer, no assistive technology run, and the per-role preserved-information contract (`AM-U21`) is undefined (the three roles are synthetic). |
| `AM-C09` Retention/garbage collection | `BLOCKED` | Same reason as `AM5-W09`. |

### Evidence

- Code and tests: the commit of this ticket; `npx vitest run` (frontend): all files pass, including the isolation test (it builds the production bundle into a temp directory); `npx eslint src/visualAssets` clean; `npm run build` (`tsc -b && vite build`) passes and `dist/` has no match for `visualAssets`, `rehearsal` or `runtime_manifest`.
- Mutants killed (each failed the named test): loader keeps late completions; duplicate JSON keys allowed; an unknown key triggers a lookup; cross glyph equals diamond; letter always dark; the app imports the parser (static check, and the build check when used); the config also builds the rehearsal page.
- Local capture (not committed; `frontend/e2e-artifacts/rehearsal/`, gitignored): run through `playwright.rehearsal.config.ts` with the cached Chromium 1223 headless shell (the Playwright version in `package.json` expects a newer build that is not installed; `REHEARSAL_CHROMIUM` points at the cached one). `evidence.json`: Chromium 148.0.7778.96, `devicePixelRatio` 1, generation `sha256:f38e4ee3dd84c7c0a87812d4f7330736f9e0f7e7f2b1e045fa7249e9f24e9802`, `identical: true`, `differingPixels: 0` for all three cells against the fixture PNGs; four spec tests pass (one capture and three failure injections). The capture was run twice: the first run's screenshot showed the role letter of the hollow-frame fallback invisible (dark on dark); that was fixed and a contrast test added before the second run.
- Not retained: a reviewer outcome, performance observations, and any other client.

### Known gaps stated

- The client does not recompute the `pixels-v1` hash after decoding; integrity under Profile A is the build plus the store's `verify` (ADR D9). The loader checks only that the decoded size matches the manifest.
- The harness mounts from files in the repository; it does not exercise how a real build would bundle or serve the assets.
- Readability of synthetic shapes is not an art or usability claim.
