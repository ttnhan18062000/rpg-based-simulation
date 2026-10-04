---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE
artifact_type: plan
tags: [mcp, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE

1. Commit the predeclared criteria first (AM-U21 contract, W03 reviewer criteria, W05 pass rule, scene layout): `31eaf3f8b`.
2. Commit the real export as a frontend fixture (`__fixtures__/pilot/`) with a Python equality test against a fresh `export-runtime`.
3. Isolated pilot page (`rehearsal-pilot.html`, `PilotHarness`, `pilotScene`): the predeclared scene drawn twice (image and flat control), terrain fallback = the fill, copies of Live Map constants asserted equal.
4. W05 arithmetic in `tests/visual_assets/pilot_colour_vision.py`, run once against the real tile with the committed rule.
5. Blocking question for the client matrix before any capture; run the approved clients; blocking questions for W03 after captures; record results in `docs/assets/pilot_terrain_m5_results.md`.
