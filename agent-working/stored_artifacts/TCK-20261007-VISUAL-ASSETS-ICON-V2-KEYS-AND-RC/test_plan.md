---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC
artifact_type: test_plan
tags: [architecture, hud, testing]
---

# Test plan — TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC

## Proof Plan

- level: registry facts and release-candidate equality; proof kind: exact key lists, sizes and entries plus mutants; oracle source: the user-approved families, the UI fallbacks and rc-0006; expected effect: 36 icon keys, rc-0007 equals rc-0006 slot for slot, no icon in any release; selected commands: `pytest tests/visual_assets tests/docs tests/static`, `vitest run src/visualAssets`, `store verify`.
