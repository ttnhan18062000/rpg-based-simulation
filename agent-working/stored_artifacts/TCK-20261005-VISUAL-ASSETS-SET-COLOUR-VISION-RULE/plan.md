---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE
artifact_type: plan
tags: [architecture, testing, live-map]
---

# Plan — TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

1. Blocking question to the user: S1 form, pair scope, S2, whole-map W03 wording. Answered 2026-10-05: all as proposed.
2. Write the rule and the whole-map scene criteria into `docs/assets/pilot_terrain_m5_criteria.md` (new dated section; pilot sections untouched) before any terrain-v1 file changes.
3. `tests/visual_assets/set_colour_vision.py` reusing `pilot_colour_vision`; forest read from its adopted slots; forest bush/tree reported only.
4. Tests on synthetic input, mutant proof, baseline on terrain-v1 recorded as measured.
