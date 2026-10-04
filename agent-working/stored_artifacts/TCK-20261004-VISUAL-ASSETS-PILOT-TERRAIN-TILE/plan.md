---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE
artifact_type: plan
tags: [mcp, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

1. Register `terrain.forest` (family `terrain`, no axes) by hand in `definitions/visual_keys.yaml`; update the zero-key registry test.
2. Draw candidates with the drawing tools; show the user previews and 4 x 4 patches; hand off and run intake (CLI, in this worktree) only for the one the user picks.
3. Blocking question: the user adopts through the CLI gate in their own terminal. The agent never adopts.
4. `build`, `release --catalog-id pilot`, `export-runtime`, `audit`, `verify`.
5. Update the tests that assumed an empty catalog to expect exactly the pilot asset; write `docs/assets/pilot_terrain_key.md`; fix stale docs (zero keys, "proposed" budgets).
