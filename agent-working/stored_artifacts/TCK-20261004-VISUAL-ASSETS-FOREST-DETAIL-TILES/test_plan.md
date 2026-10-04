---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES
artifact_type: test_plan
tags: [architecture, mcp, live-map]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES

- [x] Each tile adopted by the user (ids recorded); verify and audit clean.
- [x] rc-0002 lists plain, bush, tree; the runtime manifest lists every value and the declared `details`.
- [x] Committed fixture equals a fresh export; drill asserts the exact per-cell pick; mutant fails it.
- [x] Mixed preview with no seams attached.

## Proof Plan
- level: contract and catalog integrity (pure Python and vitest); real Aseprite only for build/review, run locally
- proof kind: exact catalog contents, fixture equality, per-cell pick equality, a mutant on the drill
- oracle source: the declared axis order and the user-approved spread; the committed records
- expected effect: three adopted slots released in rc-0002 and consumed by the client with the documented fallback
- selected commands: `pytest tests/visual_assets`, `python -m visual_assets.store verify`, `npx vitest run src/visualAssets`
