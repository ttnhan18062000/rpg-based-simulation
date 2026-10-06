---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE
artifact_type: test_plan
tags: [architecture, testing, live-map]
---

# Test plan — TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

`tests/visual_assets/test_set_colour_vision.py` (10 tests): approved constants; tiles equal to fills pass ("same"); close pair fails and far pair passes in every vision; margin 2.0 exactly
(inside 1.5 passes, outside 2.5 fails, floor cannot rescue); the 10 dE floor branch; texture below 2.0; determinism and forest variants outside the verdict; tile/fill key mismatch refused;
committed inputs cover 23 keys, forest from adopted slots; live report 23 tiles / 253 pairs / 1012 pair-visions (no verdict asserted).
Mutants: margin 0, margin 4, one vision only, no 10 dE floor, TEXTURE_MIN 0: each fails the named test(s). Also `test_boundaries`, `test_no_ignored_files`, `test_py311_fstrings`, `test_pilot_colour_vision`.
