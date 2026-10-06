---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE

## Proof Plan

- level: unit on planted sprites plus the real terrain-v1 tiles; proof kind: boundary tests and mutants; oracle source: the user thresholds and the measured baselines; expected effect: identical or recoloured pair fails I1, boundary at 3/6 px, I2 boundary at 6 L*, a one-vision collapse fails only there, I3 low-contrast and dark rims fail, deterministic; selected commands: `pytest tests/visual_assets tests/docs tests/static`.
