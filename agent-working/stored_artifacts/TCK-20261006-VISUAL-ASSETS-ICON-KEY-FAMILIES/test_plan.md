---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES
artifact_type: test_plan
tags: [architecture, hud, testing]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES

## Proof Plan

- level: unit and fixture guards; proof kind: equality pins plus mutants; oracle source: the committed registry, rc-0005/rc-0006 candidates and the fresh export; expected effect: key set equals 40, rc-0006 entries equal rc-0005, pilot forest slots equal a fresh export; selected commands: `pytest tests/visual_assets tests/docs tests/static`, `vitest run src/visualAssets`, `python -m visual_assets.store verify`.
