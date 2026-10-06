---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN
artifact_type: plan
tags: [mcp, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

1. Re-check against what landed; planner approved nine points (rc-0005, terrainset fixture, scene, review format, W05, fallback, rollback, unaffected list, handoff step). User approved build + rc-0005 + export (2026-10-06).
2. `build` 31 sources, `release` rc-0005, `export-runtime` into `__fixtures__/terrainset/`; re-point guards by equality; new fixture test.
3. Whole-map scene (mapScene, MapHarness, mapMain, rehearsal-map.html, capture + config), tests: layout, per-key and per-variant fallback, missing masks, rollback drill; borderRender fix; isolation count.
4. Commit the code, run every check on that clean commit (pytest, vitest, tsc, eslint, AM5-S, Playwright x4 clients). 5. User review of W03-SET (C1..C6, neutral options). 6. Record in the results docs; refresh handoff snapshots; close the batch.
