---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE
artifact_type: plan
tags: [architecture, testing]
---

# Plan (DESIGN ONLY, no code yet): evidence capture from the built bundle

Status: the file list outside asset-owned frontend paths is awaiting rpg-planner clearance via asset-planner. Nothing is written until it is cleared.

## What changes
Capture the rehearsal harness pages from `vite build` + `vite preview` (the real bundle: hashed asset URLs) instead of the dev server, assert every image the pages load comes from a hashed `/assets/<name>-<hash>.png` URL, sample pixels from the drawn canvases and compare them with the stored artifacts' pixel hashes, and write a compact evidence record. The harness already imports its fixtures with `import.meta.glob(... ?url)`, so a built bundle carries them as hashed assets; no harness source change is needed.

## Files I would touch OUTSIDE `frontend/src/visualAssets/**` and `frontend/rehearsal-capture/**` (all NEW; no existing file there is edited)
1. `frontend/vite.rehearsal-bundle.config.ts`: a separate Vite config (multi-page `build.rollupOptions.input` = the existing `frontend/rehearsal*.html` pages, `outDir` = `e2e-artifacts/rehearsal-bundle`). `frontend/vite.config.ts` and `index.html` are NOT edited, so the real app build is unchanged.
2. `frontend/playwright.bundle.config.ts`: a fifth local-only Playwright config next to the four existing ones (`webServer`: `vite build -c vite.rehearsal-bundle.config.ts && vite preview --outDir e2e-artifacts/rehearsal-bundle --port 5175 --strictPort`; `testDir` stays `./rehearsal-capture`, `testMatch` `**/bundle.*.capture.ts`).
3. `Makefile` (repo root): one new target `visual-assets-bundle-capture` (local only, like `visual-assets-aseprite-local`), no change to existing targets.
Not touched: `frontend/package.json` (no new script; the make target runs `npx`), `frontend/vite.config.ts`, the four existing Playwright configs, `.github/**`, `src/**`, any `src/` outside `visualAssets`. `e2e-artifacts/` is already gitignored by `frontend/.gitignore`. The existing ESLint glob (`**/*.{ts,tsx}`) will lint the two new config files like the existing four.

## Asset-owned files I would add
`frontend/rehearsal-capture/bundle.capture.ts` (the spec), `docs/assets/surface_rehearsal_bundle_evidence.json.txt` (compact record: per page the asset URL hashes, sampled-pixel verdicts, Chromium version, commit; screenshots stay gitignored), a section in `docs/assets/surface_rehearsal_result.md` (the gate result `INCONCLUSIVE` does not move), `tests/visual_assets/` guard that the committed record parses and its pixel verdicts are all true.

## Proof Plan
Capture from the built bundle passes against Chromium (local `google-chrome` via `REHEARSAL_CHROMIUM`); a planted wrong asset (a built bundle whose fixture PNG was changed by one pixel) fails the pixel check; the committed evidence is from a real run.
