---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
phase: done
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Title
Icon recognisability: per-icon construction specs, a reference study step, a blind recognition check and a whole-sheet look-alike report

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4b of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. At the owner gate of `icons-v2` the user found the weapon sword "kinda weird" (a short 4 px blade, a lumpy grip
wider than the guard, no pommel: reads as a cleaver, and it nearly duplicates the rogue dagger) and asked for the root
cause. Planner analysis (2026-10-08): every gate measures **distinguishability** (I1 shape, I2 value, I3 contrast, lint),
none measures **recognisability**. Four misreads in 36 icons all passed every gate: the debuff frame (a smile), the shrine
(a bell), the ruins (a boot), the sword (a cleaver). Causes: one-word glyph specs with no proportions; drawing from
memory with no reference study; a design loop that optimised the rule numbers; no cross-family comparison; agent eyeballing
of tiny pixel art is unreliable (the implementer and the planner both passed the sword). The user chose (blocking
question, 2026-10-08) **"Fix the process now"**: build the checks in this batch, run them on the 22 v2 icons, redraw what
they flag, then the owner gate.

## Scope
1. **Construction specs** in `docs/assets/icon_style_guide.md` (a dated section): per family, conventions (e.g. weapons
   upright point-up, tools diagonal handle bottom-left; say which and why), and per icon (all 22 v2 + the 14 adopted, the
   latter as description of what exists): orientation, proportions in pixels (e.g. sword: blade length >= 60% of height,
   blade width 2-3 px with a centre line, crossguard perpendicular, grip <= guard width, pommel), the parts list, one line
   **reads as**, one line **must not read as**. Specs are written BEFORE any redraw.
2. **Reference study step** (D20 reference-only): for each glyph, look at 2-3 existing icons of that object at 16-32 px
   (e.g. game-icons.net, Kenney, Shikashi; the packs research) and record title/author/source/licence plus the
   conventions observed (one line). Nothing is traced or copied. Recorded per icon in the review doc or a stored artifact.
3. **Blind recognition check** (evidence, not a CI gate, because it is not deterministic): a tool that renders each icon
   unlabelled at 1x and 4x (on the plate for location glyphs) and asks a FRESH agent with no project context to name
   it, free text first, then pick from a candidate list that includes distractors (e.g. sword / knife / cleaver /
   dagger). Record the prompt, the model, the images' hashes and every answer as a stored artifact. An icon is
   **flagged** when the free-text answer does not name the intended object (synonyms listed in the spec count).
   Run it once on the 14 adopted key-set icons as a calibration: report, change nothing there.
4. **Whole-sheet look-alike report** (deterministic, report-only): for every icon, its nearest neighbours across ALL
   families by silhouette difference (compare at a common scale; state the method), so cross-family twins (dagger vs
   sword) surface. Tested on planted twins.
5. **Process rule** for future batches, in the style guide: spec -> reference study -> one-colour silhouette sheet that
   the owner approves -> drawing -> sheet rule + recognition check + look-alike report -> owner gate.

## Out of Scope
- Redrawing (child 4c). Changing I1-I3 or any user threshold. Changing adopted pixels.

## Acceptance Criteria
- [x] Specs for all 22 v2 icons (and the 14 adopted, descriptive) committed before any redraw.
- [x] Recognition check implemented and run on the 22 v2 and the 14 adopted icons; answers stored; flags listed.
- [x] Look-alike report tested (a planted twin is reported) and run on all 36.
- [x] The process rule is in the style guide.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

## Related Docs
- docs/assets/icon_style_guide.md, docs/assets/icon_research/research_icon_craft.md (NN/G 'guess what this is' test), research_packs_palettes.md (reference packs, licences)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/ (plan, investigation, test_plan, mutant_proof.txt, blind_check_results.md, blind_check/, lookalike_report.json)

## Related Code Areas
- tests/visual_assets/ (icon_specs, icon_recognition, icon_lookalikes and their tests), visual_assets/icons/icon_specs.yaml, docs/assets/icon_style_guide.md, agent-working/stored_artifacts/

## Assumptions / Open Questions
- The fresh agent for the blind check is spawned without project context (a general subagent given only the images and the question). If that cannot be guaranteed, say what context it had.

## Implementation Notes
- **Specs:** `visual_assets/icons/icon_specs.yaml`, 36 entries (22 `v2` targets, 14 `adopted` descriptions) with orientation, pixel proportions, parts, reads as, must not read as, synonyms and distractors, written before any redraw; family conventions (weapons upright, class dagger diagonal, rarity never octagon or diamond). `tests/visual_assets/icon_specs.py` validates (every registered icon key; no distractor that contains a synonym) and generates the style-guide table, which a test requires verbatim in `docs/assets/icon_style_guide.md`.
- **Reference study:** Kenney Tiny Dungeon and 1-Bit Pack previews (CC0, viewing only), conventions recorded in the style guide; game-icons.net and Shikashi not examined (stated).
- **Blind check:** `tests/visual_assets/icon_recognition.py` (render, neutral shuffled ids, hashes, seeded candidate lists, whole-word scoring, CLI `build` and `evaluate`). Run with two independent fresh `general-purpose` sonnet subagents (free text, then choice) on all 36; the record states the context they had and that "no project context" is intent, not verified.
- **Results (single sample):** ten free-text flags: five v2 misreads (ruins as mountain peaks, trinket as a medal, tool as a war hammer, ranger bow as a crossbow, common bead as a square), plus on the adopted calibration the buff and debuff frames and tier badges B, D, E (abstract; expected). **The sword was not flagged** (named "steel sword"): the check cannot see "looks wrong"; the look-alike report does (sword and dagger are each other's nearest neighbour at 55 XOR px; the next nearest is 152). Details and candid reading: `blind_check_results.md`.
- **Look-alike report:** `tests/visual_assets/icon_lookalikes.py` (bounding box fitted to 24x24 by nearest neighbour, XOR out of 576, report only), tested on planted twins; run on all 36 (stored).
- **Process rule:** six numbered steps in the style guide (spec, reference study, one-colour silhouette sheet approved by the owner, draw, checks, owner gate).
- A scoring flaw found by the first run ("crossbow" matched "bow") was fixed in the tool (whole-word match) and pinned by a test before the record; the answers were not changed.


## Test Summary
- New: `test_icon_specs.py` (5), `test_icon_recognition.py` (9), `test_icon_lookalikes.py` (5). Mutants A to D caught (mutant_proof.txt). `pytest tests/visual_assets tests/docs tests/static`: 1808 passed, 2 skipped, 1 xfailed. No frontend file changed.


## Files Changed
- visual_assets/icons/icon_specs.yaml, tests/visual_assets/{icon_specs,icon_recognition,icon_lookalikes,test_icon_specs,test_icon_recognition,test_icon_lookalikes}.py, docs/assets/icon_style_guide.md, ticket and stored artifacts.


## Completion Summary
Specs for all 36 icons, a reference study, a blind recognition check (run on all 36 by two fresh agents, answers stored), a whole-sheet look-alike report and the process rule are committed, with no icon changed. The first run flags five v2 icons (ruins, trinket, tool, ranger, common bead) and the adopted buff and debuff frames; it did not flag the sword, which only the look-alike report singles out.

