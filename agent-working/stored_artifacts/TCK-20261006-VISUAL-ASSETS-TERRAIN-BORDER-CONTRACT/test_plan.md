---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT
artifact_type: test_plan
tags: [architecture, testing, live-map]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT

`frontend/src/visualAssets/__tests__/terrainBorders.test.ts` (20 tests): table equals the AM5-B doc table and crisp set; total order; no overlay between equal codes; higher onto lower only; crisp neither gives nor takes; side rotations 0/90/180/270; outer corner (and not when a side covers it); inner corner replaces two edges, falls back to two edges when its mask is missing; three and four matching sides; draw order lower first; off-map, unknown code, missing mask; determinism and declared variants; `rotate`; cap violation check; `composeCell` never draws beyond 4 px in any kind and rotation, shows neighbour pixels where the mask is opaque, leaves inputs untouched; depth equals the approved 4 and the doc.
Mutants caught: reversed comparison (8 failures), cap removed from `composeCell`, depth 5, wall added to the order. Registry test (3 border keys), pilot fixture rc-0004, catalog integrity (4 candidates). Full: `tests/visual_assets` 1534 passed (2 GB cap), `vitest src/visualAssets` 207 passed, `tsc -b` and `eslint src/visualAssets` clean.
