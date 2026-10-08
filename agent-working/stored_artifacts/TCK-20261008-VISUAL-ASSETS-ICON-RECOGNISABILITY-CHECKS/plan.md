---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
artifact_type: plan
tags: [architecture, testing, hud]
---

# Plan — TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

1. Specs for all 36 icons as data (`visual_assets/icons/icon_specs.yaml`) before any redraw; loader, validation (every registered icon key, no distractor that would count as correct) and a generated style-guide table guarded by a test.
2. Reference study (Kenney Tiny Dungeon and 1-Bit, CC0, viewing only) recorded in the style guide.
3. Blind recognition tool (neutral shuffled images, hashes, seeded candidate lists with distractors, whole-word scoring); run it with two independent fresh agents on all 36; store prompts, hashes, answers and the evaluation.
4. Whole-sheet look-alike report (bounding box fitted to 24x24, XOR), tested on planted twins; run on all 36.
5. Process rule in the style guide. Mutants; close. No redraw (child 4c).
