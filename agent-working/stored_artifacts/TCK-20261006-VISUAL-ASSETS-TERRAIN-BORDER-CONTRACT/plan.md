---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT
artifact_type: plan
tags: [architecture, testing, live-map]
---

# Plan — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT

1. Blocking question (order, crisp set, depth cap, C6), answered 2026-10-06 as proposed; written to the criteria doc (AM5-B) before any art.
2. `terrainBorders.ts`: `TERRAIN_PRIORITY`, `CRISP_TERRAINS`, pure `borderOverlays`, `rotate`, `maskCapViolation`, `composeCell` (cap enforced whatever a mask holds); tests incl. doc-equality.
3. Register `border.edge|outer_corner|inner_corner` (optional, detail v1-v3); ADR D19, store_contract, fallback_safety. 4. Registry hash moved: user approved `pilot/rc-0004` (same entries), fixture re-export, guards re-pointed.
5. Probe in a guarded scratch copy that a transparent mask passes intake, `draft keep` and `verify`.
