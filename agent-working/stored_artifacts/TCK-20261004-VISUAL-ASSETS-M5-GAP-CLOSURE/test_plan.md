---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE
artifact_type: test_plan
tags: [mcp, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE

Frontend (vitest): the pilot export holds exactly `terrain.forest`; copies of Live Map constants equal the originals (fills, names, kind colours, state colour, building colours/letters read from source); the predeclared layout and marker positions; image scene draws 49 forest cells 1:1 plus markers; flat control draws no image; every AM-U21 failure shows exactly the fill (missing, corrupt, wrong size, still loading, late, key absent, invalid manifest); non-Forest never gets the image; hover text equals the names. Python: the committed export equals a fresh export; the colour-vision arithmetic on synthetic input. Browser: 4 clients x (capture + 3 failure injections), local only.

## Proof Plan

- Level: unit, plus local real-browser captures.
- Proof kind: executable tests, a predeclared rule evaluated once, and recorded owner review.
- Oracle source: the ticket's acceptance criteria and `docs/assets/pilot_terrain_m5_criteria.md` (committed first).
- Expected effect: all pass; results recorded without claiming unrun clients.
- Selected commands: `npx vitest run` and `npx eslint src/visualAssets rehearsal-capture`; `pytest tests/visual_assets`; `npx playwright test -c playwright.pilot.config.ts` (local).
