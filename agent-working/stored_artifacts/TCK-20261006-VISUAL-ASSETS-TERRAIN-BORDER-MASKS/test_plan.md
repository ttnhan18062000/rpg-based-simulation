---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS
artifact_type: test_plan
tags: [architecture, testing, live-map]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS

`tests/visual_assets/test_border_masks.py` (6): exactly nine slots; 1-bit non-empty shapes within the 4 px cap for their kind; no isolated pixel; edge profiles are runs from the cell edge, depth 2 at both ends, steps <= 1, ragged, three different variants; inner corner equals edge union its east turn; outer corners are small north-east blobs.
`frontend/.../borderRender.test.ts` (5) and a harness toggle test: no masks gives no overlay, centre always own terrain and changes only within 4 px, deterministic, missing masks, cells put at their map position; toggle on by default and switches the status line.
`test_terrain_draft_set.py` updated in intent (22 tiles + 9 masks = 31 entries, nothing adopted); `set_colour_vision.draft_tiles` scoped to `terrain.` entries.
Full: `tests/visual_assets` 1541 passed (2 GB cap); `vitest src/visualAssets` 213 passed; `tsc -b`, `eslint src/visualAssets` clean; `draft verify` ok; catalog `verify` ok.
