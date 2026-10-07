---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
phase: open
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Title
Icon recognisability: per-icon construction specs, a reference study step, a blind recognition check and a whole-sheet look-alike report

## Status
OPEN

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
- [ ] Specs for all 22 v2 icons (and the 14 adopted, descriptive) committed before any redraw.
- [ ] Recognition check implemented and run on the 22 v2 and the 14 adopted icons; answers stored; flags listed.
- [ ] Look-alike report tested (a planted twin is reported) and run on all 36.
- [ ] The process rule is in the style guide.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

## Related Docs
- docs/assets/icon_style_guide.md, docs/assets/icon_research/research_icon_craft.md (NN/G 'guess what this is' test), research_packs_palettes.md (reference packs, licences)

## Related Stored Artifacts


## Related Code Areas
- tests/visual_assets/ (new tools), agent-working/stored_artifacts/

## Assumptions / Open Questions
- The fresh agent for the blind check is spawned without project context (a general subagent given only the images and the question). If that cannot be guaranteed, say what context it had.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

