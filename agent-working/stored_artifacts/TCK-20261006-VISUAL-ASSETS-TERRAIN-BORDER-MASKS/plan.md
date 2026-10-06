---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS
artifact_type: plan
tags: [architecture, testing, live-map]
---

# Plan — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS

1. Design nine masks (edge, outer_corner, inner_corner x v1-v3) in `mask_generator.py` under the approved contract; draw, hand off, intake, `draft keep` into terrain-v1.
2. Render-match check (`rendering.compare_preview`, the function adopt-set calls) on every entry, tiles as control (planner condition).
3. `test_border_masks.py`; keep `test_terrain_draft_set.py` and the set check scoped to terrain tiles.
4. Preview page: `borderRender.ts` and a borders on/off toggle; tests. 5. Evidence: screenshots on/off, close-up sheet, masks sheet. 6. Re-run AM5-S.
