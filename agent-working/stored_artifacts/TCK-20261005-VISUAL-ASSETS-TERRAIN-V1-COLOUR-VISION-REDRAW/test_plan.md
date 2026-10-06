---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW
artifact_type: test_plan
tags: [architecture, testing, live-map]
---

# Test plan — TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW

No new code under test in the repository (the generator and drawing driver are stored artifacts). Verification: `draft verify` ("drafts ok"), catalog `verify` ("store ok"), `python -m tests.visual_assets.set_colour_vision` re-run (after_terrain_v1.txt), `tests/visual_assets` full: 1533 passed (foreground, 2 GB cap) including `test_terrain_draft_set.py` (22 drafts, nothing adopted).
Honest wording: with mean == fill, S1 holds by construction (dE_tile == dE_fill within rounding), so PASS means "no worse than the flat fills"; the tiles add only the S2 texture cue. The flat-fill baseline is hue-only and not colour-vision safe.
