---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER
artifact_type: plan
tags: [architecture, testing, hud]
---

# Plan — TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER

One module `tests/visual_assets/review_sheets.py` writes `~/Work/asset-review/<set>/` (outside every repo): six large labelled PNG canvases at whole-number zoom plus a README with the results, findings and exact owner commands. Pure Python (zlib and struct for the PNG, a built-in 5x7 bitmap font for labels), no dependency; deterministic; tests; the process rule gets "every owner gate ships the folder path"; generate it for icons-owner-fixes-v1 (the four proposed revisions only) and give the path to the planner.
