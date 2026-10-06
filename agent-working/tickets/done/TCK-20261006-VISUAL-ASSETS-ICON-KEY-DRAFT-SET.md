---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET
phase: done
date: 2026-10-06
tags: [architecture, hud, testing]
---

# TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET

## Title
Draw the icon key set as draft set icons-key-v1, with a preview page and the sheet rule result, ready for the owner's adopt-set

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 5 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. With the style guide (child 1), keys (child 2), palette and rule (child 3) committed, draw the key
set so the user can judge the style on a few icons before the whole set is drawn.

## Scope
- Draw with the Aseprite MCP tools only, our own pixels (reference-only outside art; record any reference looked at
  as title/author/source/licence in the draft's provenance or notes; no AI generators): every key from child 2.
  Follow `docs/assets/icon_style_guide.md` and `pixel_art_technique.md` (silhouette first, palette from child 3,
  `lint_sprite` clean or every finding explained).
- Keep them as draft set `icons-key-v1` (`draft keep`), the same flow as terrain-v1.
- Preview page (extend the draft harness): contact sheet at 1x and 2x; the location plate+glyph over the darkest and
  brightest terrain-v1 tiles and on a small map scene at whole-number zoom (child 4); the tier ladder in greyscale and
  the three simulated visions next to the colour version; buff/debuff pair likewise; each icon beside its fallback.
- Run child 3's check; record the result as measured. A FAIL is reported, not tuned away (redraw only with the
  planner's say-so).
- Hand the user the exact `adopt-set` command (absolute venv interpreter path) and the preview command; then wait.

## Out of Scope
- Adoption. Panel wiring. Any icon outside the key set.

## Acceptance Criteria
- [ ] Every child-2 key has a draft in `icons-key-v1`; `lint_sprite` results recorded.
- [ ] Sheet rule result recorded as measured (I1-I3).
- [ ] Preview page shows every view listed in Scope; the user has the commands.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION, TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES, TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE, TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

## Related Docs
- docs/assets/icon_style_guide.md, docs/assets/icon_criteria.md (after children 1 and 3)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET/ (plan, investigation, test_plan, rule_result.txt, art_prototype_*.py.txt, mutant_proof.txt)

## Related Code Areas
- visual_assets/drafts/, visual_assets/store/drafts.py, frontend/src/visualAssets/DraftHarness.tsx

## Assumptions / Open Questions
- If the draft harness assumes 16x16 tiles, extending it for 24 and 8 is in scope; report the size of that change to the planner first. Done: the store, drawing tools, intake and `draft keep` are size-agnostic (1 to 128 px, previews up to 1024 px); only the frontend harness is terrain-specific, so a sibling page was built (planner approved).

## Implementation Notes
- **Art:** 14 sprites drawn with the Aseprite MCP tools from palette `icons-v1` only (own pixels, no outside art, no generator); kept as draft set `icons-key-v1` (`draft keep`, `draft verify` ok). Descriptions of each: `docs/assets/icon_key_set_review.md`.
- **Prototype failures (the rule was fixed first; using it as design feedback is not tuning, planner 2026-10-06):** the first ASCII prototype passed I1 and I3 but failed I2 on two pairs: the ring badge A (no interior pixels left, so its mean included the outline) and the buff and debuff frames (identical interiors). A became a smaller 4x2 cut-out and the frames got different interiors (`#4a6050` green, `#2d1722` ember-dark); nothing was tuned after drawing. The prototypes are in the stored artifacts.
- **Lint:** the first draw had value-separation warnings on three sprites (marker blade and tip, blacksmith wood and ember, warrior grip); recoloured to palette colours of distinct brightness (marker tip `#eafeff`, blade `#c8d8e8`; wood `#8e8c75`, spark `#e8c040`; grip `#5a2a1a`) and re-linted: no warnings, info notes only (diagonal strokes as orphan pixels; edge contact on plates, frames, badges is intentional).
- **Rule as measured on the real read-back (not asserted by any test):** PASS; I1 smallest 4 px (C vs E, S vs SS), buff/debuff 92 px; I2 smallest L* gap 8.74 (tiers) and 14.2 (frames); I3 18.0 (snow); 0 off-palette pixels. Full numbers in `rule_result.txt`.
- **Stars:** the diamond-with-pips fallback, as ruled. Reason: one outlined four-point sparkle is 5x5 and three need more than 8 px even overlapped; unoutlined 3x3 plus-stars would pass I1 (5 px each) but break the outline policy. Threshold unchanged.
- **Preview page (sibling harness inside visualAssets, isolation guard untouched):** `rehearsal-icons.html`, `IconHarness.tsx`, `iconScene.ts` (pure), `iconDraftSource.ts`, `pixelFit.ts` (a copy of the app's fit function, equality-tested), fixture `__fixtures__/icondraft/` (48 PNGs: 14 icons and the 34 adopted slots the export references, plus manifest and the recorded rule result). Views: contact sheet 1x/2x on dark and light beside the fallbacks; plate and glyph over the darkest (floor) and brightest (snow) tile; a small scene at a whole-number scale; tier ladder and frames in colour, greyscale, protan, deutan, tritan (SVG matrices in linear RGB, labelled a visual approximation; no pass or fail computed in the browser); the recorded rule result.
- **Page bug found by the user's "the page not working?" (2026-10-06) and fixed before the gate:** a whitespace text node in the vision table's header row made React log a DOM-nesting error in the browser console (the page still rendered). Fixed; the test file now fails any React console error or warning on the first mount (React reports each warning once, so the guard is file-wide; a mutant restoring the whitespace fails two tests). The dev server answers on `localhost` only, not `127.0.0.1`.
- **Registry-hash design (planner approved):** the freshness guard compares the fixture to a fresh `draft export` ignoring only the manifest's `registry_hash` (`draft_set_hash` is the file hash of `draft_set.json`, which holds no registry hash). A key registration cannot break it. Adopting the set changes the export (adopted references), so the adoption ticket refreshes the fixture.
- **Isolation guard re-pointed by equality:** fixture PNG count 47 to 95 (+14 icons +34 adopted references).
- **Tooling finding:** the MCP server runs from the MAIN checkout, so `submit_candidate` wrote its intakes to `/home/vboxuser/Work/rpg-based-simulation/visual_assets/catalog/.quarantine/` (gitignored, not deleted). Stray intake ids: in-b38a2188769869c1 (plate), in-641f3c59f5f4939d (marker), in-37bd500fef9a7034 (blacksmith), in-8737f1d1f0c8ba06 (warrior), in-ba348f41d73dfade (E), in-4b525122b446cb8b (D), in-7f5f75a61b4342a0 (C), in-2c7256eaabef8a0e (B), in-134be4b2159fdd2e (A), in-31644cad57a45f11 (S), in-5c261a962f9915bd (SS), in-065bc4aa0dea7235 (SSS), in-ec0f01dd297e3dc9 (buff), in-5eb3750c52019dca (debuff); plus throwaway size tests in-912123fa34e41d8a and in-b7494c152ff23e1e. The same intakes were re-run from the worktree with the CLI (same ids): those are the ones the draft set uses. Covered by the 30-day local retention rule.
- **Debuff frame redrawn at the planner's request, before the gate:** the first drawing (down chevron plus two light dots) read as a smiling face. Redrawn alone: dots removed, solid bone down arrow (2 px shaft, 4-then-2 px head), same inverted-triangle frame and ember rim; `draft keep --replace` (new intake `in-64c1eef69abd939b` from the worktree CLI, replacing `in-5eb3750c52019dca`), rule re-run: PASS, I1 buff vs debuff 92 px unchanged, I2 buff vs debuff smallest gap 14.2 to 7.7 (deutan), I3 and tiers unchanged, draft set hash now `sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd`. A 6-wide arrow head failed I2 in the prototype (2.8) before drawing, so the head is smaller. Fixture and review doc refreshed. The `adopt-set` template now leaves the licence value a placeholder too (no terrain template with a prefilled value is on record; `adopt-set --help` says only CLEARED is adoptable).
- **For the owner gate (findings):** E and D hard to see at 1x on a dark panel; plate rim is mid-light (departs from the research's dark outline, plates only); tier fills are mixed hues because value carries the order.

## Test Summary
- `pytest tests/visual_assets tests/docs tests/static`: 1729 passed, 2 skipped, 1 xfailed (17 new: `test_icon_draft_set.py`, `test_icon_draft_fixture.py`).
- `vitest run` whole frontend: 28 files, 333 passed (new: IconHarness 10, iconScene 10, pixelFit 3; the isolation guard and production build included); `npm run build` clean; new files lint-clean.
- Fixture guard mutants (flipped PNG byte, changed entry, missing file) are caught; a changed `registry_hash` alone is deliberately not (`mutant_proof.txt`).
- Looked at the page rendered in headless Chromium at DPR 1 and 2 (dev server, screenshots in the session scratchpad only).

## Files Changed
- visual_assets/drafts/icons-key-v1/ (14 draft entries), frontend/rehearsal-icons.html, frontend/src/visualAssets/{IconHarness.tsx,iconMain.tsx,iconScene.ts,iconDraftSource.ts,pixelFit.ts,__fixtures__/icondraft/,__tests__/(IconHarness,iconScene,pixelFit,isolation)}, tests/visual_assets/{icon_draft_set,icon_draft_fixture,test_icon_draft_set,test_icon_draft_fixture}.py, docs/assets/{icon_key_set_review,drawing_tools,icon_style_guide}.md, ticket and stored artifacts.

## Completion Summary
icons-key-v1 drawn (14 keys), kept as a draft set, sheet rule PASS as measured, preview page and fixtures committed; the owner's adopt-set command and the preview command are in docs/assets/icon_key_set_review.md.
