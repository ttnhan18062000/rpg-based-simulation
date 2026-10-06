---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW
artifact_type: plan
tags: [architecture, testing, live-map]
---

# Plan — TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW

1. Enumerate subsets of the failing tiles under an exact mean-to-fill correction (result: none passes; all 22 passes). Planner decision A, 2026-10-05: re-tint all 22.
2. Offset rule in `tile_retint.py` (drawing unchanged, ramp pixels shifted by one RGB offset, refined against 8-bit and clipping). 3. Draw, hand off, intake, `draft keep --replace` for each of the 22.
4. `draft verify`, catalog `verify`, re-run the committed set check, record before/after. 5. Evidence: before/after sheet, repeat sheet, preview-page screenshot, per-tile report.
