---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS
artifact_type: investigation
tags: [architecture, testing, live-map]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS

- Mask design: every edge profile starts and ends at depth 2 (any two variants meet seamlessly), steps of at most 1 per column, 3 to 4 distinct depths, no isolated pixel; the inner corner is the edge union its east-side turn; outer corners are 6 to 10 pixel blobs at the north-east corner. All within the approved 4 px cap.
- **Render match (alpha risk retired):** `render_match_check.py` ran the real sandboxed Aseprite renderer through `rendering.compare_preview` on all 31 entries (22 tiles as control, 9 masks): 31 of 31 `MATCH` with `rendered_pixel_hash == entry pixel_hash` (`render_match_terrain_v1.txt`). Nothing in rendering or intake was changed.
- AM5-S: the set check now ignores non-terrain drafts (the rule is about tiles); its report is byte-identical to the re-tint ticket's `after_terrain_v1.txt` (PASS, 0/1012).
- Visual finding: borders read as ragged transitions between natural terrains and as clean edges for crisp ones (town/mountain); the fringe shows the higher neighbour's own tile pixels. The user's judgement of C6 is theirs at the owner gate.
- Draft set hash with masks: sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2 (34 manifest entries incl. 3 forest references; 31 drafts).
