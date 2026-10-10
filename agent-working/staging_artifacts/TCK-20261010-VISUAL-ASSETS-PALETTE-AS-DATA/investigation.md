---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation
Only icons-v1.json existed. Terrain fills live in colors.ts and are already read by `icon_palette.terrain_fills`, so terrain-v1 is the first 23 entries of icons-v1 as its own file. Technique code is import-pure; the rules file is read once at import by lint.py (documented in the module). `lint_sprite` on adopted icons: 0 off-palette pixels for all 36, so the palette matches the art. MCP `lint_sprite` gained two optional parameters (back-compatible).
