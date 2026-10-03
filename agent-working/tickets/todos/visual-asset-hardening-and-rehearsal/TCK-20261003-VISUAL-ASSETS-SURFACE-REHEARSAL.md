---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL
phase: open
date: 2026-10-03
tags: [live-map, rendering, testing, architecture]
---

# TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL

## Title
AM-M5 surface compatibility rehearsal in an isolated frontend harness: strict runtime-manifest parser, read-only resolver, fallbacks, single-generation loading, isolation proof and a per-gate result record

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The user authorized (2026-10-03) an isolated `AM-M5` rehearsal (`docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md`)
on synthetic fixtures, with the normal Live Map, HUD and simulation untouched. Under Profile A (ADR `D8`) the resolver is client
code bound to the manifest of its own build. This ticket builds that resolver in isolation, proves it against ticket 3's
fixture, and records an honest result for each gate. It also closes the epic.

## Scope
All new code lives in `frontend/src/visualAssets/`; nothing in the normal app imports it.

1. **Participating-surface matrix (`AM5-W01`)**: in the result record (item 8): the rehearsed role is **map-only**, one 16-pixel
   cell (`CELL_SIZE`); HUD does not participate and is recorded as out of scope, not passed.
2. **Strict manifest parser** `manifest.ts`: parses ticket 3's `runtime_manifest.json` into a frozen typed snapshot; rejects unknown
   fields, a wrong `record_type`/`schema_version`/`fallback_contract_version`, a `file` that is not `<64 hex>.png` or not derived from
   its `pixel_hash`, duplicate or unsorted keys, out-of-range dimensions. Duplicate JSON object keys cannot be seen after
   `JSON.parse`: either scan for them on the raw text or record it as a stated gap (the Python side already rejects them at export).
3. **Resolver** `resolver.ts`: pure `resolveVisual(snapshot, key)` returning either an image result (file URL from the build, logical
   size, the snapshot's generation) or a fallback result with a typed reason (`unknown_key`, `missing_image`, `decode_failed`,
   `manifest_invalid`, `late_result_dropped`). The key set is the manifest's, finite; an unknown key never triggers a fetch and
   never registers anything. The generation is the manifest's `candidate_manifest_hash`.
4. **Fallback (`AM5-W04`, `W05`)**: each family has a typed fallback (a primitive glyph drawn with the existing Canvas style plus a
   text label) that keeps the critical fact (which role this cell shows) without the image and without relying on hue alone.
   Tests cover missing image, corrupt image, late image, invalid manifest.
5. **Single generation (`AM5-W06`)**: a loader that loads the snapshot's images and drops any completion that belongs to an
   older generation, so a mounted view never mixes two manifests. Test with two snapshots and out-of-order completions.
6. **Harness (`AM5-W02`, `W03`)**: a React component that draws (a) one 16 x 16 cell with each fixture key and (b) a predeclared
   crowded scene (for example a 12 x 8 cell grid with all three keys, some fallbacks mixed in), at native scale with
   `imageSmoothingEnabled = false`. It is mounted only from tests and from a dev-only Vite page `frontend/rehearsal.html`, which is
   **not** in the production build (Vite builds only `index.html` unless `rollupOptions.input` says otherwise; do not change that).
   Optional but wanted: a local Playwright spec with its own config (`playwright.rehearsal.config.ts`, a plain `vite` dev server,
   not `make dev`) that opens `rehearsal.html` and saves native-scale screenshots for a human to look at. Local only; not in CI.
7. **Isolation proof (`AM5-W08`)**: a test that no file outside `frontend/src/visualAssets/` imports from it, and that the
   production `npm run build` output contains no fixture PNG and no `visualAssets` module (check `dist/` after the build in the test,
   or a small script the CI Build step already covers). `GameCanvas.tsx`, `useCanvas.ts`, `App.tsx` and `src/` are unchanged
   (`git diff --stat` in Test Summary).
8. **Result record** `docs/assets/surface_rehearsal_result.md` (frontmatter `layer: frontend`): per deliverable `AM5-W01`..`W09` and per
   gate `AM-C05`, `C06`, `C07`, `C09`, a result from {`PASS`, `FAIL`, `BLOCKED`, `INCONCLUSIVE`} with the evidence and the reason, using
   the gate definitions in the proposal's gate table and the M5 plan. Expected honest outcomes, unless evidence says otherwise:
   `W07` supported clients is at best "jsdom in CI, Chromium locally" and otherwise `INCONCLUSIVE`; `W09` retention cannot run
   (no M4 records, no client roots) and is `BLOCKED`; readability of synthetic shapes is not an art claim. Never write `PASS` for
   something not run.
9. **Docs and close-out**: `docs/assets/store_contract.md` "Not built" list, the runtime-integration README status, the M5 plan
   status note, the foundation README's "As built" section if anything deviates; epic close per CLAUDE.md (move the folder to
   `done/` when all four children are done).

## Out of Scope
- Any change to the normal Live Map, HUD, `App.tsx`, `src/` or the WebSocket path; any real asset; wiring the resolver into gameplay
  (`AM-M6`, dormant); renderer selection (PixiJS etc.).
- Running Playwright in CI; adding browsers beyond the configured Chromium.
- New npm dependencies (if one seems needed, ask the planner first).

## Acceptance Criteria
- [ ] Parser rejection cases each have a test; a valid fixture parses into a frozen snapshot.
- [ ] Resolver: every fallback reason has a test; an unknown key performs no fetch (spy).
- [ ] Out-of-order completions across two generations never show the older one (test).
- [ ] Fallback output keeps a text label for every family and the three fixture keys are distinguishable without colour (test on the fixture alpha masks or the fallback glyphs).
- [ ] Isolation test passes; production build output has no fixture and no `visualAssets` chunk; the normal-path files are unchanged.
- [ ] `npx vitest run` and `npm run build` pass; `npm run lint` passes for the new files.
- [ ] `docs/assets/surface_rehearsal_result.md` has a result for every `AM5-W*` deliverable and every M5 gate, with evidence or the reason it could not run.
- [ ] Epic closed: all four children in `done/`, folder moved, plan statuses updated.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST (fixture and contract)

## Related Docs
- docs/plans/visual-asset-management-runtime-integration/05_surface_compatibility_rehearsal_plan.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (9.1-9.3, gate table)
- docs/plans/render-and-art/02_hud_core_readiness_plan.md, 05_integrated_browser_validation_plan.md (surface owners; HUD not participating)
- docs/architecture/visual_asset_foundation_adr.md (D6, D8)

## Related Stored Artifacts
- None yet; staging artifacts go to `agent-working/staging_artifacts/TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL/`.

## Related Code Areas
- frontend/src/visualAssets/ (new), frontend/rehearsal.html (new, dev-only), frontend/src/constants/ (`CELL_SIZE`, read only), frontend/vite.config.ts (read only)

## Assumptions / Open Questions
- The CI `Frontend` job runs `npx vitest run` and `npm run build` on frontend changes, so the new tests and the build check run in CI with no workflow change.
- The plan's "named owners for every participating surface" is the user for the Live Map seam in this rehearsal (authorized 2026-10-03).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
