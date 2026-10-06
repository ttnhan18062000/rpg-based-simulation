---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW
artifact_type: investigation
tags: [architecture, testing, live-map]
---

# Investigation — TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW

- The saved generator reproduced all 22 committed drafts pixel for pixel, so the re-tint starts from the same drawings.
- Cause of the baseline FAIL: each tile's mean drifted from its flat fill (0.9 to 13.1 dE); a pair fails when the combined drift shrinks the pair's distance by more than the 2.0 margin and stays under 10.
- Base-colour-only retinting distorted palettes (farmland base to #6bb243, floor to #080c1b) and was dropped; one offset on the five ramp colours keeps the contrast structure.
- Subset enumeration (exact correction): correcting the 16 tiles in failing pair-visions leaves shallow_water/wall failing; 17 still fails; no subset of the 16 passes; all 22 passes. Every corrected tile moves the pairs it drifted with.
- Clipping: only lava (b) and snow (b, g) clipped; compensated by the refine loop; final mean-to-fill 0.40 and 0.14 dE.
- Texture after the shift: every tile still >= 5.3 (min L* std over visions); dungeon_entrance and farmland rose (9.6 -> 11.8, 14.7 -> 17.4).
- Quarantine: the 22 replaced intakes remain in the gitignored quarantine (`draft keep --replace` removes only the old draft entry). Old workspace sprites `tdraft_<name>_a` and the `_b` sprites stay in `~/.cache/rpg-aseprite-mcp`.
