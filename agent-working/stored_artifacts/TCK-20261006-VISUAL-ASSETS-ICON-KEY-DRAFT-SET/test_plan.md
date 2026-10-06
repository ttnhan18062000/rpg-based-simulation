---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET
artifact_type: test_plan
tags: [architecture, hud, testing]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET

## Proof Plan

- level: set structure and read-back arithmetic (Python), page behaviour and copies pinned to their sources (vitest); proof kind: equality pins and planted-change guards; oracle source: the registry, palette, recorded rule and pilot_colour_vision.py; expected effect: 14 keys, sizes, palette-only pixels, fixture equals a fresh export modulo registry_hash; selected commands: `pytest tests/visual_assets tests/docs tests/static`, `npx vitest run`, `npm run build`.
