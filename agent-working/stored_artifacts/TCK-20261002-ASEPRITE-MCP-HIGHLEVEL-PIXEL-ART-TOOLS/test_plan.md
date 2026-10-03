---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS
artifact_type: test_plan
tags: [mcp, testing, rendering]
---

# Test Plan — TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS

Command (from the worktree): `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m pytest experiments/aseprite_mcp/test_highlevel.py -q -p no:cacheprovider`

| Area | Tests | Kind |
|---|---|---|
| Ramps | base in place, luma monotone, hue direction, no overshoot, neutral base, validation | pure |
| Dither | matrices are permutations, exact tile coverage (5 cases), extremes, monotone gradient, determinism, validation | pure |
| Stroke | L-corner removal, vertices kept (closed box), straight/diagonal unchanged, single point, empty | pure |
| Shade | bevel rect edges, round ellipse bands and orientation, 5 bands, determinism, no orphans, validation, empty | pure |
| ASCII / lint | legend order, clean sprite passes, budget, value separation, edge, orphans, empty, budget by size | pure |
| Sprite tools | tiled readback on 70x40, shade ellipse/colour target, error paths publish nothing, dither region/mask, stroke + layer creation, outline full/selout/skip/clipping, selout colour reuse, remap + multilayer guard, lint + ascii on a real sprite, MCP registration set | real Aseprite |

Baseline: 49 passed (coherent private copy). Open: mutation checks (plan step 4); green run in the shared worktree.
Not covered: performance on 128x128 (tiled readback is up to 16 sandbox launches), visual quality (human judgement).
