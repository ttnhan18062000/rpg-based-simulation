---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA
artifact_type: plan
tags: [architecture, testing]
---

# Plan
`review/palette_data.py` generates `palettes/terrain-v1.json` (read-only from colors.ts via the icons-v1 reader) and `icons-v1.gpl` / `terrain-v1.gpl`; tests compare the committed files with the generators (drift guards). `lint_grid(palette=...)` adds an advisory `off_palette` info finding; `drawing/palettes.py` loads a committed palette by validated id; `compose.lint` and the `lint_sprite` MCP tool take `palette` or `palette_id`. The colour budgets move to `drawing/technique/style_rules.json` (same values, pinned).

## Proof Plan
Drift guards for 3 generated files; planted off-palette pixel flagged (also in a real adopted icon); all 36 adopted icons have zero off-palette pixels against icons-v1; advice never changes `ok`; budgets pinned at 8/12/16/24 across boundary sizes; 5 mutants killed (inverted membership, budget value, finding level, GPL header, id validation).
