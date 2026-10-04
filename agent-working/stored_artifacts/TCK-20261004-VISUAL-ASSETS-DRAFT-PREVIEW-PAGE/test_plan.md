---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE
artifact_type: test_plan
tags: [architecture, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE

- [x] Mutually unparseable in Python and TS, both directions, with and without the swapped type.
- [x] The sample map is deterministic and covers every TILE_NAMES code.
- [x] Isolation test; the pilot page and its tests are unchanged.
- [x] The displayed set hash equals the exported hash equals the hash adopt-set prints.
- [x] A screenshot with the fixture set is stored.

## Proof Plan
- level: unit and component (vitest with a recording 2D context) plus Python contract tests; one local browser capture
- proof kind: positive and negative parser cases, exact draw calls per cell, a three-way hash equality, fixture equality to a fresh export
- oracle source: the ticket, planner decisions D1-D7, `store_contract.md`
- expected effect: a reviewer can see a whole draft set on a map and name the exact set by its hash
- selected commands: `pytest tests/visual_assets`, `npx vitest run src/visualAssets`, `npx tsc -b`, `npx eslint src/visualAssets`
