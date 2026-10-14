---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET
phase: done
date: 2026-10-07
tags: [architecture, hud, testing]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

## Title
Draw icon set v2 as draft set icons-v2 against the adopted key set, extend the icon preview page, record the rule result

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. Draw every v2 key in the style the owner adopted (`icons-key-v1`, `docs/assets/icon_style_guide.md`,
palette `icons-v1`), following child 1's glyph choices.

## Scope
- Aseprite MCP tools, own pixels, palette `icons-v1` only, no outside art copied, no AI generators. Submit intakes from
  the WORKTREE CLI (the MCP server runs from the main checkout; see the key-set batch). Keep as draft set `icons-v2`.
- Prototype against the fixed rule before drawing is allowed (design feedback); thresholds never move.
- Extend `rehearsal-icons.html` / `IconHarness` to show v2 next to the adopted key set (one contact sheet per family,
  1x and 2x, dark and light panels, fallbacks), location glyphs on the plate over darkest and brightest terrain,
  rarity next to tier badges, the colour-vision columns labelled as approximation, and the recorded rule result.
- Run the rule; record as measured. A FAIL is reported to the planner before any redraw.
- Review doc `docs/assets/icon_set_v2_review.md` with honest findings and the adopt-set template (licence a placeholder);
  remind the owner that `adopt-set` needs their own terminal (no TTY refusal) and the preview URL `http://[::1]:5173/rehearsal-icons.html`.

## Out of Scope
- Adoption, wiring, any change to the adopted key set's pixels.

## Acceptance Criteria
- [x] Every v2 key drafted in `icons-v2`; lint and rule recorded.
- [x] Preview page shows every view; the owner has the commands.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS, TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC, TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS, TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET (precedent)

## Related Docs
- docs/assets/icon_style_guide.md, icon_criteria.md, icon_key_set_review.md, icon_set_v2_review.md (new)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET/ (plan, investigation, test_plan, mutant_proof.txt, drawing/ scripts that reproduce the pixels)

## Related Code Areas
- visual_assets/drafts/, frontend/src/visualAssets/IconHarness.tsx, iconScene.ts, __fixtures__/icondraft/

## Assumptions / Open Questions
- About 24 icons; if drawing reveals that a family's glyph choice cannot pass the rule, stop and ask the planner.

## Implementation Notes
- **Drawing:** all 22 prototyped locally (own canvas + the same lint + the fixed rule), looked at, then drawn via `visual_assets.drawing.api` in-process (planner-approved, 2026-10-08; handoff limitations say so), intakes by the worktree CLI (22 PASSED), `draft keep --set icons-v2`, `draft verify` ok. The drafts equal the prototypes pixel for pixel. Scripts: `stored_artifacts/<ticket>/drawing/`.
- **Redraw before the owner gate (planner request after reviewing the previews, 2026-10-08):** `icon.marker.shrine` (read as a bell or bottle) became a slim straight obelisk with a pointed tip and a 2 px plinth; `icon.marker.ruins` (read as a boot or chess piece) became two broken stubs of different heights with a fallen block. `draft keep --replace` on those two slots only; rule PASS before and after (locations group minimum 17 px, boss arena vs dungeon entrance, untouched; ruins and shrine at least 27 and 45 px from the others, 49 px from each other); draft set hash `sha256:07ded31ec3dbddba4cae5ba54eca5d80da9dc739bc544156af0fc97efc3d6d9c`; fixture `icondraft_v2/` refreshed. Before/after table in the review doc, which also gained the blade-overlap flag.
- **Design-loop changes (from previews, not from the rule):** uncommon badge redrawn as a real kite gem (the first read as an up-arrow, confusable with the buff chevron); common bead got a highlight pixel; broken column and obelisk redrawn with clearly different silhouettes (planner request; 39 px apart); several near-equal-brightness shade colours changed to clear `value_separation` lint.
- **Rule as measured:** PASS (I1, I2, I3). Rarity I2 smallest L* gap 9.2 (protan); rarity vs tier silhouettes at least 8 px (floor 3); subject groups 17 / 65 / 132 / 71 px (locations / buildings / classes / items); no off-palette pixel; lint no warning; live areas respected. No FAIL, so nothing to report before a redraw.
- **Harness:** `IconHarness` takes an optional `v2` source; native sizes come from the manifests (`width / scale`), not a hard-coded list; new sections: v2 sheets by family, six location glyphs on the plate over floor and snow, rarity beside tiers in five visions, the recorded v2 result. `icon_draft_fixture` gained `--set icons-v2` and `icondraft_v2/`; the isolation guard is untouched except its PNG count pin (95 -> 151, on purpose).
- `docs/assets/icon_set_v2_review.md`: honest findings, adopt-set template with the licence a placeholder, the reminder that `adopt-set` needs the owner's own terminal, preview URL `http://[::1]:5173/rehearsal-icons.html`.


## Test Summary
- After the shrine and ruins redraw, re-run: `pytest tests/visual_assets tests/docs tests/static`: 1783 passed, 2 skipped, 1 xfailed; `vitest run src/visualAssets`: 261 passed; `tsc` and `eslint` clean. First run (before the redraw): `pytest tests/visual_assets`: 1642 passed (incl. the new `test_icon_v2_draft_set.py`, 8 tests); `vitest run src/visualAssets`: 21 files, 261 passed (incl. 7 new v2 harness tests and 1 new fallback test); `tsc` and `eslint src/visualAssets` clean. Mutants A and B caught (mutant_proof.txt).
- Known gap: the flaky `src/hooks/useSimulation.test.tsx` (load-dependent, code this branch does not touch) did not run in the scoped frontend run; it failed once in a full run during child 3 and passed 3 of 3 alone.


## Files Changed
- visual_assets/drafts/icons-v2/ (22 drafts), frontend/src/visualAssets/{IconHarness.tsx,iconScene.ts,iconDraftSource.ts,iconMain.tsx}, __fixtures__/icondraft_v2/, __tests__/{IconHarness,iconScene,isolation}.test, tests/visual_assets/{icon_v2_draft_set,test_icon_v2_draft_set,icon_draft_fixture}.py, docs/assets/icon_set_v2_review.md, ticket and stored artifacts.


## Completion Summary
All 22 v2 icons are drawn as the draft set `icons-v2` in the adopted style; the sheet rule PASSES as measured; the preview page shows every view next to the adopted key set; the review doc gives the owner the commands. Nothing is adopted or wired.
