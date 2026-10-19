---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT
artifact_type: plan
tags: []
---

# plan - TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT

1. `TerrainDefinition` gets required `gives_cover` and `high_ground`; `data/content/world/terrain.yaml` declares them (cover: forest, mountain, ruin, cave; high ground: mountain).
2. `src/content/terrain_cost.py` becomes the one reader of what a terrain declares (cost, cover, high ground); `legality.py` `check_cover` and `check_high_ground` read through it and name no terrain.
3. Correct the stale rows: Bible 02 tactical modifiers and the two combat parity rows (divergence 2.129).
4. Rebase onto the post-route tip: renumber the divergence from 2.127 to 2.129, drop the duplicate warmup imports, follow the cache rename in the one test that read it.
5. Measure with the standard paired command and a call-count probe; close.
