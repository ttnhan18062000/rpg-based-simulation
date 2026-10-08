---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS

## Proof Plan

- level: unit on planted sprites; proof kind: boundary tests and mutants; oracle source: the user thresholds (I1 8 at 24x24) and the shape-only answer; expected effect: a recolour pair fails I1 in every group size, 8 px passes and 7 fails at 24x24, shape-only groups skip I2 and say so, the rarity group keeps I2; selected commands: `pytest tests/visual_assets`.
