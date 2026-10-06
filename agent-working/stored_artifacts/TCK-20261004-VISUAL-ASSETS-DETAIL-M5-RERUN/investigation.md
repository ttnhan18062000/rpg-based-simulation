---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN
artifact_type: investigation
tags: [mcp, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

- Built artifacts equal the draft pixels: every one of the 31 built 16x16 PNGs equals the draft preview sampled every 8th pixel (0 diffs); the rc-0005 forest PNGs are byte-identical to the pilot fixture's.
- Defect found by the Playwright "missing" injection and fixed: `composeBorderedCells` listed a mask variant as available when it was in the manifest, even if its image had failed to load, so the page reported 140 fringed cells while drawing none. Now a variant is available only when its image is loaded (test: missing and corrupt masks give no fringe, no putImageData).
- `tile_pixels()` in `pilot_colour_vision.py` takes the first PNG of the pilot export; here that is the tree slot, so its default output is the tree row (known fragility, not fixed); per-slot rows were computed by calling `evaluate()` on each slot.
- Stale-process traps met and handled: `systemd-run` scopes do not pass env vars (use `--setenv=`), and a leftover Vite on port 5176 makes the next Playwright run refuse to start.
- Review format (planner conditions): all captures first; per criterion the same neutral options in the same order, no recommendation; answers verbatim then expanded per terrain.
