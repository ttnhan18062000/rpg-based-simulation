---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE
artifact_type: investigation
tags: [mcp, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE

- Re-checked against what landed: the real export was not committed by ticket 2, so the harness needs a committed copy with an equality test. The key is `terrain.forest`, not "terrain/forest".
- The rehearsal's terrain fallback was a typed glyph; the AM-U21 contract for the pilot role is the flat fill, so the pilot scene has its own `drawTerrainCell` (the old harness is unchanged).
- The 12 x 8 layout has 49 forest cells, not "half": the criteria page said "half" loosely; the formula and results are unaffected.
- Marker bleed: the hero's glow spills into adjacent cells, so "clean forest cells" for the pixel comparison are those with no marker on or next to them (30). My first capture spec picked cells by hand and was wrong; it failed, and was fixed in the spec, not in the harness.
- Client availability: Playwright Chromium build 1234 (expected by Playwright 1.62.1) is not installed; the cached 1223 headless shell (148.0.7778.96) ran, via `PILOT_CHROMIUM`. System Chrome 151.0.7922.71 ran via the `chrome` channel. The system Firefox is a snap build Playwright cannot drive.
- Whole-project `eslint .` reports 18 errors in existing app files (`App.tsx`, `GameCanvas.tsx`, ...) that this ticket does not touch; the files it adds or changes lint clean.
