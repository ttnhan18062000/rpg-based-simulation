---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Investigation

- c14/c15 (`codebase/structure/importlinter.toml`) only forbid visual_assets <-> src; the real `lint-imports` run: 17 kept, 0 broken after the move. The package registry covers `src` only; `visual_assets` is already one root package, so `visual_assets/review` needs no registration.
- The store's own layering (`STORE_ALLOWED`) forbids importing `drawing`, and the tools need `drawing.technique` (lint, ramps): so the home is a peer package, not `store/`. The tools also read `store.records` (adoption records) and `store.draftexport`, read-only; no gate layer is allowed (`test_boundaries.py`).
- 18 modules moved (17 listed plus `set_colour_vision`, a dependency of `icon_palette`); `REPO = parents[2]` is the same depth. The frontend test `iconScene.test.ts` reads `pilot_colour_vision.py` by path and had to follow.
- `tile_pixels()` took the first PNG in glob order = the tree slot on this machine. Users: its own CLI and one loose test; the per-slot rows in the docs call `evaluate()` directly and the icon rules use `icon_palette._tiles()`. No recorded result depends on the old behaviour.
- `palettes/icons-v1.json` quotes the old tool path in its derivation/source strings and is exactly the output of `icon_palette.build_palette`; left untouched (a recorded file).
