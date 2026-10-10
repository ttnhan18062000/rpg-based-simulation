---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE
phase: open
date: 2026-10-10
tags: [testing, observability]
---

# TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE

## Title
Repeatable visual evidence: capture the harness pages from a built bundle and commit a compact evidence record

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 8 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. surface_rehearsal_result.md:112,119: captures are gitignored and the harness mounts repo files instead of exercising a real build. Four Playwright configs exist at `frontend/` root, all local-only.

## Scope
- **Before code: the planner confirms with `rpg-planner` any change outside `frontend/src/visualAssets/**` and `frontend/rehearsal-capture/**`** (e.g. a new Playwright config, vite build input, package.json script); stop if not cleared.
- A capture run against `vite build` + `vite preview` (the built bundle) for the harness pages; asserts that every asset loads from hashed bundle URLs and that sampled pixels match the stored artifacts (pixel hashes).
- A compact committed evidence record (per page: URL hashes, sampled-pixel verdicts, browser version, commit) as `.json.txt` (the stored_artifacts `.json` ignore rule) or under docs/assets; screenshots stay gitignored.
- A make target; local only, like the rehearsal config.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- CI execution of the capture (needs a `.github/` change, not this batch). Moving any gate result.

## Acceptance Criteria
- [x] rpg-planner clearance recorded for any file outside asset-owned frontend paths.
- [x] Capture from the built bundle passes; a planted wrong asset fails the pixel check.
- [x] Evidence record committed from a real run.

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
- **Clearance (2026-10-10), recorded as relayed by asset-planner.** Two new frontend files outside the asset-owned paths, `frontend/vite.rehearsal-bundle.config.ts` and `frontend/playwright.bundle.config.ts`: owner decision, "Clear both" (blocking question asked by asset-planner). The OWNER decided because the rpg-planner seat was not live. The Makefile target `visual-assets-bundle-capture`: cleared by lead-planner (the Makefile is theirs) with four conditions, all met: (1) same shape as `visual-assets-aseprite-local`: its own `.PHONY` line, a one-line `##` help saying "Local only, CI never runs it" and naming this ticket, and a body that only delegates to `tools/visual_assets_bundle_capture.py` (no inline shell); (2) placed directly after `visual-assets-aseprite-local`; (3) NO new dependency (vite, vite preview and @playwright/test were already devDependencies; the capture uses the installed `/usr/bin/google-chrome` through `REHEARSAL_CHROMIUM`, no new browser channel); (4) output under `reports/visual_assets/bundle_capture/`, only the compact record `docs/assets/surface_rehearsal_bundle_evidence.json.txt` is committed (screenshots and the bundle are not).
- **Planner confirmation of the scope, with three conditions (2026-10-10):** pixel verdicts for the three `rehearsal.html` cells and asset-loading-only evidence for pilot, map, icons and draft, stated per page in plain words (the record's `pixel_verification` says `verified: ...` or `not_taken: asset-loading evidence only, no pixel verdict`; no gate result moves, the rehearsal stays INCONCLUSIVE); the in-browser `pixels-v1` hash proven equal to the Python one on known vectors; the drawn cell sampled at the page's own integer scale with smoothing off, and DPR pinned to 1.
- **The hash is a second implementation, so it is proven:** `frontend/src/visualAssets/pixelsV1.ts` (one implementation, imported by the spec and by the vitest). Vectors are written by Python (`tests/visual_assets/test_pixelhash_vectors.py`): the 3 committed rehearsal artifacts, a non-square 5x3, an alpha mix 4x2 and a 2x2 whose transparent pixels carry colour; a pytest keeps the committed `__fixtures__/pixelhash/vectors.json` equal to a fresh Python computation, and `__tests__/pixelsV1.test.ts` compares the TypeScript hash with every vector (9 tests). Mutants: keeping the colour of a transparent pixel fails 3 tests, dropping the NUL after the magic fails 6.
- **The capture (`frontend/rehearsal-capture/bundle.check.ts`):** per page it records that every image came from `/assets/<64 hex>-<hash>.png` of a committed fixture, that nothing came from the dev server (`/src/`, `/@vite`...), that nothing failed, and that no `<img>` is a data: URL. For `rehearsal.html` it reads each cell's canvas at its own integer scale (the top-left pixel of each scale x scale block, every block must be one colour: smoothing off), hashes the result with `pixelsV1Hash` and compares with the committed manifest's pixel hash. DPR is pinned to 1 in the config and asserted. The evidence is written BEFORE the assertions, so a failing run still leaves what it saw.
- **Deviations from the plan, for the planner:** (a) the spec is `bundle.check.ts`, not `bundle.capture.ts`: the existing `playwright.rehearsal.config.ts` matches `**/*.capture.ts` and would have run a bundle spec with no bundle. (b) `assetsInlineLimit: 0` in the bundle config: Vite inlines assets under 4 KiB as data: URLs and the 16 px fixtures are far smaller, so by default there would be no hashed image URL to check; the config forces them to be emitted. (c) The planted proof is orchestrated by the tool module (copy the bundle, change one pixel of one hashed PNG through the store's own PNG codec, preview that copy with `REHEARSAL_BUNDLE_PLANTED_DIR`, expect the same spec to FAIL), so the Playwright config only needs one env switch. (d) The record is refused when a capture-defining file is modified or untracked (it names the commit it ran on), as in the proof record of child 4.
- **Result of the first real run (commit `507bb4979`, Chromium 151.0.7922.71, vite 7.3.1, DPR 1):** all five pages loaded only hashed `/assets/<64 hex>-<hash>.png` images of committed fixtures (3, 3, 34, 53 and 7 images; none from the dev server, none inlined, none failed). `rehearsal.html`: the three cells (gem, rock, frame) drew exactly the stored artifacts' `pixels-v1` hashes at scale 1. Pilot, map, icons and draft carry NO pixel verdict, and the record says so per page. Planted proof: one pixel of the gem's hashed PNG changed in a copy of the bundle, the same capture FAILED on exactly `fixture.rehearsal.gem` and the other two cells stayed identical. The first real run of the make target also showed what a failing run looks like: its second (planted) Playwright run prints a failure by design, and the tool then writes the record.

## Test Summary
- `tests/visual_assets/test_bundle_capture_evidence.py`: the record's rules on 22 planted violations (an unhashed image, a non-fixture image, an inlined data image, a dev-server request, a failed request, a pixel verdict that is not identical, at the wrong scale or missing, pixel verdicts claimed for a page without them, a page that does not say it has none, a planted proof that was not caught or failed on the wrong image or changed a different file, a moved gate result, a HiDPI run, and shape errors), the planted one-pixel PNG (same size, exactly one byte one apart, different hash, for each of the 3 artifacts), the hashed-URL pattern, and the committed record (valid, a real commit and browser).
- `tests/visual_assets/test_pixelhash_vectors.py` (3) and `frontend/src/visualAssets/__tests__/pixelsV1.test.ts` (9): the TypeScript hash equals the Python one on all 6 vectors; two mutants of the TypeScript hash are caught (3 and 6 failing tests).
- Real run: `make visual-assets-bundle-capture` (see Implementation Notes). ESLint and `tsc -p tsconfig.app.json` are clean on the new files.

## Files Changed
`Makefile`, `frontend/vite.rehearsal-bundle.config.ts`, `frontend/playwright.bundle.config.ts`, `frontend/rehearsal-capture/bundle.check.ts`, `frontend/src/visualAssets/{pixelsV1.ts,__tests__/pixelsV1.test.ts,__fixtures__/pixelhash/vectors.json}`, `tools/visual_assets_bundle_capture.py`, `tests/visual_assets/{test_pixelhash_vectors,test_bundle_capture_evidence}.py`; with the record: `docs/assets/surface_rehearsal_bundle_evidence.json.txt`, `docs/assets/surface_rehearsal_result.md`.

## Completion Summary
The rehearsal harness pages are captured from the built bundle (hashed asset URLs) by a local-only make target, with a proven second implementation of the pixel hash, a pixel verdict for the three cells of `rehearsal.html` only (the other four pages are asset-loading evidence and say so), a planted one-pixel wrong asset that the same capture fails on, and the compact record committed from a real run. No gate result moves. The capture is not run in CI (that would need a `.github/` change, out of scope).
