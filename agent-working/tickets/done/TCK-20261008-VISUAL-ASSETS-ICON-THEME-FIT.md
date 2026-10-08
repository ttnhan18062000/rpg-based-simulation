---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT
phase: done
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT

## Title
Theme fit: a written medieval-fantasy theme rule, a theme field in every icon spec and the blind check, an audit of all 36 icons, and the tool icon redrawn as hammer and tongs

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The owner (2026-10-08) rejected the proposed tool icon: a toolbox reads as a modern suitcase and breaks the
theme ("fantasy medieval/magical ... we need to maintain a theme"). Planner analysis: no theme or era constraint exists
anywhere (D20 fixes style, sizes, palette, sources, not setting), so the specs and the blind check passed a modern object;
the adopted v2 tool (a wrench) has the same flaw. Owner decisions (blocking question, 2026-10-08): theme = **"Medieval
fantasy + magic"** (objects a medieval craftsman, traveller, soldier or mage would own; magic items allowed; nothing
modern: suitcases, wrenches, zips, plastic, printing); tool icon = **"Hammer and tongs"** (a smith's hammer crossed with
tongs, not a weapon pose).

## Scope
1. **Theme rule:** ADR row D21 (theme, decided by the owner 2026-10-08, the wording above) and a theme section in
   `docs/assets/icon_style_guide.md` with examples of allowed and forbidden objects; the process rule gains "theme fit" at
   the spec step and the check step.
2. **Specs:** every entry in `visual_assets/icons/icon_specs.yaml` gains `theme` (what era/setting it belongs to) and
   `modern_lookalikes_to_avoid`; the loader requires both.
3. **Blind check:** add an era question ("what era or setting is this object from?"); an answer naming a modern
   setting flags the icon. Record prompt and answers as before.
4. **Audit all 36 adopted/proposed icons** (key set, v2, the four proposed revisions) against the rule, on THREE
   inputs (owner, 2026-10-08: "also check other icons, the description or something"): the pixels (era question), the
   spec text (glyph choice, reads-as), and the registry key description / fallback text. List every offender with the
   reason. Planner's own first pass (to be confirmed or overturned by the audit): wrench (modern, replaced by item 5),
   hero house (white walls + blue square glass windows read as a modern suburban house; should be a timber-framed
   cottage with shutters or small leaded windows, thatch or tile roof), inn mug (glass beer mug with foam; a wooden or
   pewter tankard fits better). Report to the planner; the planner decides redraws with the owner.
5. **Tool icon:** replace the proposed toolbox in `icons-owner-fixes-v1` (not adopted, so `draft keep --replace` is
   fine) with hammer and tongs, through the process: spec (theme fields, crossed, not a weapon pose, live area), reference
   study, silhouette in the review folder for the owner's approval, draw, checks (rule, compliance, blind + era).
6. Regenerate `~/Work/asset-review/icons-owner-fixes-v1/` (needs the review-sheet ticket) and update the owner commands
   (the tool's intake id changes).

## Out of Scope
- Redrawing audit offenders other than the tool without the planner's and owner's say-so. Wiring.

## Acceptance Criteria
- [x] D21 and the style-guide theme section recorded with the owner's wording; specs carry theme fields (loader-enforced).
- [x] Era question in the blind check; audit of all 36 reported.
- [x] Tool redrawn as hammer and tongs via the process, owner-approved silhouette; checks recorded; commands updated.

## Related Tickets
- TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES, TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER, TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Related Docs
- docs/architecture/visual_asset_foundation_adr.md (D20), docs/assets/icon_style_guide.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/ (audit_36_icons.md, era_check/, blind_check_round5/, drawing/, owner_fixes_result.json, mutant_proof.txt)


## Related Code Areas
- visual_assets/icons/icon_specs.yaml, tests/visual_assets/icon_specs.py, icon_recognition.py, visual_assets/drafts/icons-owner-fixes-v1/

## Assumptions / Open Questions
- The ranger's registry fallback text ("Lucide Crosshair") is UI chrome, left as is (planner instruction), noted in the audit.
- Decided beyond the ticket text by the owner (relayed 2026-10-08): hero house redrawn as a cottage, debuff frame reshaped, inn gets staves; ruins and enemy camp kept as adopted.
- Round 5 blind check: the tool's tongs read as a wrench and the debuff frame as a gear. Owner (2026-10-08, via the planner's blocking question), verbatim: tool "Accept as drawn", debuff spiked ring "Accept as drawn"; restated spec numbers (hammer head 25 to 20, thatch 90 to 80, plaster 50 to 30): "Accept the changes".
- Process rule added to the style guide (step 4b): spec numbers guessed before the silhouette are re-agreed at the owner's silhouette question, never restated after drawing.

## Implementation Notes
- D21 theme rule; spec fields `theme` and `modern_lookalikes_to_avoid`, loader-enforced with a modern-term guard; era question; free-text scoring flags a named modern object; audit of 36 icons.
- Seven revisions drawn into `icons-owner-fixes-v1` (`_fix` ids): buff, rogue, common, tool (hammer and tongs), cottage, spiked debuff frame, staved tankard. Owner approved every silhouette before drawing.
- Disclosed after-the-fact corrections: three compliance thresholds guessed before drawing were restated to the approved outlines' measured values (hammer head 25->20, thatch 90->80, plaster 50->30); the debuff frame was symmetrised at the source; the tool rivet colour changed to clear a lint warning; a spike-count measurement bug fixed. Sheet-rule thresholds untouched.

## Test Summary
- Sheet rule PASS on the set with all seven in place; compliance all rows ok; lint clean.
- Blind round 5 (free, choice, era; fresh sonnet agents): cottage, tankard, buff, rogue, bead named; tool read as wrench and debuff frame as gear (flagged, reported).
- Mutants A to E caught (`mutant_proof.txt`). Full scoped runs recorded in the commit report.

## Files Changed
- tests/visual_assets/{icon_specs,icon_recognition,icon_compliance,icon_owner_fixes_draft_set,review_sheets}.py and their tests, visual_assets/icons/{icon_specs,silhouette_proposals}.yaml, visual_assets/drafts/icons-owner-fixes-v1/, frontend icondraft_fixes fixtures, iconsilhouettes fixture and harness tests, docs (ADR D21, style guide, review doc), stored artifacts.

## Completion Summary
A written medieval-fantasy-plus-magic theme rule (D21) is now enforced in the specs, the blind check and the audit; seven revisions of adopted icons are drawn and ready for the owner's 14 commands in `~/Work/asset-review/icons-owner-fixes-v1/`. Two drawings (tool, debuff frame) still misread at a glance in free text; the owner accepted both as drawn, and accepted the three restated spec numbers.
